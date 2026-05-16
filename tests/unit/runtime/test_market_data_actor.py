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
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
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
                account_id=AccountId("acct-a"),
                strategy_id=StrategyId("strategy-a"),
                client_order_id="client-001",
                correlation_id=CorrelationId("corr-001"),
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


def test_market_data_actor_deduplicates_physical_subscription_and_fans_out() -> None:
    from qts.core.ids import InstrumentId
    from qts.data.capabilities import MarketDataFeedCapabilities
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.market_data_actor import MarketDataActor, SubscribeMarketData
    from qts.runtime.mailbox import Mailbox
    from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

    source = FakeStreamingMarketDataAdapter(
        source_id="ibkr-live-md",
        capabilities=MarketDataFeedCapabilities(
            source_id="ibkr-live-md",
            supported_timeframes=frozenset({"5s"}),
        ),
    )
    left = Mailbox()
    right = Mailbox()
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    actor = MarketDataActor(feed=source, exchange_timezone=UTC)

    actor.handle(
        SubscribeMarketData(
            subscriber_id="strategy-a",
            subscriber_ref=ActorRef(mailbox=left),
            instrument_id=instrument_id,
            timeframe="1m",
        )
    )
    actor.handle(
        SubscribeMarketData(
            subscriber_id="strategy-b",
            subscriber_ref=ActorRef(mailbox=right),
            instrument_id=instrument_id,
            timeframe="1m",
        )
    )

    assert source.subscription_count == 1
    assert actor.logical_subscription_count == 1


def test_market_data_actor_aggregates_one_source_stream_once_and_fans_out_to_strategies() -> None:
    from qts.core.ids import InstrumentId
    from qts.data.capabilities import MarketDataFeedCapabilities
    from qts.domain.market_data import Bar
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.market_data_actor import (
        MarketDataActor,
        MarketDataEvent,
        SubscribeMarketData,
    )
    from qts.runtime.mailbox import Mailbox
    from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

    source = FakeStreamingMarketDataAdapter(
        source_id="ibkr-live-md",
        capabilities=MarketDataFeedCapabilities(
            source_id="ibkr-live-md",
            supported_timeframes=frozenset({"5s"}),
        ),
    )
    left = Mailbox()
    right = Mailbox()
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    actor = MarketDataActor(feed=source, exchange_timezone=UTC)

    for subscriber_id, mailbox in (("strategy-a", left), ("strategy-b", right)):
        actor.handle(
            SubscribeMarketData(
                subscriber_id=subscriber_id,
                subscriber_ref=ActorRef(mailbox=mailbox),
                instrument_id=instrument_id,
                timeframe="1m",
            )
        )

    for offset in range(12):
        value = Decimal(str(100 + offset))
        actor.handle(
            MarketDataEvent(
                payload=Bar(
                    instrument_id=instrument_id,
                    start_time=start + timedelta(seconds=5 * offset),
                    end_time=start + timedelta(seconds=5 * (offset + 1)),
                    timeframe="5s",
                    session_id="2026-01-02",
                    open=value,
                    high=value,
                    low=value,
                    close=value,
                    volume=Decimal("1"),
                    is_complete=True,
                )
            )
        )

    left_bar = left.get()
    right_bar = right.get()
    assert isinstance(left_bar, Bar)
    assert isinstance(right_bar, Bar)
    assert left_bar == right_bar
    assert left_bar.start_time == start
    assert left_bar.end_time == start + timedelta(minutes=1)
    assert left_bar.timeframe == "1m"
    assert left_bar.close == Decimal("111")
    assert left_bar.volume == Decimal("12")
    assert left.empty()
    assert right.empty()
