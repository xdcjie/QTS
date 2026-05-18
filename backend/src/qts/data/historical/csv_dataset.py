"""Streaming CSV access for local historical futures datasets."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from qts.core.ids import InstrumentId
from qts.data.historical.chains import HistoricalChain
from qts.data.historical.csv_format import (
    DEFAULT_HISTORICAL_CSV_SCHEMA,
    EXPECTED_HISTORICAL_COLUMNS,
    HistoricalCsvSchema,
    parse_historical_ts_event,
    validate_historical_csv_columns,
)
from qts.data.historical.csv_row_mapper import HistoricalCsvRowMapper
from qts.data.historical.symbols import HistoricalFutureChainSymbolResolver
from qts.data.historical.validation import (
    HistoricalCsvStats,
    HistoricalDatasetValidator,
    HistoricalValidationSample,
)
from qts.data.sessions import RegularSessionWindow
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
        schema: HistoricalCsvSchema | None = None,
    ) -> None:
        self._csv_path = csv_path
        self._symbol_resolver = symbol_resolver
        self._timeframe = timeframe
        self._start = start
        self._end = end
        self._contract_selector = contract_selector
        self._continuous_instrument_id = continuous_instrument_id
        self._session_window = session_window
        self._schema = schema or DEFAULT_HISTORICAL_CSV_SCHEMA
        self._configured_schema = schema
        self._row_mapper = HistoricalCsvRowMapper(timeframe=timeframe, schema=self._schema)
        self.stats = HistoricalCsvStats()
        self.roll_selections: list[FutureRollSelection] = []

    def __iter__(self) -> Iterator[Bar]:
        with self._csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            validate_historical_csv_columns(
                tuple(reader.fieldnames or ()),
                schema=self._configured_schema,
            )
            if self._contract_selector is None:
                yield from self._iter_all_supported_rows(reader)
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
            session_override = self._session_id_for(timestamp)
            if self._session_window is not None and session_override is None:
                continue
            try:
                bar = self._row_mapper.to_bar(
                    row,
                    symbol_resolver=self._symbol_resolver,
                )
            except ValueError:
                self.stats.invalid_rows += 1
                continue
            if session_override is not None and bar.session_id != session_override:
                bar = replace(bar, session_id=session_override)
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
            session_override = self._session_id_for(timestamp)
            if self._session_window is not None and session_override is None:
                # Break-time row: skip the whole timestamp group.
                continue
            candidates: list[FutureContractCandidate] = []
            bars_by_instrument: dict[InstrumentId, Bar] = {}
            for row in rows:
                symbol = self._field(row, "symbol")
                if not self._symbol_resolver.is_supported_symbol(symbol):
                    self._count_excluded_symbol(symbol)
                    continue
                try:
                    bar = self._row_mapper.to_bar(
                        row,
                        symbol_resolver=self._symbol_resolver,
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
            if session_override is not None and output_bar.session_id != session_override:
                output_bar = replace(output_bar, session_id=session_override)
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

    def _session_id_for(self, timestamp: datetime) -> str | None:
        """Return the exchange-local session_id for ``timestamp``, if a window is set."""
        if self._session_window is None:
            return None
        return self._session_window.session_id_for_timestamp(timestamp)

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
        return row[self._schema.resolve_column(semantic_name)]

    def _timestamp(self, row: dict[str, str]) -> datetime:
        return parse_historical_ts_event(self._field(row, "timestamp"))


def describe_csv_dataset(
    path: Path,
    *,
    root: str,
    timeframe: str = "1m",
    count_rows: bool = False,
    schema: HistoricalCsvSchema | None = None,
    timezone_policy: str = "source UTC timestamps; exchange session semantics",
    normalization_policy: str = "raw OHLCV rows; spreads excluded by default",
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
        timezone_policy=timezone_policy,
        normalization_policy=normalization_policy,
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
    schema: HistoricalCsvSchema | None = None,
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


def validate_historical_sample(
    csv_path: Path,
    symbol_resolver: SourceSymbolResolver | HistoricalChain,
    *,
    sample_rows: int | None,
    timeframe: str = "1m",
    schema: HistoricalCsvSchema | None = None,
) -> HistoricalValidationSample:
    """Validate a bounded sample or full CSV when `sample_rows` is None."""
    return HistoricalDatasetValidator().validate_sample(
        csv_path=csv_path,
        symbol_resolver=_as_symbol_resolver(symbol_resolver),
        sample_rows=sample_rows,
        timeframe=timeframe,
        schema=schema,
    )


def _resolver_root(symbol_resolver: SourceSymbolResolver) -> str:
    if not isinstance(symbol_resolver, RootSymbolResolver):
        raise ValueError("rolling historical streams require a root-aware symbol resolver")
    root = symbol_resolver.root
    if not root:
        raise ValueError("rolling historical streams require a root-aware symbol resolver")
    return root


@runtime_checkable
class RootSymbolResolver(Protocol):
    """Protocol for symbol resolvers that provide a root identifier."""

    @property
    def root(self) -> str:
        """Return the root identifier."""
        ...


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
    "HistoricalValidationSample",
    "describe_csv_dataset",
    "iter_historical_bars",
    "validate_historical_sample",
]
