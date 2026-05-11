"""Streaming CSV access for local historical futures datasets."""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.chains import HistoricalChain
from qts.data.historical.csv_format import (
    DEFAULT_HISTORICAL_CSV_SCHEMA,
    EXPECTED_HISTORICAL_COLUMNS,
    HistoricalCsvSchema,
    historical_timeframe_delta,
    parse_historical_ts_event,
    validate_historical_csv_columns,
)
from qts.data.historical.symbols import HistoricalFutureChainSymbolResolver
from qts.data.sessions import RegularSessionWindow
from qts.data.validation_report import (
    DataValidationIssue,
    DataValidationIssueCode,
    DataValidationReport,
    DataValidationSeverity,
    validate_bars,
)
from qts.domain.market_data import Bar
from qts.registry.future_roll import (
    FutureContractCandidate,
    FutureContractSelector,
    FutureRollSelection,
)
from qts.registry.symbol_resolution import SourceSymbolResolver


@dataclass(frozen=True, slots=True)
class CsvDatasetDescription:
    """Cheap metadata description for a historical CSV dataset."""

    root: str
    path: Path
    columns: tuple[str, ...]
    timeframe: str
    timezone_policy: str
    normalization_policy: str
    source_hash_policy: str
    row_count: int | None = None


@dataclass(slots=True)
class HistoricalCsvStats:
    """Streaming reader counters."""

    rows_seen: int = 0
    bars_emitted: int = 0
    symbols_excluded: int = 0
    spreads_excluded: int = 0
    contracts_excluded: int = 0
    invalid_rows: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "rows_seen": self.rows_seen,
            "bars_emitted": self.bars_emitted,
            "symbols_excluded": self.symbols_excluded,
            "spreads_excluded": self.spreads_excluded,
            "contracts_excluded": self.contracts_excluded,
            "invalid_rows": self.invalid_rows,
        }


@dataclass(frozen=True, slots=True)
class HistoricalValidationSample:
    """Validation report plus counters for a sampled historical CSV."""

    report: DataValidationReport
    stats: HistoricalCsvStats
    bars: tuple[Bar, ...]


@dataclass(frozen=True, slots=True)
class HistoricalSessionRollSelection:
    """Session-level selected contract summary for a historical rolling dataset."""

    session_id: str
    selected_symbol: str
    selected_instrument_id: InstrumentId
    selected_volume: Decimal
    selected_bar_count: int


@dataclass(slots=True)
class HistoricalSessionRollStats:
    """Counters for session-level historical roll summarization."""

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
    """Session-level selected contract summary plus source counters."""

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


