from __future__ import annotations

import csv
from datetime import UTC, datetime, time, timedelta
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
from qts.data.historical.csv_format import HistoricalCsvSchema
from qts.data.sessions import RegularSessionWindow
from qts.data.validation_report import DataValidationIssueCode, DataValidationSeverity
from qts.registry.future_roll import HighestVolumeFutureContractSelector
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
    volume: str = "2",
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
        "volume": volume,
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


def test_iter_historical_bars_uses_configured_csv_schema_mapping(tmp_path: Path) -> None:
    path = tmp_path / "equity_alt_schema.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("event_time", "ticker", "o", "h", "l", "c", "qty"),
        )
        writer.writeheader()
        writer.writerow(
            {
                "event_time": "2026-01-02T14:30:00.000000000Z",
                "ticker": "AAPL",
                "o": "100",
                "h": "101",
                "l": "99",
                "c": "100.5",
                "qty": "42",
            }
        )
    schema = HistoricalCsvSchema(
        timestamp="event_time",
        symbol="ticker",
        open="o",
        high="h",
        low="l",
        close="c",
        volume="qty",
    )
    resolver = StaticSymbolResolver({"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")})

    stream = iter_historical_bars(path, resolver, timeframe="1m", schema=schema)
    bars = tuple(stream)

    assert len(bars) == 1
    assert bars[0].instrument_id == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert bars[0].open == Decimal("100")
    assert bars[0].close == Decimal("100.5")
    assert bars[0].volume == Decimal("42")


def test_explicit_default_schema_accepts_semantic_columns_without_databento_order(
    tmp_path: Path,
) -> None:
    path = tmp_path / "equity_reordered.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("symbol", "ts_event", "open", "high", "low", "close", "volume"),
        )
        writer.writeheader()
        writer.writerow(
            {
                "symbol": "AAPL",
                "ts_event": "2026-01-02T14:30:00.000000000Z",
                "open": "100",
                "high": "101",
                "low": "99",
                "close": "100.5",
                "volume": "42",
            }
        )
    resolver = StaticSymbolResolver({"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")})

    stream = iter_historical_bars(
        path,
        resolver,
        timeframe="1m",
        schema=HistoricalCsvSchema(),
    )
    bars = tuple(stream)

    assert len(bars) == 1
    assert bars[0].close == Decimal("100.5")


def test_iter_historical_bars_can_emit_one_rolling_bar_per_timestamp(
    tmp_path: Path,
) -> None:
    path = tmp_path / "gc.csv"
    _write_rows(
        path,
        [
            _row("GCN0", 30, open_="1220.2", high="1220.2", low="1220.2", close="1220.2"),
            _row("GCQ0", 30, open_="1221.6", high="1221.6", low="1221.6", close="1221.6"),
            _row("GCN0-GCQ0", 30, open_="-1.4", high="-1.4", low="-1.4", close="-1.4"),
        ],
    )
    chain = load_historical_chain(Path("historical/chains/GC.json"))
    continuous_id = InstrumentId("CONTINUOUS_FUTURE.CME.GC")

    stream = iter_historical_bars(
        path,
        chain,
        timeframe="1m",
        contract_selector=HighestVolumeFutureContractSelector(),
        continuous_instrument_id=continuous_id,
    )
    bars = tuple(stream)

    assert [bar.instrument_id for bar in bars] == [continuous_id]
    assert bars[0].close == Decimal("1221.6")
    assert stream.roll_selections[0].concrete_instrument_id == InstrumentId("FUTURE.CME.GC.GCQ0")
    assert stream.stats.bars_emitted == 1
    assert stream.stats.contracts_excluded == 1
    assert stream.stats.spreads_excluded == 1


def test_iter_historical_bars_can_roll_once_per_exchange_session_by_total_volume(
    tmp_path: Path,
) -> None:
    path = tmp_path / "gc.csv"
    _write_rows(
        path,
        [
            _row("GCN0", 30, open_="100", high="100", low="100", close="100", volume="100"),
            _row("GCQ0", 30, open_="110", high="110", low="110", close="110", volume="1"),
            _row("GCN0", 31, open_="101", high="101", low="101", close="101", volume="1"),
            _row("GCQ0", 31, open_="111", high="111", low="111", close="111", volume="100"),
        ],
    )
    chain = load_historical_chain(Path("historical/chains/GC.json"))
    continuous_id = InstrumentId("CONTINUOUS_FUTURE.CME.GC")
    session_window = RegularSessionWindow(
        exchange_timezone="US/Eastern",
        open_time=time(18, 0),
        close_time=time(17, 0),
    )

    stream = iter_historical_bars(
        path,
        chain,
        timeframe="1m",
        contract_selector=HighestVolumeFutureContractSelector(),
        continuous_instrument_id=continuous_id,
        session_window=session_window,
    )
    bars = tuple(stream)

    assert [bar.close for bar in bars] == [Decimal("110"), Decimal("111")]
    assert [selection.source_symbol for selection in stream.roll_selections] == ["GCQ0", "GCQ0"]
    assert stream.stats.bars_emitted == 2
    assert stream.stats.contracts_excluded == 2


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
