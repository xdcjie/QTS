from __future__ import annotations

from datetime import timedelta

import pytest
from qts.core.ids import InstrumentId
from qts.data.historical.csv_row_mapper import HistoricalCsvRowMapper
from qts.registry.symbol_resolution import StaticSymbolResolver


def _row(timestamp: str) -> dict[str, str]:
    return {
        "ts_event": timestamp,
        "symbol": "GCQ0",
        "open": "100.0",
        "high": "101.0",
        "low": "99.0",
        "close": "100.5",
        "volume": "42",
    }


def test_row_mapper_maps_row_with_timeframe_and_timezone_session_id() -> None:
    resolver = StaticSymbolResolver({"GCQ0": InstrumentId("FUTURE.CME.GC.GCQ0")})
    mapper = HistoricalCsvRowMapper(timeframe="5m")

    bar = mapper.to_bar(
        _row("2026-01-02T23:30:00-05:00"),
        symbol_resolver=resolver,
    )

    assert bar.start_time.tzinfo is not None
    assert bar.end_time == bar.start_time + timedelta(minutes=5)
    assert bar.session_id == "2026-01-03"


def test_row_mapper_requires_required_fields() -> None:
    resolver = StaticSymbolResolver({"GCQ0": InstrumentId("FUTURE.CME.GC.GCQ0")})
    incomplete_row = {"ts_event": "2026-01-02T14:30:00Z"}

    with pytest.raises(KeyError, match="symbol"):
        HistoricalCsvRowMapper().to_bar(incomplete_row, symbol_resolver=resolver)
