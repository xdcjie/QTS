"""StrategyContext composes focused subcontexts that own the SDK state (QTS-FINAL-005).

The facade keeps its public API but no longer owns emission/signal/timer/
subscription/universe state directly -- each lives in a focused subcontext.
These tests lock both the composition and that delegation produces identical
behaviour to the pre-split facade.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.strategy_sdk import AssetRef, StrategyContext
from qts.strategy_sdk.subcontexts import (
    AssetContext,
    PortfolioContext,
    SignalContext,
    SubscriptionContext,
    TargetContext,
    TimerContext,
    UniverseContext,
)


def _asset() -> AssetRef:
    return AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")


def test_facade_composes_focused_subcontexts() -> None:
    ctx = StrategyContext()
    assert isinstance(ctx.asset, AssetContext)
    assert isinstance(ctx.target, TargetContext)
    assert isinstance(ctx.subscription, SubscriptionContext)
    assert isinstance(ctx.signal, SignalContext)
    assert isinstance(ctx.timer, TimerContext)
    assert isinstance(ctx.universe_context, UniverseContext)
    assert isinstance(ctx.portfolio_context, PortfolioContext)


def test_facade_does_not_own_subcontext_state_directly() -> None:
    forbidden = {
        "_signals",
        "_cancel_intents",
        "_timer_subscriptions",
        "_subscription_registry",
        "_intent_emitter",
    }
    # slots=True dataclass: the facade exposes exactly its declared fields, none
    # of which is a forbidden state attribute -- the state lives on subcontexts.
    assert forbidden.isdisjoint(set(StrategyContext.__slots__))


def test_target_emission_routes_through_target_subcontext() -> None:
    ctx = StrategyContext()
    intent = ctx.target_percent(_asset(), Decimal("0.5"))
    # Facade view and the owning subcontext agree.
    assert ctx.intents == (intent,)
    assert ctx.target.pending_intents == (intent,)


def test_signal_emission_routes_through_signal_subcontext() -> None:
    from datetime import UTC, datetime

    from qts.strategy_sdk.signals import Signal, SignalDirection

    ctx = StrategyContext()
    signal = ctx.emit_signal(
        Signal(
            asset=_asset(),
            direction=SignalDirection.UP,
            generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            horizon=timedelta(days=1),
            source_model="momentum-v1",
        )
    )
    assert ctx.signals == (signal,)
    assert ctx.signal.pending == (signal,)


def test_cancel_emission_routes_through_target_subcontext() -> None:
    ctx = StrategyContext()
    ctx.cancel_order("ORD-1", reason="stale")
    assert len(ctx.cancel_intents) == 1
    assert ctx.cancel_intents == ctx.target.pending_cancels


def test_timer_subscription_routes_through_timer_subcontext() -> None:
    ctx = StrategyContext()
    sub = ctx.schedule_timer("rebalance", timedelta(minutes=5))
    assert ctx.timer_subscriptions == (sub,)
    assert ctx.timer.timer_subscriptions == (sub,)


def test_freeze_timers_rejects_later_schedule() -> None:
    import pytest

    ctx = StrategyContext()
    ctx.schedule_timer("init_timer", timedelta(minutes=1))
    ctx.freeze_timers()
    with pytest.raises(RuntimeError, match="initialization-only"):
        ctx.schedule_timer("late_timer", timedelta(minutes=1))


def test_subscription_routes_through_subscription_subcontext() -> None:
    ctx = StrategyContext()
    sub = ctx.subscribe(_asset(), timeframe="1m")
    assert ctx.subscriptions == (sub,)
    assert ctx.subscription.subscriptions == (sub,)


def test_universe_routes_through_universe_subcontext() -> None:
    ctx = StrategyContext()
    asset = _asset()
    ctx.set_universe([asset])
    assert ctx.universe == ctx.universe_context.universe
    assert asset.instrument_id in ctx.universe.instrument_ids
