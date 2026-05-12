from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol, runtime_checkable

from qts.core.ids import InstrumentId
from qts.data.historical.chains import HistoricalChain
from qts.data.historical.csv_format import (
    DEFAULT_HISTORICAL_CSV_SCHEMA,
    HistoricalCsvSchema,
    historical_timeframe_delta,
    parse_historical_ts_event,
    validate_historical_csv_columns,
)
from qts.data.historical.symbols import HistoricalFutureChainSymbolResolver
from qts.data.sessions import RegularSessionWindow
from qts.registry.future_roll import (
    FutureContractCandidate,
    FutureContractSelector,
)
from qts.registry.symbol_resolution import SourceSymbolResolver


@dataclass(frozen=True, slots=True)
class HistoricalSessionRollSelection:
    session_id: str
    selected_symbol: str
    selected_instrument_id: InstrumentId
    selected_volume: Decimal
    selected_bar_count: int


@dataclass(slots=True)
class HistoricalSessionRollStats:
    rows_seen: int = 0
    spreads_excluded: int = 0
    unsupported_contracts_excluded: int = 0
    outside_session_rows_excluded: int = 0

    def to_payload(self) -> dict[str, int]:
        return {
            "rows_seen": self.rows_seen,
            "spreads_excluded": self.spreads_excluded,
            "unsupported_contracts_excluded": self.unsupported_contracts_excluded,
            "outside_session_rows_excluded": self.outside_session_rows_excluded,
        }


@dataclass(frozen=True, slots=True)
class HistoricalSessionRollSummary:
    rows: tuple[HistoricalSessionRollSelection, ...]
    stats: HistoricalSessionRollStats


@dataclass(slots=True)
class _SessionContractRollStats:
    symbol: str
    instrument_id: InstrumentId
    volume: Decimal = Decimal("0")
    bar_count: int = 0
    latest_as_of: datetime | None = None
    latest_close: Decimal | None = None


def summarize_historical_session_rolls(
    csv_path: Path,
    symbol_resolver: SourceSymbolResolver | HistoricalChain,
    *,
    session_window: RegularSessionWindow,
    contract_selector: FutureContractSelector,
    timeframe: str = "1m",
    schema: HistoricalCsvSchema | None = None,
) -> HistoricalSessionRollSummary:
    resolver = _as_symbol_resolver(symbol_resolver)
    active_schema = schema or DEFAULT_HISTORICAL_CSV_SCHEMA
    root = _resolver_root(resolver)
    timeframe_delta = historical_timeframe_delta(timeframe)
    sessions: dict[str, dict[InstrumentId, _SessionContractRollStats]] = {}
    build_stats = HistoricalSessionRollStats()
    current_timestamp: str | None = None
    current_timestamp_value: datetime | None = None
    current_session_id: str | None = None

    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        columns = tuple(next(reader))
        validate_historical_csv_columns(columns, schema=schema)
        column_index = active_schema.column_indices(columns)
        timestamp_index = column_index["timestamp"]
        open_index = column_index["open"]
        high_index = column_index["high"]
        low_index = column_index["low"]
        close_index = column_index["close"]
        volume_index = column_index["volume"]
        symbol_index = column_index["symbol"]

        for row in reader:
            build_stats.rows_seen += 1
            symbol = row[symbol_index]
            if not resolver.is_supported_symbol(symbol):
                if _is_spread_symbol(symbol):
                    build_stats.spreads_excluded += 1
                else:
                    build_stats.unsupported_contracts_excluded += 1
                continue

            timestamp_text = row[timestamp_index]
            if timestamp_text != current_timestamp:
                current_timestamp = timestamp_text
                current_timestamp_value = parse_historical_ts_event(timestamp_text)
                current_session_id = session_window.session_id_for_timestamp(
                    current_timestamp_value
                )
            if current_session_id is None:
                build_stats.outside_session_rows_excluded += 1
                continue
            if current_timestamp_value is None:
                raise RuntimeError("timestamp was not parsed before session roll aggregation")

            try:
                _, _, _, close, volume = _parse_ohlcv_values(
                    open_value=row[open_index],
                    high_value=row[high_index],
                    low_value=row[low_index],
                    close_value=row[close_index],
                    volume_value=row[volume_index],
                )
            except ValueError:
                continue

            instrument_id = resolver.instrument_id_for_symbol(symbol)
            per_contract = sessions.setdefault(current_session_id, {})
            contract_stats = per_contract.setdefault(
                instrument_id,
                _SessionContractRollStats(symbol=symbol, instrument_id=instrument_id),
            )
            contract_stats.volume += volume
            contract_stats.bar_count += 1
            contract_stats.latest_as_of = current_timestamp_value + timeframe_delta
            contract_stats.latest_close = close

    rows: list[HistoricalSessionRollSelection] = []
    for session_id in sorted(sessions):
        candidates = tuple(
            FutureContractCandidate(
                root_symbol=root,
                symbol=contract_stats.symbol,
                instrument_id=contract_stats.instrument_id,
                as_of=_required_as_of(contract_stats),
                close=_required_close(contract_stats),
                volume=contract_stats.volume,
            )
            for contract_stats in sessions[session_id].values()
        )
        selected = contract_selector.select(candidates)
        selected_stats = sessions[session_id][selected.instrument_id]
        rows.append(
            HistoricalSessionRollSelection(
                session_id=session_id,
                selected_symbol=selected.symbol,
                selected_instrument_id=selected.instrument_id,
                selected_volume=selected_stats.volume,
                selected_bar_count=selected_stats.bar_count,
            )
        )

    return HistoricalSessionRollSummary(rows=tuple(rows), stats=build_stats)


def _as_symbol_resolver(
    value: SourceSymbolResolver | HistoricalChain,
) -> SourceSymbolResolver:
    if isinstance(value, HistoricalChain):
        return HistoricalFutureChainSymbolResolver(value)
    return value


def _resolver_root(symbol_resolver: SourceSymbolResolver) -> str:
    if not isinstance(symbol_resolver, _RootSymbolResolver):
        raise ValueError("rolling historical streams require a root-aware symbol resolver")
    root = symbol_resolver.root
    if not isinstance(root, str) or not root.strip():
        raise ValueError("rolling historical streams require a root-aware symbol resolver")
    return root


@runtime_checkable
class _RootSymbolResolver(Protocol):
    """Protocol for symbol resolvers that expose a root identifier."""

    @property
    def root(self) -> str: ...


def _parse_ohlcv_values(
    *,
    open_value: str,
    high_value: str,
    low_value: str,
    close_value: str,
    volume_value: str,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    open_ = Decimal(open_value)
    high = Decimal(high_value)
    low = Decimal(low_value)
    close = Decimal(close_value)
    volume = Decimal(volume_value)
    if high < max(open_, close):
        raise ValueError("high must be greater than or equal to open and close")
    if low > min(open_, close):
        raise ValueError("low must be less than or equal to open and close")
    if low > high:
        raise ValueError("low must be less than or equal to high")
    if volume < Decimal("0"):
        raise ValueError("volume must be non-negative")
    return open_, high, low, close, volume


def _required_as_of(stats: _SessionContractRollStats) -> datetime:
    if stats.latest_as_of is None:
        raise ValueError(f"missing latest timestamp for {stats.symbol}")
    return stats.latest_as_of


def _required_close(stats: _SessionContractRollStats) -> Decimal:
    if stats.latest_close is None:
        raise ValueError(f"missing latest close for {stats.symbol}")
    return stats.latest_close


def _is_spread_symbol(symbol: str) -> bool:
    return "-" in symbol
