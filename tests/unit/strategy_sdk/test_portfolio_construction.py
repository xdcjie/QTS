from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.context import StrategyContext
from qts.strategy_sdk.portfolio_construction import EqualWeightSignalPortfolioConstruction
from qts.strategy_sdk.signals import Signal, SignalDirection
from qts.strategy_sdk.target import TargetIntent, TargetIntentType


def _asset(symbol: str) -> AssetRef:
    return AssetRef(
        instrument_id=InstrumentId(f"EQUITY.US.NASDAQ.{symbol}"),
        symbol=symbol,
    )


def _signal(asset: AssetRef, direction: SignalDirection) -> Signal:
    return Signal(
        asset=asset,
        direction=direction,
        generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        horizon=timedelta(days=1),
        source_model="momentum-v1",
    )


def test_equal_weight_construction_turns_up_down_flat_signals_into_targets() -> None:
    aapl = _asset("AAPL")
    msft = _asset("MSFT")
    flat = _asset("FLAT")
    model = EqualWeightSignalPortfolioConstruction(gross_exposure=Decimal("1"))

    targets = model.construct(
        (
            _signal(aapl, SignalDirection.UP),
            _signal(msft, SignalDirection.DOWN),
            _signal(flat, SignalDirection.FLAT),
        )
    )

    assert all(isinstance(target, TargetIntent) for target in targets)
    assert [target.intent_type for target in targets] == [
        TargetIntentType.PERCENT,
        TargetIntentType.PERCENT,
        TargetIntentType.CLOSE,
    ]
    assert {target.asset: target.value for target in targets} == {
        aapl: Decimal("0.5"),
        msft: Decimal("-0.5"),
        flat: None,
    }


def test_equal_weight_construction_closes_flat_only_signals() -> None:
    aapl = _asset("AAPL")
    model = EqualWeightSignalPortfolioConstruction()

    targets = model.construct((_signal(aapl, SignalDirection.FLAT),))

    assert targets == (TargetIntent(asset=aapl, intent_type=TargetIntentType.CLOSE, value=None),)


def test_equal_weight_construction_requires_positive_gross_exposure() -> None:
    with pytest.raises(ValueError, match="gross_exposure must be finite and positive"):
        EqualWeightSignalPortfolioConstruction(gross_exposure=Decimal("0"))


@pytest.mark.parametrize(
    "gross_exposure",
    [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")],
)
def test_equal_weight_construction_rejects_non_finite_gross_exposure(
    gross_exposure: Decimal,
) -> None:
    with pytest.raises(ValueError, match="gross_exposure must be finite and positive"):
        EqualWeightSignalPortfolioConstruction(gross_exposure=gross_exposure)


def test_strategy_context_constructs_targets_from_active_signals() -> None:
    aapl = _asset("AAPL")
    ctx = StrategyContext()
    ctx.emit_signal(_signal(aapl, SignalDirection.UP))

    targets = ctx.construct_targets(EqualWeightSignalPortfolioConstruction())

    assert ctx.signals == ()
    assert targets == (
        TargetIntent(asset=aapl, intent_type=TargetIntentType.PERCENT, value=Decimal("1")),
    )
    assert ctx.intents == targets


def test_strategy_context_construct_targets_consumes_pending_signals_once() -> None:
    aapl = _asset("AAPL")
    ctx = StrategyContext()
    ctx.emit_signal(_signal(aapl, SignalDirection.UP))

    first = ctx.construct_targets(EqualWeightSignalPortfolioConstruction())
    second = ctx.construct_targets(EqualWeightSignalPortfolioConstruction())

    assert first == (
        TargetIntent(asset=aapl, intent_type=TargetIntentType.PERCENT, value=Decimal("1")),
    )
    assert second == ()
    assert ctx.intents == first
    assert ctx.signals == ()


def test_strategy_context_does_not_mix_new_opposite_signal_with_stale_signal() -> None:
    aapl = _asset("AAPL")
    ctx = StrategyContext()
    ctx.emit_signal(_signal(aapl, SignalDirection.UP))
    up_targets = ctx.construct_targets(EqualWeightSignalPortfolioConstruction())

    ctx.emit_signal(_signal(aapl, SignalDirection.DOWN))
    down_targets = ctx.construct_targets(EqualWeightSignalPortfolioConstruction())

    assert up_targets == (
        TargetIntent(asset=aapl, intent_type=TargetIntentType.PERCENT, value=Decimal("1")),
    )
    assert down_targets == (
        TargetIntent(asset=aapl, intent_type=TargetIntentType.PERCENT, value=Decimal("-1")),
    )
    assert ctx.intents == up_targets + down_targets
    assert ctx.signals == ()
