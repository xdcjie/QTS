from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
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


def test_market_data_flow_publishes_actor_ready_bars() -> None:
    from qts.runtime.market_data_flow import MarketDataFlow

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    flow = MarketDataFlow(target_timeframe=None, exchange_timezone_by_instrument={})

    assert flow.publish_bar(bar) == (bar,)


def test_market_data_flow_requires_timezone_for_target_aggregation() -> None:
    from qts.runtime.market_data_flow import MarketDataFlow

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    flow = MarketDataFlow(target_timeframe="5m", exchange_timezone_by_instrument={})

    with pytest.raises(RuntimeError, match="exchange timezone is required"):
        flow.publish_bar(bar)