class HistoricalBarStream:
    """Lazy iterable over historical bars with side-channel reader stats."""

    def __init__(
        self,
        *,
        csv_path: Path,
        symbol_resolver: SourceSymbolResolver,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        contract_selector: FutureContractSelector | None = None,
        continuous_instrument_id: InstrumentId | None = None,
        session_window: RegularSessionWindow | None = None,
        schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA,
    ) -> None:
        self._csv_path = csv_path
        self._symbol_resolver = symbol_resolver
        self._timeframe = timeframe
        self._start = start
        self._end = end
        self._contract_selector = contract_selector
        self._continuous_instrument_id = continuous_instrument_id
        self._session_window = session_window
        self._schema = schema
        self.stats = HistoricalCsvStats()
        self.roll_selections: list[FutureRollSelection] = []

    def __iter__(self) -> Iterator[Bar]:
        with self._csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            validate_historical_csv_columns(tuple(reader.fieldnames or ()), schema=self._schema)
            if self._contract_selector is None:
                yield from self._iter_all_supported_rows(reader)
            elif self._session_window is not None:
                yield from self._iter_session_selected_contract_rows(reader)
            else:
                yield from self._iter_selected_contract_rows(reader)

    def _iter_all_supported_rows(self, reader: csv.DictReader[str]) -> Iterator[Bar]:
        for row in reader:
            self.stats.rows_seen += 1
            symbol = self._field(row, "symbol")
            if not self._symbol_resolver.is_supported_symbol(symbol):
                self._count_excluded_symbol(symbol)
                continue
            timestamp = self._timestamp(row)
            if self._start is not None and timestamp < self._start:
                continue
            if self._end is not None and timestamp >= self._end:
                break
            try:
                bar = _row_to_bar(
                    row,
                    symbol_resolver=self._symbol_resolver,
                    timeframe=self._timeframe,
                    schema=self._schema,
                )
            except ValueError:
                self.stats.invalid_rows += 1
                continue
            self.stats.bars_emitted += 1
            yield bar

    def _iter_selected_contract_rows(self, reader: csv.DictReader[str]) -> Iterator[Bar]:
        contract_selector = self._contract_selector
        if contract_selector is None:
            raise RuntimeError("contract selector is not configured")
        for timestamp, rows in self._timestamp_groups(reader):
            if self._start is not None and timestamp < self._start:
                continue
            if self._end is not None and timestamp >= self._end:
                break
            candidates: list[FutureContractCandidate] = []
            bars_by_instrument: dict[InstrumentId, Bar] = {}
            for row in rows:
                symbol = self._field(row, "symbol")
                if not self._symbol_resolver.is_supported_symbol(symbol):
                    self._count_excluded_symbol(symbol)
                    continue
                try:
                    bar = _row_to_bar(
                        row,
                        symbol_resolver=self._symbol_resolver,
                        timeframe=self._timeframe,
                        schema=self._schema,
                    )
                except ValueError:
                    self.stats.invalid_rows += 1
                    continue
                bars_by_instrument[bar.instrument_id] = bar
                candidates.append(
                    FutureContractCandidate(
                        root_symbol=self._resolver_root(),
                        symbol=symbol,
                        instrument_id=bar.instrument_id,
                        as_of=bar.end_time,
                        close=bar.close,
                        volume=bar.volume,
                    )
                )
            if not candidates:
                continue
            selected = contract_selector.select(tuple(candidates))
            selected_bar = bars_by_instrument[selected.instrument_id]
            output_instrument_id = self._continuous_instrument_id or selected.instrument_id
            output_bar = (
                selected_bar
                if output_instrument_id == selected.instrument_id
                else replace(selected_bar, instrument_id=output_instrument_id)
            )
            self.roll_selections.append(
                FutureRollSelection(
                    continuous_instrument_id=output_instrument_id,
                    root_symbol=selected.root_symbol,
                    as_of=output_bar.end_time,
                    concrete_instrument_id=selected.instrument_id,
                    source_symbol=selected.symbol,
                    prices_by_instrument={
                        candidate.instrument_id: candidate.close for candidate in candidates
                    },
                )
            )
            self.stats.contracts_excluded += len(candidates) - 1
            self.stats.bars_emitted += 1
            yield output_bar

    def _iter_session_selected_contract_rows(
        self,
        reader: csv.DictReader[str],
    ) -> Iterator[Bar]:
        contract_selector = self._contract_selector
        session_window = self._session_window
        if contract_selector is None:
            raise RuntimeError("contract selector is not configured")
        if session_window is None:
            raise RuntimeError("session window is not configured")

        current_session_id: str | None = None
        current_groups: list[tuple[datetime, list[dict[str, str]]]] = []
        for timestamp, rows in self._timestamp_groups(reader):
            if self._start is not None and timestamp < self._start:
                continue
            if self._end is not None and timestamp >= self._end:
                break
            session_id = session_window.session_id_for_timestamp(timestamp)
            if session_id is None:
                if current_session_id is not None:
                    yield from self._emit_selected_session_rows(
                        current_session_id,
                        current_groups,
                        contract_selector=contract_selector,
                    )
                    current_session_id = None
                    current_groups = []
                continue
            if current_session_id is not None and session_id != current_session_id:
                yield from self._emit_selected_session_rows(
                    current_session_id,
                    current_groups,
                    contract_selector=contract_selector,
                )
                current_groups = []
            current_session_id = session_id
            current_groups.append((timestamp, rows))

        if current_session_id is not None:
            yield from self._emit_selected_session_rows(
                current_session_id,
                current_groups,
                contract_selector=contract_selector,
            )

    def _emit_selected_session_rows(
        self,
        session_id: str,
        groups: list[tuple[datetime, list[dict[str, str]]]],
        *,
        contract_selector: FutureContractSelector,
    ) -> Iterator[Bar]:
        rows_by_timestamp: list[dict[InstrumentId, dict[str, str]]] = []
        closes_by_timestamp: list[dict[InstrumentId, Decimal]] = []
        total_volume_by_instrument: dict[InstrumentId, Decimal] = defaultdict(lambda: Decimal("0"))
        latest_as_of_by_instrument: dict[InstrumentId, datetime] = {}
        latest_close_by_instrument: dict[InstrumentId, Decimal] = {}
        symbol_by_instrument: dict[InstrumentId, str] = {}
        timeframe_delta = historical_timeframe_delta(self._timeframe)

        for timestamp, rows in groups:
            rows_by_instrument: dict[InstrumentId, dict[str, str]] = {}
            closes_by_instrument: dict[InstrumentId, Decimal] = {}
            for row in rows:
                symbol = self._field(row, "symbol")
                if not self._symbol_resolver.is_supported_symbol(symbol):
                    self._count_excluded_symbol(symbol)
                    continue
                try:
                    _, _, _, close, volume = _row_ohlcv(row, schema=self._schema)
                except ValueError:
                    self.stats.invalid_rows += 1
                    continue
                instrument_id = self._symbol_resolver.instrument_id_for_symbol(symbol)
                rows_by_instrument[instrument_id] = row
                closes_by_instrument[instrument_id] = close
                total_volume_by_instrument[instrument_id] += volume
                latest_as_of_by_instrument[instrument_id] = timestamp + timeframe_delta
                latest_close_by_instrument[instrument_id] = close
                symbol_by_instrument[instrument_id] = symbol
            if rows_by_instrument:
                rows_by_timestamp.append(rows_by_instrument)
                closes_by_timestamp.append(closes_by_instrument)

        if not total_volume_by_instrument:
            return

        candidates = tuple(
            FutureContractCandidate(
                root_symbol=self._resolver_root(),
                symbol=symbol_by_instrument[instrument_id],
                instrument_id=instrument_id,
                as_of=latest_as_of_by_instrument[instrument_id],
                close=latest_close_by_instrument[instrument_id],
                volume=volume,
            )
            for instrument_id, volume in total_volume_by_instrument.items()
        )
        selected = contract_selector.select(candidates)

        for rows_by_instrument, closes_by_instrument in zip(
            rows_by_timestamp,
            closes_by_timestamp,
            strict=True,
        ):
            selected_row = rows_by_instrument.get(selected.instrument_id)
            if selected_row is None:
                continue
            selected_bar = _row_to_bar(
                selected_row,
                symbol_resolver=self._symbol_resolver,
                timeframe=self._timeframe,
                schema=self._schema,
            )
            output_instrument_id = self._continuous_instrument_id or selected.instrument_id
            output_bar = replace(
                selected_bar,
                instrument_id=output_instrument_id,
                session_id=session_id,
            )
            self.roll_selections.append(
                FutureRollSelection(
                    continuous_instrument_id=output_instrument_id,
                    root_symbol=selected.root_symbol,
                    as_of=output_bar.end_time,
                    concrete_instrument_id=selected.instrument_id,
                    source_symbol=selected.symbol,
                    prices_by_instrument=closes_by_instrument,
                )
            )
            self.stats.contracts_excluded += len(rows_by_instrument) - 1
            self.stats.bars_emitted += 1
            yield output_bar

    def _timestamp_groups(
        self,
        reader: csv.DictReader[str],
    ) -> Iterator[tuple[datetime, list[dict[str, str]]]]:
        current_timestamp: str | None = None
        current_rows: list[dict[str, str]] = []
        for row in reader:
            self.stats.rows_seen += 1
            timestamp_text = self._field(row, "timestamp")
            if current_timestamp is not None and timestamp_text != current_timestamp:
                yield parse_historical_ts_event(current_timestamp), current_rows
                current_rows = []
            current_timestamp = timestamp_text
            current_rows.append(row)
        if current_timestamp is not None:
            yield parse_historical_ts_event(current_timestamp), current_rows

    def _count_excluded_symbol(self, symbol: str) -> None:
        self.stats.symbols_excluded += 1
        if _is_spread_symbol(symbol):
            self.stats.spreads_excluded += 1

    def _resolver_root(self) -> str:
        return _resolver_root(self._symbol_resolver)

    def _field(self, row: dict[str, str], semantic_name: str) -> str:
        return row[getattr(self._schema, semantic_name)]

    def _timestamp(self, row: dict[str, str]) -> datetime:
        return parse_historical_ts_event(self._field(row, "timestamp"))


