"""Strategy SDK tests: cancel_order, target_bracket, schedule_timer, subscribe_ticks, intent_id."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId, OrderId
from qts.domain.orders import BracketSpec, CancelIntent, OrderSide, OrderType
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.context import StrategyContext
from qts.strategy_sdk.events import Fill, TimerSubscription
from qts.strategy_sdk.subscription_registry import DataSubscription
from qts.strategy_sdk.target import TargetIntent, TargetIntentType


def _make_asset(symbol: str = "AAPL") -> AssetRef:
    return AssetRef(InstrumentId(f"EQUITY.US.NASDAQ.{symbol}"), symbol)


def test_cancel_order_stores_cancel_intent() -> None:
    ctx = StrategyContext()
    ctx.cancel_order("ORD-001", reason="manual override")

    assert len(ctx.cancel_intents) == 1
    cancel = ctx.cancel_intents[0]
    assert isinstance(cancel, CancelIntent)
    assert cancel.order_id == OrderId("ORD-001")
    assert cancel.reason == "manual override"


def test_cancel_order_without_reason() -> None:
    ctx = StrategyContext()
    ctx.cancel_order("ORD-002")

    cancel = ctx.cancel_intents[0]
    assert cancel.reason is None


def test_cancel_order_multiple() -> None:
    ctx = StrategyContext()
    ctx.cancel_order("ORD-001")
    ctx.cancel_order("ORD-002", reason="risk limit")

    assert len(ctx.cancel_intents) == 2
    assert ctx.cancel_intents[0].order_id == OrderId("ORD-001")
    assert ctx.cancel_intents[1].order_id == OrderId("ORD-002")


def test_target_bracket_creates_bracket_order_spec_with_correct_legs() -> None:
    ctx = StrategyContext()
    asset = _make_asset()
    tp = Decimal("105")
    sl = Decimal("95")

    intent = ctx.target_bracket(asset, take_profit_price=tp, stop_loss_price=sl)

    assert isinstance(intent, TargetIntent)
    assert intent.intent_type == TargetIntentType.QUANTITY
    assert intent.value == Decimal("1")
    assert intent.asset == asset
    assert intent.order_spec.order_type == OrderType.BRACKET

    bracket = intent.order_spec.bracket
    assert bracket is not None
    assert isinstance(bracket, BracketSpec)
    assert len(bracket.legs) == 2

    tp_leg = bracket.legs[0]
    assert tp_leg.order_type == OrderType.LIMIT
    assert tp_leg.side == "sell"
    assert tp_leg.quantity == Decimal("1")
    assert tp_leg.limit_price == tp
    assert tp_leg.stop_price is None

    sl_leg = bracket.legs[1]
    assert sl_leg.order_type == OrderType.STOP
    assert sl_leg.side == "sell"
    assert sl_leg.quantity == Decimal("1")
    assert sl_leg.stop_price == sl
    assert sl_leg.limit_price is None


def test_target_bracket_with_custom_quantity() -> None:
    ctx = StrategyContext()
    asset = _make_asset()

    intent = ctx.target_bracket(
        asset,
        take_profit_price=Decimal("110"),
        stop_loss_price=Decimal("90"),
        quantity=Decimal("5"),
    )

    assert intent.value == Decimal("5")
    bracket = intent.order_spec.bracket
    assert bracket is not None
    assert bracket.legs[0].quantity == Decimal("5")
    assert bracket.legs[1].quantity == Decimal("5")


def test_target_bracket_appears_in_intents() -> None:
    ctx = StrategyContext()
    asset = _make_asset()

    intent = ctx.target_bracket(asset, Decimal("105"), Decimal("95"))

    assert ctx.intents == (intent,)


def test_schedule_timer_creates_timer_subscription() -> None:
    ctx = StrategyContext()
    interval = timedelta(minutes=15)

    subscription = ctx.schedule_timer("rebalance_timer", interval)

    assert isinstance(subscription, TimerSubscription)
    assert subscription.name == "rebalance_timer"
    assert subscription.interval == interval
    assert subscription.first_fire is None
    assert ctx.timer_subscriptions == (subscription,)


def test_schedule_timer_with_first_fire() -> None:
    ctx = StrategyContext()
    interval = timedelta(hours=1)
    first = datetime(2024, 6, 1, 9, 30, tzinfo=UTC)

    subscription = ctx.schedule_timer("hourly_check", interval, first_fire=first)

    assert subscription.first_fire == first


def test_schedule_timer_multiple() -> None:
    ctx = StrategyContext()

    sub_a = ctx.schedule_timer("timer_a", timedelta(minutes=5))
    sub_b = ctx.schedule_timer("timer_b", timedelta(minutes=30))

    assert ctx.timer_subscriptions == (sub_a, sub_b)


def test_subscribe_ticks_creates_data_subscription_with_tick_timeframe() -> None:
    ctx = StrategyContext()
    asset = _make_asset()

    subscription = ctx.subscribe_ticks(asset)

    assert isinstance(subscription, DataSubscription)
    assert subscription.asset == asset
    assert subscription.timeframe == "tick"
    assert subscription.warmup == 1


def test_subscribe_ticks_appears_in_subscriptions() -> None:
    ctx = StrategyContext()
    asset = _make_asset()

    subscription = ctx.subscribe_ticks(asset)

    assert ctx.subscriptions == (subscription,)


def test_target_intent_has_auto_generated_intent_id() -> None:
    asset = _make_asset()
    intent_a = TargetIntent(
        asset=asset,
        intent_type=TargetIntentType.QUANTITY,
        value=Decimal("100"),
    )
    intent_b = TargetIntent(
        asset=asset,
        intent_type=TargetIntentType.QUANTITY,
        value=Decimal("200"),
    )

    assert isinstance(intent_a.intent_id, str)
    assert len(intent_a.intent_id) > 0
    assert intent_a.intent_id != intent_b.intent_id


def test_target_intent_intent_id_via_context() -> None:
    ctx = StrategyContext()
    asset = _make_asset()

    intent = ctx.target_quantity(asset, Decimal("100"))

    assert isinstance(intent.intent_id, str)
    assert len(intent.intent_id) > 0


def test_fill_has_optional_intent_id_field() -> None:
    fill_without = Fill(
        fill_id="F-001",
        order_id=OrderId("ORD-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("100"),
        price=Decimal("150.25"),
    )

    assert fill_without.intent_id is None

    fill_with = Fill(
        fill_id="F-002",
        intent_id="some-intent-id",
        order_id=OrderId("ORD-002"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.SELL,
        quantity=Decimal("50"),
        price=Decimal("155.50"),
    )

    assert fill_with.intent_id == "some-intent-id"


def test_fill_intent_id_correlates_with_target_intent() -> None:
    ctx = StrategyContext()
    asset = _make_asset()

    intent = ctx.target_quantity(asset, Decimal("100"))

    fill = Fill(
        fill_id="F-001",
        intent_id=intent.intent_id,
        order_id=OrderId("ORD-001"),
        instrument_id=asset.instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("100"),
        price=Decimal("150.25"),
    )

    assert fill.intent_id == intent.intent_id


def test_fill_rejects_empty_intent_id() -> None:
    with pytest.raises(ValueError, match="intent_id must not be empty"):
        Fill(
            fill_id="F-001",
            intent_id="  ",
            order_id=OrderId("ORD-001"),
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            price=Decimal("150.25"),
        )
