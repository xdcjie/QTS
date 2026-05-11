from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from qts.core.ids import InstrumentId
from qts.data.historical.chains import load_historical_chain
from qts.data.historical.csv_dataset import (
    EXPECTED_HISTORICAL_COLUMNS,
    describe_csv_dataset,
    iter_historical_bars,
    validate_historical_sample,
)
from qts.data.validation_report import DataValidationIssueCode, DataValidationSeverity
from qts.registry.symbol_resolution import StaticSymbolResolver


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row(
    symbol: str,
    minute: int,
    *,
    open_: str = "2000.0",
    high: str = "2000.0",
    low: str = "2000.0",
    close: str = "2000.0",
) -> dict[str, str]:
    return {
        "ts_event": f"2026-01-02T14:{minute:02d}:00.000000000Z",
        "rtype": "33",
        "publisher_id": "1",
        "instrument_id": "123",
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": "2",
        "symbol": symbol,
    }


def test_describe_csv_dataset_reads_header_without_counting_rows() -> None:
    description = describe_csv_dataset(Path("historical/data/gc.csv"), root="GC")

    assert description.root == "GC"
    assert description.path == Path("historical/data/gc.csv")
    assert description.columns == EXPECTED_HISTORICAL_COLUMNS
    assert description.row_count is None
    assert description.timeframe == "1m"
    assert description.timezone_policy == "source UTC timestamps; exchange session semantics"
    assert description.normalization_policy == "raw OHLCV rows; spreads excluded by default"
    assert description.source_hash_policy == "not computed unless explicitly requested"


def test_describe_csv_dataset_counts_rows_only_when_requested(tmp_path: Path) -> None:
    path = tmp_path / "gc.csv"
    _write_rows(path, [_row("GCM0", 30), _row("GCQ0", 31)])

    description = describe_csv_dataset(path, root="GC", count_rows=True)

    assert description.row_count == 2


def test_describe_csv_dataset_rejects_invalid_column_order(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("symbol,ts_event\nGCQ0,2026-01-02T14:30:00Z\n", encoding="utf-8")

    with pytest.raises(ValueError, match="columns"):
        describe_csv_dataset(path, root="GC")


def test_iter_historical_bars_streams_outrights_and_excludes_spreads(tmp_path: Path) -> None:
    path = tmp_path / "gc.csv"
    _write_rows(path, [_row("GCQ0", 30), _row("GCN0-GCQ0", 31), _row("GCM0", 32)])
    chain = load_historical_chain(Path("historical/chains/GC.json"))

    stream = iter_historical_bars(path, chain, timeframe="1m")
    bars = tuple(stream)

    assert [bar.instrument_id.value for bar in bars] == [
        "FUTURE.CME.GC.GCQ0",
        "FUTURE.CME.GC.GCM0",
    ]
    assert bars[0].start_time == datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    assert bars[0].end_time == bars[0].start_time + timedelta(minutes=1)
    assert bars[0].open == Decimal("2000.0")
    assert bars[0].is_complete is True
    assert stream.stats.rows_seen == 3
    assert stream.stats.bars_emitted == 2
    assert stream.stats.spreads_excluded == 1


def test_iter_historical_bars_accepts_static_symbol_resolver_without_chain(
    tmp_path: Path,
) -> None:
    path = tmp_path / "equity.csv"
    _write_rows(path, [_row("AAPL", 30), _row("MSFT", 31)])
    resolver = StaticSymbolResolver({"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")})

    stream = iter_historical_bars(path, resolver, timeframe="1m")
    bars = tuple(stream)

    assert [bar.instrument_id for bar in bars] == [InstrumentId("EQUITY.US.NASDAQ.AAPL")]
    assert stream.stats.rows_seen == 2
    assert stream.stats.bars_emitted == 1
    assert stream.stats.symbols_excluded == 1
    assert stream.stats.spreads_excluded == 0


def test_validate_historical_sample_reports_invalid_ohlc_and_spread_exclusion(
    tmp_path: Path,
) -> None:
    path = tmp_path / "gc.csv"
    _write_rows(
        path,
        [
            _row("GCQ0", 30, open_="2000", high="1999", low="1998", close="2000"),
            _row("GCN0-GCQ0", 31),
            _row("GCM0", 32),
        ],
    )
    chain = load_historical_chain(Path("historical/chains/GC.json"))

    result = validate_historical_sample(path, chain, sample_rows=3)

    assert result.stats.rows_seen == 3
    assert result.stats.spreads_excluded == 1
    assert result.stats.bars_emitted == 1
    assert DataValidationIssueCode.INVALID_OHLC in {issue.code for issue in result.report.issues}
    assert DataValidationIssueCode.EXCLUDED_SPREAD in {issue.code for issue in result.report.issues}
    assert any(
        issue.code is DataValidationIssueCode.INVALID_OHLC
        and issue.severity is DataValidationSeverity.ERROR
        for issue in result.report.issues
    )
