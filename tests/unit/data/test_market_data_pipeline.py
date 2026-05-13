from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


def _bar(start: datetime, *, timeframe: str = "1m") -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe=timeframe,
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("10"),
        is_complete=True,
    )


def test_market_data_pipeline_passes_through_matching_bars() -> None:
    from qts.data.market_data_pipeline import MarketDataPipeline

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    pipeline = MarketDataPipeline()

    assert pipeline.process_bar(bar, target_timeframe=None) == (bar,)
    assert pipeline.process_bar(bar, target_timeframe="1m") == (bar,)


def test_market_data_pipeline_requires_timezone_for_aggregation() -> None:
    import pytest
    from qts.data.market_data_pipeline import MarketDataPipeline

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    pipeline = MarketDataPipeline()

    with pytest.raises(RuntimeError, match="exchange timezone is required"):
        pipeline.process_bar(bar, target_timeframe="5m")