def describe_csv_dataset(
    path: Path,
    *,
    root: str,
    timeframe: str = "1m",
    count_rows: bool = False,
    schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA,
) -> CsvDatasetDescription:
    """Read historical CSV identity metadata without materializing row data."""

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        columns = tuple(next(reader))
        validate_historical_csv_columns(columns, schema=schema)
        row_count = sum(1 for _ in reader) if count_rows else None
    return CsvDatasetDescription(
        root=root,
        path=path,
        columns=columns,
        timeframe=timeframe,
        timezone_policy="source UTC timestamps; exchange session semantics",
        normalization_policy="raw OHLCV rows; spreads excluded by default",
        source_hash_policy="not computed unless explicitly requested",
        row_count=row_count,
    )


def iter_historical_bars(
    csv_path: Path,
    symbol_resolver: SourceSymbolResolver | HistoricalChain,
    *,
    timeframe: str = "1m",
    start: datetime | None = None,
    end: datetime | None = None,
    contract_selector: FutureContractSelector | None = None,
    continuous_instrument_id: InstrumentId | None = None,
    session_window: RegularSessionWindow | None = None,
    schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA,
) -> HistoricalBarStream:
    """Return a lazy stream of outright historical bars."""

    return HistoricalBarStream(
        csv_path=csv_path,
        symbol_resolver=_as_symbol_resolver(symbol_resolver),
        timeframe=timeframe,
        start=start,
        end=end,
        contract_selector=contract_selector,
        continuous_instrument_id=continuous_instrument_id,
        session_window=session_window,
        schema=schema,
    )


