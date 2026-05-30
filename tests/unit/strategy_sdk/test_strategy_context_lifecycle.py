"""Gate: Strategy SDK order-lifecycle APIs are wired through the runtime (DR-025).

These tests lock the runtime wiring for ``ctx.cancel_order`` (drained and routed
to OrderManagerActor), ``ctx.schedule_timer`` (``on_timer`` fires deterministically),
``ctx.subscribe_ticks`` (explicit rejection on a bar-only runtime), and
``intent_id`` propagation (a strategy fill carries the originating intent_id).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import (
    AccountId,
    BrokerId,
    CorrelationId,
    InstrumentId,
    OrderId,
    StrategyId,
)
from qts.domain.market_data import Bar
from qts.domain.orders import OrderFill, OrderIntent, OrderSide, OrderState
from qts.domain.risk import RiskDecision
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.execution_actor import OrderCancelRequest
from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
from qts.runtime.actors.strategy_actor import (
    StrategyActor,
    StrategyBarEvent,
    StrategyBarResult,
    StrategyFillEvent,
)
from qts.runtime.mailbox import Mailbox
from qts.runtime.order_lifecycle import CancelIntentRouter
from qts.runtime.order_route_metadata import OrderRouteMetadata
from qts.runtime.strategy_execution_pipeline import (
    StrategyExecutionPipeline,
    TickFeedUnavailableError,
)
from qts.strategy_sdk import (
    DataView,
    PortfolioView,
    Strategy,
    StrategyContext,
    TimerEvent,
)
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.events import Fill, TimerScheduler, TimerSubscription

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _asset() -> AssetRef:
    return AssetRef(_INSTRUMENT, "AAPL")


def _empty_portfolio() -> PortfolioView:
    return PortfolioView(cash=Decimal("100000"), equity=Decimal("100000"))


def _bar(minute: int) -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return Bar(
        instrument_id=_INSTRUMENT,
        start_time=start + timedelta(minutes=minute),
        end_time=start + timedelta(minutes=minute + 1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("100"),
        is_complete=True,
    )


def _route_metadata(account_id: AccountId, strategy_id: StrategyId) -> OrderRouteMetadata:
    return OrderRouteMetadata(
        broker_id=BrokerId("broker-route"),
        account_id=account_id,
        strategy_id=strategy_id,
        client_order_id="client-001",
        correlation_id=CorrelationId("corr-001"),
    )


# --- cancel_order is drained and routed to OrderManagerActor -----------------


def test_cancel_order_routes_drained_cancel_to_order_manager_actor() -> None:
    account_id = AccountId("acct-a")
    strategy_id = StrategyId("strategy-a")
    order_id = OrderId("ord-001")
    execution_mailbox = Mailbox()
    actor = OrderManagerActor(
        account_id=account_id,
        execution_ref=ActorRef(mailbox=execution_mailbox),
        account_ref=ActorRef(mailbox=Mailbox()),
    )
    order_manager_ref = ActorRef(actor=actor, mailbox=Mailbox())
    actor.handle(
        SubmitOrder(
            intent=OrderIntent(
                order_id=order_id,
                account_id=account_id,
                instrument_id=_INSTRUMENT,
                side=OrderSide.BUY,
                quantity=Decimal("10"),
            ),
            risk_decision=RiskDecision.approve(),
            broker_order_id="broker-001",
            market_price=Decimal("101"),
            account_id=account_id,
            strategy_id=strategy_id,
            route_metadata=_route_metadata(account_id, strategy_id),
        )
    )
    assert execution_mailbox.get() is not None  # drain the submit request

    # A strategy emits the cancel via the SDK surface (no broker internals).
    ctx = StrategyContext()
    ctx.cancel_order(order_id.value)

    router = CancelIntentRouter(order_manager_ref=order_manager_ref)
    routed = router.route(ctx.cancel_intents)

    assert routed == (order_id,)
    cancel_request = execution_mailbox.get()
    assert isinstance(cancel_request, OrderCancelRequest)
    assert cancel_request.order_id == order_id
    assert cancel_request.account_id == account_id
    assert actor.get_order(order_id).state is OrderState.CANCEL_REQUESTED


def test_cancel_router_skips_unknown_order_id() -> None:
    account_id = AccountId("acct-a")
    actor = OrderManagerActor(
        account_id=account_id,
        execution_ref=ActorRef(mailbox=Mailbox()),
        account_ref=ActorRef(mailbox=Mailbox()),
    )
    order_manager_ref = ActorRef(actor=actor, mailbox=Mailbox())

    ctx = StrategyContext()
    ctx.cancel_order("never-submitted")

    routed = CancelIntentRouter(order_manager_ref=order_manager_ref).route(ctx.cancel_intents)

    assert routed == ()


def test_strategy_actor_surfaces_cancel_intents_in_bar_result() -> None:
    class CancelStrategy(Strategy):
        def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
            ctx.cancel_order("ord-001", reason="exit")

    result_mailbox = Mailbox()
    ctx = StrategyContext()
    actor = StrategyActor(
        strategy=CancelStrategy(),
        context=ctx,
        result_ref=ActorRef(mailbox=result_mailbox),
    )
    bar = _bar(0)
    actor.handle(
        StrategyBarEvent(
            bar=bar,
            data=DataView(bars={_INSTRUMENT: [bar]}, as_of=bar.end_time),
            portfolio=_empty_portfolio(),
        )
    )
    result = result_mailbox.get()
    assert isinstance(result, StrategyBarResult)
    assert len(result.cancel_intents) == 1
    assert result.cancel_intents[0].order_id == OrderId("ord-001")


# --- schedule_timer fires on_timer deterministically -------------------------


def test_timer_scheduler_fires_when_due_and_advances() -> None:
    scheduler = TimerScheduler()
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    scheduler.register(TimerSubscription(name="t", interval=timedelta(minutes=2), first_fire=start))

    assert scheduler.due(start) == (TimerEvent(name="t", time=start),)
    # Not yet due at +1m.
    assert scheduler.due(start + timedelta(minutes=1)) == ()
    # Due again at +2m.
    fired = scheduler.due(start + timedelta(minutes=2))
    assert fired == (TimerEvent(name="t", time=start + timedelta(minutes=2)),)


def test_timer_scheduler_catches_up_multiple_intervals_in_one_jump() -> None:
    scheduler = TimerScheduler()
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    scheduler.register(TimerSubscription(name="t", interval=timedelta(minutes=1), first_fire=start))
    fired = scheduler.due(start + timedelta(minutes=3))
    assert [event.time for event in fired] == [
        start,
        start + timedelta(minutes=1),
        start + timedelta(minutes=2),
        start + timedelta(minutes=3),
    ]


def test_strategy_actor_dispatches_on_timer_before_on_bar() -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)

    class TimerStrategy(Strategy):
        def __init__(self) -> None:
            self.timer_fires: list[TimerEvent] = []

        def initialize(self, ctx: StrategyContext) -> None:
            ctx.schedule_timer(
                "rebalance",
                timedelta(minutes=1),
                first_fire=start + timedelta(minutes=1),
            )

        def on_timer(self, ctx: StrategyContext, timer: TimerEvent) -> None:
            self.timer_fires.append(timer)

    strategy = TimerStrategy()
    ctx = StrategyContext()
    actor = StrategyActor(
        strategy=strategy,
        context=ctx,
        result_ref=ActorRef(mailbox=Mailbox()),
    )
    # First bar ends one minute after start: the timer is due.
    bar = Bar(
        instrument_id=_INSTRUMENT,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("100"),
        is_complete=True,
    )
    actor.handle(
        StrategyBarEvent(
            bar=bar,
            data=DataView(bars={_INSTRUMENT: [bar]}, as_of=bar.end_time),
            portfolio=_empty_portfolio(),
        )
    )
    assert len(strategy.timer_fires) == 1
    assert strategy.timer_fires[0].name == "rebalance"
    assert strategy.timer_fires[0].time == start + timedelta(minutes=1)


# --- subscribe_ticks is rejected explicitly on a bar-only runtime ------------


def test_pipeline_rejects_tick_subscription_explicitly() -> None:
    class TickStrategy(Strategy):
        def initialize(self, ctx: StrategyContext) -> None:
            ctx.subscribe_ticks(_asset())

    with pytest.raises(TickFeedUnavailableError, match="tick subscriptions are unavailable"):
        StrategyExecutionPipeline(
            strategy=TickStrategy(),
            strategy_id=StrategyId("strategy-a"),
            instrument_registry=None,
            future_chain_registry=None,
            portfolio_view=lambda snapshot, *, latest_prices: _empty_portfolio(),
            prune_history=False,
        )


def test_pipeline_allows_bar_subscription() -> None:
    class BarStrategy(Strategy):
        def initialize(self, ctx: StrategyContext) -> None:
            ctx.subscribe(_asset(), timeframe="1m", warmup=2)

    pipeline = StrategyExecutionPipeline(
        strategy=BarStrategy(),
        strategy_id=StrategyId("strategy-a"),
        instrument_registry=None,
        future_chain_registry=None,
        portfolio_view=lambda snapshot, *, latest_prices: _empty_portfolio(),
        prune_history=False,
    )
    assert pipeline.subscriptions[0].timeframe == "1m"


# --- a strategy fill carries the originating intent_id -----------------------


def test_strategy_actor_delivers_fill_with_intent_id() -> None:
    received: list[Fill] = []

    class FillStrategy(Strategy):
        def on_fill(self, ctx: StrategyContext, fill: Fill) -> None:
            received.append(fill)

    ctx = StrategyContext()
    actor = StrategyActor(
        strategy=FillStrategy(),
        context=ctx,
        result_ref=ActorRef(mailbox=Mailbox()),
    )
    order_fill = OrderFill(
        fill_id="fill-001",
        order_id=OrderId("ord-001"),
        instrument_id=_INSTRUMENT,
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("101"),
        account_id=AccountId("acct-a"),
        intent_id="intent-xyz",
    )
    actor.handle(StrategyFillEvent(fills=(order_fill,)))

    assert len(received) == 1
    assert received[0].intent_id == "intent-xyz"
    assert received[0].fill_id == "fill-001"


def test_intent_id_propagates_order_intent_to_order_fill() -> None:
    """Domain-level: an OrderFill carries its OrderIntent's intent_id end to end."""
    from qts.domain.orders import ExecutionReport, ExecutionReportStatus
    from qts.execution.order_manager import OrderManager

    manager = OrderManager()
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        account_id=AccountId("acct-a"),
        instrument_id=_INSTRUMENT,
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        intent_id="intent-abc",
    )
    manager.create_order(intent, risk_decision=RiskDecision.approve())
    manager.mark_sent(intent.order_id, broker_order_id="broker-001")
    result = manager.process_report(
        ExecutionReport(
            report_id="rpt-001",
            broker_order_id="broker-001",
            status=ExecutionReportStatus.FILLED,
            filled_quantity=Decimal("10"),
            fill_price=Decimal("101"),
            fill_id="fill-001",
        )
    )
    assert result.fills[0].intent_id == "intent-abc"
