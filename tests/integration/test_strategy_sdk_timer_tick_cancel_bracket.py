"""Integration gate: Strategy SDK order-lifecycle APIs wired through the runtime.

Drives the production ``BacktestActorLoop`` (the same loop ``BacktestEngine``
runs) for a strategy that schedules a timer, emits a bracket, and cancels a
resting order. Verifies, on the real backtest path:

- ``on_timer`` fires deterministically from bar/clock time;
- ``ctx.cancel_order`` reaches OrderManager and cancels the resting order;
- ``ctx.target_bracket`` produces a BRACKET order;
- a fill carries the originating ``intent_id`` back to ``on_fill``.

Tick subscriptions are rejected explicitly on this bar-only runtime, asserted
via ``TickFeedUnavailableError`` from the strategy execution pipeline.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.backtest.actor_loop import BacktestActorLoop, BacktestActorLoopState
from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
from qts.core.ids import AccountId, InstrumentId, StrategyId
from qts.domain.market_data import Bar
from qts.domain.orders import Order, OrderFill, OrderState, OrderType
from qts.reporting.backtest import EquityCurvePoint
from qts.runtime.actors.order_manager_actor import GetOrderManagerSnapshot
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.strategy_execution_pipeline import (
    StrategyExecutionPipeline,
    TickFeedUnavailableError,
)
from qts.strategy_sdk import Strategy, StrategyContext
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.events import Fill, TimerEvent
from qts.strategy_sdk.portfolio_view import PortfolioView
from qts.strategy_sdk.target import OrderSpec

from tests.support.backtest_engine import backtest_engine_from_inputs

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")
_RESTING_LIMIT_ORDER = "bt-000001"


def _bars(count: int) -> list[Bar]:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return [
        Bar(
            instrument_id=_INSTRUMENT,
            start_time=start + timedelta(minutes=i),
            end_time=start + timedelta(minutes=i + 1),
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal("100"),
            high=Decimal("100"),
            low=Decimal("100"),
            close=Decimal("100"),
            volume=Decimal("100"),
            is_complete=True,
        )
        for i in range(count)
    ]


class RecordingSink:
    """Minimal in-memory backtest sink that records orders and fills."""

    def __init__(self) -> None:
        self.events: list[RuntimeEvent] = []
        self.orders: list[Order] = []
        self.fills: list[OrderFill] = []
        self._order_count = 0

    @property
    def order_count(self) -> int:
        return self._order_count

    def write(self, event: RuntimeEvent) -> object:
        self.events.append(event)
        return event

    def write_processed(
        self,
        *,
        orders: tuple[Order, ...],
        fills: tuple[OrderFill, ...],
        bar: Bar,
    ) -> None:
        self.orders.extend(orders)
        self.fills.extend(fills)
        self._order_count += len(orders)

    def write_equity_point(self, point: EquityCurvePoint) -> None:
        return None

    def write_holdings_snapshot(self, *, gross_notional: Decimal, net_notional: Decimal) -> None:
        return None


class LifecycleStrategy(Strategy):
    """Schedules a timer, rests a limit order, cancels it, and brackets in."""

    def __init__(self) -> None:
        self.timer_fires: list[TimerEvent] = []
        self.fills: list[Fill] = []
        self.bracket_intent_id: str | None = None
        self._bar_index = 0

    def initialize(self, ctx: StrategyContext) -> None:
        # Timer fires at the end of the first bar and every minute after.
        ctx.schedule_timer(
            "rebalance",
            timedelta(minutes=1),
            first_fire=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        )

    def on_timer(self, ctx: StrategyContext, timer: TimerEvent) -> None:
        self.timer_fires.append(timer)

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        asset = ctx.symbol("AAPL")
        if self._bar_index == 0:
            # A buy limit well below market never fills: it rests as bt-000001.
            ctx.target_quantity(
                asset,
                Decimal("1"),
                spec=OrderSpec(order_type=OrderType.LIMIT, limit_price=Decimal("1")),
            )
        elif self._bar_index == 1:
            # Cancel the resting limit and enter via a bracket (parent fills).
            ctx.cancel_order(_RESTING_LIMIT_ORDER, reason="replace with bracket")
            bracket = ctx.target_bracket(
                asset,
                take_profit_price=Decimal("120"),
                stop_loss_price=Decimal("90"),
                quantity=Decimal("1"),
            )
            self.bracket_intent_id = bracket.intent_id
        self._bar_index += 1

    def on_fill(self, ctx: StrategyContext, fill: Fill) -> None:
        self.fills.append(fill)


def _run_lifecycle_strategy() -> tuple[LifecycleStrategy, RecordingSink, BacktestActorLoopState]:
    bars = _bars(3)
    strategy = LifecycleStrategy()
    account_id = AccountId("acct-backtest")
    strategy_id = StrategyId("strategy")
    # BacktestEngine assembles the production collaborators; we drive the loop
    # with compact_orders=False so a resting (non-terminal) order survives to be
    # cancelled on the next bar.
    engine = backtest_engine_from_inputs(
        strategy=strategy,
        bars=bars,
        initial_cash=Decimal("100000"),
    )
    loop = BacktestActorLoop(
        strategy=strategy,
        bars=iter(bars),
        config=BacktestActorLoopConfig(initial_cash=Decimal("100000")),
        dependencies=BacktestActorLoopDependencies(
            instrument_registry=engine._instrument_context.instrument_registry(),
            future_roll_registry=engine._future_roll_registry,
            contract_multipliers=engine._contract_multipliers,
            execution_adapter=engine._execution_adapter,
            process_intent=engine._intent_processor.process_intent,
            portfolio_view=engine._portfolio_projector.portfolio_view,
            equity_point=engine._portfolio_projector.equity_point,
            update_rolling_prices=engine._instrument_context.update_rolling_prices,
            execution_timing=engine._execution_timing,
        ),
        strategy_id=strategy_id,
        account_id=account_id,
    )
    sink = RecordingSink()
    state = loop.initialize_run_phase(sink=sink, prune_history=False, compact_orders=False)
    for source_bar in bars:
        loop.process_market_data_phase(state, source_bar)
    loop.finalize_run_phase(state)
    return strategy, sink, state


def test_timer_fires_through_backtest_runtime() -> None:
    strategy, _sink, _state = _run_lifecycle_strategy()

    fire_names = {event.name for event in strategy.timer_fires}
    assert fire_names == {"rebalance"}
    # Three bars ending at 14:31, 14:32, 14:33 each cross a one-minute boundary.
    assert len(strategy.timer_fires) == 3


def test_cancel_order_reaches_order_manager_and_cancels_resting_order() -> None:
    _strategy, _sink, state = _run_lifecycle_strategy()

    snapshot = state.order_manager_ref.ask(GetOrderManagerSnapshot())
    resting = {order.order_id.value: order for order in snapshot.orders}
    assert _RESTING_LIMIT_ORDER in resting
    assert resting[_RESTING_LIMIT_ORDER].state is OrderState.CANCELLED


def test_target_bracket_produces_bracket_order() -> None:
    _strategy, sink, _state = _run_lifecycle_strategy()

    bracket_orders = [
        order for order in sink.orders if order.intent.order_spec.order_type is OrderType.BRACKET
    ]
    assert bracket_orders, "expected at least one BRACKET order on the order flow"


def test_fill_carries_intent_id_back_to_on_fill() -> None:
    strategy, _sink, _state = _run_lifecycle_strategy()

    assert strategy.bracket_intent_id is not None
    bracket_fills = [
        fill for fill in strategy.fills if fill.intent_id == strategy.bracket_intent_id
    ]
    assert bracket_fills, "bracket fill must correlate back to its originating intent_id"
    assert bracket_fills[0].intent_id == strategy.bracket_intent_id


def test_tick_subscription_is_rejected_on_bar_only_runtime() -> None:
    class TickStrategy(Strategy):
        def initialize(self, ctx: StrategyContext) -> None:
            ctx.subscribe_ticks(AssetRef(_INSTRUMENT, "AAPL"))

    with pytest.raises(TickFeedUnavailableError):
        StrategyExecutionPipeline(
            strategy=TickStrategy(),
            strategy_id=StrategyId("strategy"),
            instrument_registry=None,
            future_chain_registry=None,
            portfolio_view=lambda snapshot, *, latest_prices: PortfolioView(
                cash=Decimal("0"), equity=Decimal("0")
            ),
            prune_history=False,
        )