def summarize_historical_session_rolls(
    csv_path: Path,
    symbol_resolver: SourceSymbolResolver | HistoricalChain,
    *,
    session_window: RegularSessionWindow,
    contract_selector: FutureContractSelector,
    timeframe: str = "1m",
    schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA,
) -> HistoricalSessionRollSummary:
    """Summarize the session-level contract selection a historical roll reader should use."""

    resolver = _as_symbol_resolver(symbol_resolver)
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
        column_index = schema.column_indices(columns)
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


def validate_historical_sample(
    csv_path: Path,
    symbol_resolver: SourceSymbolResolver | HistoricalChain,
    *,
    sample_rows: int | None,
    timeframe: str = "1m",
    schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA,
) -> HistoricalValidationSample:
    """Validate a bounded sample or full CSV when `sample_rows` is None."""

    if sample_rows is not None and sample_rows <= 0:
        raise ValueError("sample_rows must be positive")
    resolver = _as_symbol_resolver(symbol_resolver)
    stats = HistoricalCsvStats()
    issues: list[DataValidationIssue] = []
    bars: list[Bar] = []
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        validate_historical_csv_columns(tuple(reader.fieldnames or ()), schema=schema)
        for row in reader:
            if sample_rows is not None and stats.rows_seen >= sample_rows:
                break
            stats.rows_seen += 1
            symbol = row[schema.symbol]
            if not resolver.is_supported_symbol(symbol):
                stats.symbols_excluded += 1
                is_spread = _is_spread_symbol(symbol)
                if is_spread:
                    stats.spreads_excluded += 1
                issues.append(
                    DataValidationIssue(
                        code=(
                            DataValidationIssueCode.EXCLUDED_SPREAD
                            if is_spread
                            else DataValidationIssueCode.EXCLUDED_SYMBOL
                        ),
                        message=f"excluded unsupported symbol {symbol}",
                        severity=DataValidationSeverity.INFO,
                    )
                )
                continue
            try:
                bar = _row_to_bar(
                    row,
                    symbol_resolver=resolver,
                    timeframe=timeframe,
                    schema=schema,
                )
            except ValueError as exc:
                stats.invalid_rows += 1
                issues.append(
                    DataValidationIssue(
                        code=DataValidationIssueCode.INVALID_OHLC,
                        message=f"invalid row for {symbol}: {exc}",
                        severity=DataValidationSeverity.ERROR,
                    )
                )
                continue
            stats.bars_emitted += 1
            bars.append(bar)

    for instrument_bars in _group_bars(bars).values():
        issues.extend(
            validate_bars(
                tuple(instrument_bars),
                expected_interval=historical_timeframe_delta(timeframe),
            ).issues
        )
    return HistoricalValidationSample(
        report=DataValidationReport(issues=tuple(issues)),
        stats=stats,
        bars=tuple(bars),
    )


