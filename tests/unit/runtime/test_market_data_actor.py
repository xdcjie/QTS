from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest


def test_market_data_actor_forwards_normalized_tick_to_subscribers() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Tick
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.market_data_actor import MarketDataActor, MarketDataEvent
    from qts.runtime.mailbox import Mailbox

    subscriber = Mailbox()
    actor = MarketDataActor(subscribers=(ActorRef(mailbox=subscriber),))
    tick = Tick(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        price=Decimal("101.25"),
        size=Decimal("10"),
    )

    actor.handle(MarketDataEvent(payload=tick))

    assert subscriber.get() == tick


def test_market_data_actor_rejects_order_execution_requests() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.runtime.actors.execution_actor import OrderExecutionRequest
    from qts.runtime.actors.market_data_actor import MarketDataActor

    actor = MarketDataActor()

    with pytest.raises(TypeError, match="unsupported market data message"):
        actor.handle(
            OrderExecutionRequest(
                intent=OrderIntent(
                    order_id=OrderId("ord-001"),
                    instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                    side=OrderSide.BUY,
                    quantity=Decimal("10"),
                ),
                broker_order_id="sim-001",
                market_price=Decimal("101.25"),
            )
        )


def test_market_data_actor_owns_bar_aggregation_state_and_emits_completed_bars() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Bar
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.market_data_actor import MarketDataActor, MarketDataEvent
    from qts.runtime.mailbox import Mailbox

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    subscriber = Mailbox()
    actor = MarketDataActor(
        subscribers=(ActorRef(mailbox=subscriber),),
        aggregate_timeframe="5m",
        exchange_timezone=UTC,
    )

    for offset in range(5):
        actor.handle(
            MarketDataEvent(
                payload=Bar(
                    instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                    start_time=start + timedelta(minutes=offset),
                    end_time=start + timedelta(minutes=offset + 1),
                    timeframe="1m",
                    session_id="2026-01-02",
                    open=Decimal(str(100 + offset)),
                    high=Decimal(str(101 + offset)),
                    low=Decimal(str(99 + offset)),
                    close=Decimal(str(100 + offset)),
                    volume=Decimal("10"),
                    is_complete=True,
                )
            )
        )

    completed = subscriber.get()
    assert isinstance(completed, Bar)
    assert completed.start_time == start
    assert completed.end_time == start + timedelta(minutes=5)
    assert completed.timeframe == "5m"
    assert completed.open == Decimal("100")
    assert completed.close == Decimal("104")
    assert completed.volume == Decimal("50")
    assert completed.is_complete
    assert subscriber.empty()
