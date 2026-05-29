"""Validation services for historical dataset rows and samples."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.csv_format import (
    DEFAULT_HISTORICAL_CSV_SCHEMA,
    HistoricalCsvSchema,
    historical_timeframe_delta,
    validate_historical_csv_columns,
)
from qts.data.historical.csv_row_mapper import HistoricalCsvRowMapper
from qts.data.validation_report import (
    DataValidationIssue,
    DataValidationIssueCode,
    DataValidationReport,
    DataValidationSeverity,
    validate_bars,
)
from qts.domain.market_data import Bar
from qts.registry.symbol_resolution import SourceSymbolResolver

_FUTURES_OUTRIGHT_SYMBOL_RE = re.compile(r"^[A-Z]{1,4}[FGHJKMNQUVXZ][0-9]{1,2}$")


@dataclass(slots=True)
class HistoricalCsvStats:
    """Streaming counters for historical CSV validation."""

    rows_seen: int = 0
    bars_emitted: int = 0
    symbols_excluded: int = 0
    spreads_excluded: int = 0
    contracts_excluded: int = 0
    invalid_rows: int = 0

    def as_dict(self) -> dict[str, int]:
        """Perform as_dict."""
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
    """Validation report plus counters for one sampled historical file."""

    report: DataValidationReport
    stats: HistoricalCsvStats
    bars: tuple[Bar, ...]


@dataclass(frozen=True, slots=True)
class HistoricalDatasetValidator:
    """Validate historical sample files and return domain-friendly diagnostics."""

    row_mapper: HistoricalCsvRowMapper = field(default_factory=HistoricalCsvRowMapper)

    def validate_sample(
        self,
        csv_path: Path,
        symbol_resolver: SourceSymbolResolver,
        *,
        sample_rows: int | None,
        timeframe: str = "1m",
        schema: HistoricalCsvSchema | None = None,
        allow_futures_outright_symbols: bool = True,
    ) -> HistoricalValidationSample:
        """Perform validate_sample."""
        if sample_rows is not None and sample_rows <= 0:
            raise ValueError("sample_rows must be positive")

        active_schema = schema or DEFAULT_HISTORICAL_CSV_SCHEMA
        resolver = symbol_resolver
        mapper = self.row_mapper
        if mapper.timeframe != timeframe or mapper.schema != active_schema:
            mapper = HistoricalCsvRowMapper(timeframe=timeframe, schema=active_schema)
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
                symbol = row[active_schema.symbol]
                if not allow_futures_outright_symbols and is_futures_outright_symbol(symbol):
                    stats.invalid_rows += 1
                    issues.append(
                        DataValidationIssue(
                            code=DataValidationIssueCode.UNDECLARED_FUTURES_OUTRIGHT_SYMBOL,
                            message=(
                                "futures outright symbols require a future asset_class "
                                f"and chain metadata: {symbol}"
                            ),
                            severity=DataValidationSeverity.ERROR,
                        )
                    )
                    continue
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
                    bar = mapper.to_bar(row, symbol_resolver=resolver)
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


def find_futures_outright_symbols(
    csv_path: Path,
    *,
    schema: HistoricalCsvSchema | None = None,
    limit: int = 5,
) -> tuple[str, ...]:
    """Return distinct futures outright-looking symbols found in a CSV."""

    if limit <= 0:
        raise ValueError("limit must be positive")
    active_schema = schema or DEFAULT_HISTORICAL_CSV_SCHEMA
    symbols: list[str] = []
    seen: set[str] = set()
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        validate_historical_csv_columns(tuple(reader.fieldnames or ()), schema=schema)
        for row in reader:
            symbol = row[active_schema.symbol]
            normalized = symbol.strip().upper()
            if normalized in seen or not is_futures_outright_symbol(normalized):
                continue
            seen.add(normalized)
            symbols.append(normalized)
            if len(symbols) >= limit:
                break
    return tuple(symbols)


def is_futures_outright_symbol(symbol: str) -> bool:
    """Return whether a source symbol looks like a listed futures outright contract."""

    return bool(_FUTURES_OUTRIGHT_SYMBOL_RE.fullmatch(symbol.strip().upper()))


def _group_bars(bars: list[Bar]) -> dict[InstrumentId, list[Bar]]:
    """Perform _group_bars."""
    grouped: dict[InstrumentId, list[Bar]] = defaultdict(list)
    for bar in bars:
        grouped[bar.instrument_id].append(bar)
    return grouped


def _is_spread_symbol(symbol: str) -> bool:
    """Perform _is_spread_symbol."""
    return "-" in symbol


__all__ = [
    "find_futures_outright_symbols",
    "HistoricalCsvStats",
    "HistoricalValidationSample",
    "HistoricalDatasetValidator",
    "is_futures_outright_symbol",
]
