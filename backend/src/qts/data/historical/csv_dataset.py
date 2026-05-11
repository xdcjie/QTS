"""Streaming CSV access for local historical futures datasets."""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.chains import HistoricalChain
from qts.data.historical.symbols import HistoricalFutureChainSymbolResolver
from qts.data.validation_report import (
    DataValidationIssue,
    DataValidationIssueCode,
    DataValidationReport,
    DataValidationSeverity,
    validate_bars,
)
from qts.domain.market_data import Bar
from qts.registry.symbol_resolution import SourceSymbolResolver

EXPECTED_HISTORICAL_COLUMNS = (
    "ts_event",
    "rtype",
    "publisher_id",
    "instrument_id",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "symbol",
)


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
    invalid_rows: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "rows_seen": self.rows_seen,
            "bars_emitted": self.bars_emitted,
            "symbols_excluded": self.symbols_excluded,
            "spreads_excluded": self.spreads_excluded,
            "invalid_rows": self.invalid_rows,
        }


@dataclass(frozen=True, slots=True)
class HistoricalValidationSample:
    """Validation report plus counters for a sampled historical CSV."""

    report: DataValidationReport
    stats: HistoricalCsvStats
    bars: tuple[Bar, ...]


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
    ) -> None:
        self._csv_path = csv_path
        self._symbol_resolver = symbol_resolver
        self._timeframe = timeframe
        self._start = start
        self._end = end
        self.stats = HistoricalCsvStats()

    def __iter__(self) -> Iterator[Bar]:
        with self._csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            _validate_columns(tuple(reader.fieldnames or ()))
            for row in reader:
                self.stats.rows_seen += 1
                symbol = row["symbol"]
                if not self._symbol_resolver.is_supported_symbol(symbol):
                    self.stats.symbols_excluded += 1
                    if _is_spread_symbol(symbol):
                        self.stats.spreads_excluded += 1
                    continue
                timestamp = _parse_ts_event(row["ts_event"])
                if self._start is not None and timestamp < self._start:
                    continue
                if self._end is not None and timestamp >= self._end:
                    break
                try:
                    bar = _row_to_bar(
                        row,
                        symbol_resolver=self._symbol_resolver,
                        timeframe=self._timeframe,
                    )
                except ValueError:
                    self.stats.invalid_rows += 1
                    continue
                self.stats.bars_emitted += 1
                yield bar


def describe_csv_dataset(
    path: Path,
    *,
    root: str,
    timeframe: str = "1m",
    count_rows: bool = False,
) -> CsvDatasetDescription:
    """Read historical CSV identity metadata without materializing row data."""

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        columns = tuple(next(reader))
        _validate_columns(columns)
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
) -> HistoricalBarStream:
    """Return a lazy stream of outright historical bars."""

    return HistoricalBarStream(
        csv_path=csv_path,
        symbol_resolver=_as_symbol_resolver(symbol_resolver),
        timeframe=timeframe,
        start=start,
        end=end,
    )


def validate_historical_sample(
    csv_path: Path,
    symbol_resolver: SourceSymbolResolver | HistoricalChain,
    *,
    sample_rows: int | None,
    timeframe: str = "1m",
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
        _validate_columns(tuple(reader.fieldnames or ()))
        for row in reader:
            if sample_rows is not None and stats.rows_seen >= sample_rows:
                break
            stats.rows_seen += 1
            symbol = row["symbol"]
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
                bar = _row_to_bar(row, symbol_resolver=resolver, timeframe=timeframe)
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
                expected_interval=_timeframe_delta(timeframe),
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
) -> Bar:
    start_time = _parse_ts_event(row["ts_event"])
    end_time = start_time + _timeframe_delta(timeframe)
    symbol = row["symbol"]
    return Bar(
        instrument_id=symbol_resolver.instrument_id_for_symbol(symbol),
        start_time=start_time,
        end_time=end_time,
        timeframe=timeframe,
        session_id=start_time.astimezone(UTC).date().isoformat(),
        open=Decimal(row["open"]),
        high=Decimal(row["high"]),
        low=Decimal(row["low"]),
        close=Decimal(row["close"]),
        volume=Decimal(row["volume"]),
        is_complete=True,
    )


def _validate_columns(columns: tuple[str, ...]) -> None:
    if columns != EXPECTED_HISTORICAL_COLUMNS:
        raise ValueError(
            "historical CSV columns must be "
            f"{','.join(EXPECTED_HISTORICAL_COLUMNS)}; got {','.join(columns)}"
        )


def _parse_ts_event(value: str) -> datetime:
    text = value.removesuffix("Z")
    suffix = "+00:00" if value.endswith("Z") else ""
    if "." in text:
        prefix, rest = text.split(".", maxsplit=1)
        fraction = rest[:6].ljust(6, "0")
        text = f"{prefix}.{fraction}"
    parsed = datetime.fromisoformat(f"{text}{suffix}")
    if parsed.tzinfo is None:
        raise ValueError("ts_event must be timezone-aware")
    return parsed.astimezone(UTC)


def _timeframe_delta(timeframe: str) -> timedelta:
    if timeframe == "1m":
        return timedelta(minutes=1)
    if timeframe.endswith("m"):
        return timedelta(minutes=int(timeframe[:-1]))
    if timeframe.endswith("s"):
        return timedelta(seconds=int(timeframe[:-1]))
    if timeframe.endswith("h"):
        return timedelta(hours=int(timeframe[:-1]))
    raise ValueError(f"unsupported historical timeframe: {timeframe}")


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
    "HistoricalValidationSample",
    "describe_csv_dataset",
    "iter_historical_bars",
    "validate_historical_sample",
]
