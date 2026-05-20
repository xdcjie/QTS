from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.research import HistoryRequest, ResearchBookConfig, ResearchHistoryFrame


def test_research_book_config_rejects_missing_catalog_reference() -> None:
    with pytest.raises(ValueError, match="catalog_name is required"):
        ResearchBookConfig(
            data_config_path=Path("configs/data/historical.local.yaml"),
            catalog_name="",
            roots=("GC",),
            timeframe="1m",
        )


def test_history_request_uses_half_open_interval() -> None:
    request = HistoryRequest(
        root="GC",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
        timeframe="1m",
    )

    assert request.includes(datetime(2026, 1, 1, tzinfo=UTC))
    assert not request.includes(datetime(2026, 1, 2, tzinfo=UTC))


def test_research_history_frame_rows_expose_deterministic_bar_values() -> None:
    frame = ResearchHistoryFrame(
        bars=(
            Bar(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                start_time=datetime(2026, 1, 1, 14, 30, tzinfo=UTC),
                end_time=datetime(2026, 1, 1, 14, 31, tzinfo=UTC),
                timeframe="1m",
                session_id="2026-01-01",
                open=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
                close=Decimal("100.5"),
                volume=Decimal("250"),
                vwap=Decimal("100.25"),
                open_interest=Decimal("10"),
                trade_count=5,
                is_complete=True,
            ),
        )
    )

    rows = frame.rows()

    assert rows == (
        {
            "close": Decimal("100.5"),
            "end_time": datetime(2026, 1, 1, 14, 31, tzinfo=UTC),
            "high": Decimal("101"),
            "instrument_id": "EQUITY.US.NASDAQ.AAPL",
            "is_complete": True,
            "is_partial": False,
            "is_synthetic": False,
            "low": Decimal("99"),
            "open": Decimal("100"),
            "open_interest": Decimal("10"),
            "session_id": "2026-01-01",
            "start_time": datetime(2026, 1, 1, 14, 30, tzinfo=UTC),
            "timeframe": "1m",
            "trade_count": 5,
            "volume": Decimal("250"),
            "vwap": Decimal("100.25"),
        },
    )


def test_research_history_frame_to_pandas_preserves_row_order() -> None:
    frame = ResearchHistoryFrame(
        bars=(
            Bar(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                start_time=datetime(2026, 1, 1, 14, 30, tzinfo=UTC),
                end_time=datetime(2026, 1, 1, 14, 31, tzinfo=UTC),
                timeframe="1m",
                session_id="2026-01-01",
                open=Decimal("100"),
                high=Decimal("100"),
                low=Decimal("100"),
                close=Decimal("100"),
                volume=Decimal("1"),
            ),
            Bar(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
                start_time=datetime(2026, 1, 1, 14, 31, tzinfo=UTC),
                end_time=datetime(2026, 1, 1, 14, 32, tzinfo=UTC),
                timeframe="1m",
                session_id="2026-01-01",
                open=Decimal("200"),
                high=Decimal("200"),
                low=Decimal("200"),
                close=Decimal("200"),
                volume=Decimal("2"),
            ),
        )
    )

    data_frame = frame.to_pandas()

    assert list(data_frame["instrument_id"]) == [
        "EQUITY.US.NASDAQ.AAPL",
        "EQUITY.US.NASDAQ.MSFT",
    ]
    assert list(data_frame["close"]) == [Decimal("100"), Decimal("200")]
