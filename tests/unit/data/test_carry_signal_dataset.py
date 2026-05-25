from __future__ import annotations

import csv
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.carry_signal import (
    calendar_spread_carry_signal_rows,
    write_carry_signal_csv,
)
from qts.data.historical.chains import HistoricalChain, HistoricalContract
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row(symbol: str, timestamp: str, close: str, *, volume: str = "1") -> dict[str, str]:
    return {
        "ts_event": timestamp,
        "rtype": "33",
        "publisher_id": "1",
        "instrument_id": "123",
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": volume,
        "symbol": symbol,
    }


def _chain() -> HistoricalChain:
    contracts = (
        HistoricalContract(
            symbol="F1",
            root="GC",
            exchange="CME",
            currency="USD",
            tick_size=Decimal("0.1"),
            multiplier=Decimal("100"),
            expiry=datetime(2026, 1, 30, 22, tzinfo=UTC),
            first_notice_day=date(2026, 1, 29),
            trading_calendar="CMES",
        ),
        HistoricalContract(
            symbol="F2",
            root="GC",
            exchange="CME",
            currency="USD",
            tick_size=Decimal("0.1"),
            multiplier=Decimal("100"),
            expiry=datetime(2026, 2, 27, 22, tzinfo=UTC),
            first_notice_day=date(2026, 2, 26),
            trading_calendar="CMES",
        ),
    )
    return HistoricalChain(
        root="GC",
        exchange="CME",
        currency="USD",
        timezone="US/Eastern",
        tick_size=Decimal("0.1"),
        multiplier=Decimal("100"),
        trading_calendar="CMES",
        contracts=contracts,
        trading_hours="20260101:1800-20260102:1700",
    )


class _Calendar:
    def session_offset(self, session_date: date, offset: int) -> date:
        return session_date + timedelta(days=offset)


def test_carry_signal_dataset_uses_calendar_spread_as_research_signal(tmp_path: Path) -> None:
    path = tmp_path / "gc.csv"
    timestamp = "2026-01-02T21:59:00.000000000Z"
    _write_rows(
        path,
        [
            _row("F1", timestamp, "100", volume="10"),
            _row("F2", timestamp, "101", volume="8"),
            _row("F1-F2", timestamp, "-1", volume="3"),
        ],
    )
    rows = calendar_spread_carry_signal_rows(
        root="GC",
        csv_path=path,
        chain=_chain(),
        output_symbol="GC_CARRY",
        output_instrument_id=InstrumentId("RESEARCH.CARRY.GC"),
        session_offset=_Calendar().session_offset,
    )

    assert len(rows) == 1
    assert rows[0]["symbol"] == "GC_CARRY"
    assert rows[0]["timestamp"] == datetime(2026, 1, 2, 21, 59, tzinfo=UTC)
    assert rows[0]["session_id"] == "2026-01-02"
    assert rows[0]["carry"] == Decimal("-0.01")
    assert rows[0]["volume"] == Decimal("3")


def test_carry_signal_dataset_skips_when_calendar_spread_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "gc.csv"
    timestamp = "2026-01-02T21:59:00.000000000Z"
    _write_rows(
        path,
        [
            _row("F1", timestamp, "100"),
            _row("F2", timestamp, "101"),
        ],
    )
    rows = calendar_spread_carry_signal_rows(
        root="GC",
        csv_path=path,
        chain=_chain(),
        output_symbol="GC_CARRY",
        output_instrument_id=InstrumentId("RESEARCH.CARRY.GC"),
        session_offset=_Calendar().session_offset,
    )

    assert rows == ()


def test_carry_signal_csv_writer_emits_databento_compatible_rows(tmp_path: Path) -> None:
    path = tmp_path / "gc.csv"
    timestamp = "2026-01-02T21:59:00.000000000Z"
    _write_rows(
        path,
        [
            _row("F1", timestamp, "100", volume="10"),
            _row("F2", timestamp, "101", volume="8"),
            _row("F1-F2", timestamp, "-1", volume="3"),
        ],
    )
    rows = calendar_spread_carry_signal_rows(
        root="GC",
        csv_path=path,
        chain=_chain(),
        output_symbol="GC_CARRY",
        output_instrument_id=InstrumentId("RESEARCH.CARRY.GC"),
        session_offset=_Calendar().session_offset,
    )
    output_path = tmp_path / "carry.csv"

    rows_written = write_carry_signal_csv(output_path, rows)

    with output_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        csv_rows = list(reader)
    assert rows_written == 1
    assert csv_rows == [
        {
            "ts_event": "2026-01-02T21:59:00.000000000Z",
            "rtype": "33",
            "publisher_id": "0",
            "instrument_id": "RESEARCH.CARRY.GC",
            "open": "-0.01",
            "high": "-0.01",
            "low": "-0.01",
            "close": "-0.01",
            "volume": "3",
            "symbol": "GC_CARRY",
        }
    ]
