from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import get_type_hints

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.market_data import Bar, Tick
from qts.domain.orders import OrderSide, OrderState
from qts.strategy_sdk import StrategyContext
from qts.strategy_sdk.events import Fill, OrderUpdate, TimerEvent


def _bar() -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
    )


def _tick() -> Tick:
    return Tick(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        price=Decimal("100"),
    )


def _timer() -> TimerEvent:
    return TimerEvent(name="market-open", time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC))


def _order_update() -> OrderUpdate:
    return OrderUpdate(order_id=OrderId("order-1"), state=OrderState.ACCEPTED)


def _fill() -> Fill:
    return Fill(
        fill_id="fill-1",
        order_id=OrderId("order-1"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("100"),
        account_id=AccountId("acct-1"),
    )


def test_strategy_default_hooks_are_noops() -> None:
    from qts.strategy_sdk.strategy import Strategy

    strategy = Strategy()
    ctx = StrategyContext()

    strategy.initialize(ctx)
    strategy.on_bar(ctx, _bar())
    strategy.on_tick(ctx, _tick())
    strategy.on_timer(ctx, _timer())
    strategy.on_order_update(ctx, _order_update())
    strategy.on_fill(ctx, _fill())


def test_strategy_hooks_can_be_overridden() -> None:
    from qts.strategy_sdk.strategy import Strategy

    class RecordingStrategy(Strategy):
        def __init__(self) -> None:
            self.seen = False

        def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
            self.seen = True

    strategy = RecordingStrategy()
    strategy.on_bar(StrategyContext(), _bar())

    assert strategy.seen


def test_strategy_callback_signatures_use_public_sdk_types() -> None:
    from qts.strategy_sdk.strategy import Strategy

    assert get_type_hints(Strategy.initialize)["ctx"] is StrategyContext
    assert get_type_hints(Strategy.finalize)["ctx"] is StrategyContext
    assert get_type_hints(Strategy.on_bar)["ctx"] is StrategyContext
    assert get_type_hints(Strategy.on_bar)["bar"] is Bar
    assert get_type_hints(Strategy.on_tick)["ctx"] is StrategyContext
    assert get_type_hints(Strategy.on_tick)["tick"] is Tick
    assert get_type_hints(Strategy.on_timer)["ctx"] is StrategyContext
    assert get_type_hints(Strategy.on_timer)["timer"] is TimerEvent
    assert get_type_hints(Strategy.on_order_update)["ctx"] is StrategyContext
    assert get_type_hints(Strategy.on_order_update)["update"] is OrderUpdate
    assert get_type_hints(Strategy.on_fill)["ctx"] is StrategyContext
    assert get_type_hints(Strategy.on_fill)["fill"] is Fill