def _row_to_bar(
    row: dict[str, str],
    *,
    symbol_resolver: SourceSymbolResolver,
    timeframe: str,
    schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA,
) -> Bar:
    start_time = parse_historical_ts_event(row[schema.timestamp])
    end_time = start_time + historical_timeframe_delta(timeframe)
    symbol = row[schema.symbol]
    open_, high, low, close, volume = _row_ohlcv(row, schema=schema)
    return Bar(
        instrument_id=symbol_resolver.instrument_id_for_symbol(symbol),
        start_time=start_time,
        end_time=end_time,
        timeframe=timeframe,
        session_id=start_time.astimezone(UTC).date().isoformat(),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        is_complete=True,
    )


def _row_ohlcv(
    row: dict[str, str],
    *,
    schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    return _parse_ohlcv_values(
        open_value=row[schema.open],
        high_value=row[schema.high],
        low_value=row[schema.low],
        close_value=row[schema.close],
        volume_value=row[schema.volume],
    )


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


def _resolver_root(symbol_resolver: SourceSymbolResolver) -> str:
    root = getattr(symbol_resolver, "root", "")
    if not isinstance(root, str) or not root.strip():
        raise ValueError("rolling historical streams require a root-aware symbol resolver")
    return root


def _required_as_of(stats: _SessionContractRollStats) -> datetime:
    if stats.latest_as_of is None:
        raise ValueError(f"missing latest timestamp for {stats.symbol}")
    return stats.latest_as_of


def _required_close(stats: _SessionContractRollStats) -> Decimal:
    if stats.latest_close is None:
        raise ValueError(f"missing latest close for {stats.symbol}")
    return stats.latest_close


def _group_bars(bars: list[Bar]) -> dict[InstrumentId, list[Bar]]:
    grouped: dict[InstrumentId, list[Bar]] = defaultdict(list)
    for bar in bars:
        grouped[bar.instrument_id].append(bar)
    return grouped


def _as_symbol_resolver(
    value: SourceSymbolResolver | HistoricalChain,
) -> SourceSymbolResolver:
    if isinstance(value, HistoricalChain):
        return HistoricalFutureChainSymbolResolver(value)
    return value


def _is_spread_symbol(symbol: str) -> bool:
    return "-" in symbol


__all__ = [
    "EXPECTED_HISTORICAL_COLUMNS",
    "CsvDatasetDescription",
    "HistoricalBarStream",
    "HistoricalCsvStats",
    "HistoricalSessionRollSelection",
    "HistoricalSessionRollStats",
    "HistoricalSessionRollSummary",
    "HistoricalValidationSample",
    "describe_csv_dataset",
    "iter_historical_bars",
    "summarize_historical_session_rolls",
    "validate_historical_sample",
]
