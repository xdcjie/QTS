"""Gate tests for horizon-aware and volatility-targeted portfolio construction.

Verifies the documented sizing rules:
- Signal.confidence affects allocation (ConfidenceWeighted).
- Signal.magnitude affects allocation (Magnitude / HorizonAware).
- Signal.horizon changes target size (HorizonAware).
- The vol-targeted model scales position size inversely with volatility.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.portfolio_construction import (
    ConfidenceWeightedSignalPortfolioConstruction,
    HorizonAwareSignalPortfolioConstruction,
    MagnitudeWeightedSignalPortfolioConstruction,
    VolatilityTargetedSignalPortfolioConstruction,
)
from qts.strategy_sdk.signals import Signal, SignalDirection
from qts.strategy_sdk.target import TargetIntent, TargetIntentType

_GENERATED_AT = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)


def _asset(symbol: str) -> AssetRef:
    return AssetRef(
        instrument_id=InstrumentId(f"EQUITY.US.NASDAQ.{symbol}"),
        symbol=symbol,
    )


def _signal(
    asset: AssetRef,
    direction: SignalDirection,
    *,
    confidence: Decimal = Decimal("1"),
    magnitude: Decimal | None = None,
    horizon: timedelta = timedelta(days=1),
    volatility: Decimal | None = None,
) -> Signal:
    return Signal(
        asset=asset,
        direction=direction,
        generated_at=_GENERATED_AT,
        horizon=horizon,
        source_model="model-v1",
        confidence=confidence,
        magnitude=magnitude,
        volatility=volatility,
    )


def _percent(targets: tuple[TargetIntent, ...], asset: AssetRef) -> Decimal:
    target = next(t for t in targets if t.asset == asset)
    assert target.intent_type == TargetIntentType.PERCENT
    assert target.value is not None
    return target.value


# ---------------------------------------------------------------------------
# Confidence and magnitude affect allocation (existing axes still hold).
# ---------------------------------------------------------------------------


def test_confidence_affects_allocation() -> None:
    aapl, msft = _asset("AAPL"), _asset("MSFT")
    model = ConfidenceWeightedSignalPortfolioConstruction(
        target_gross_exposure=Decimal("1.0"), max_single_weight=Decimal("1.0")
    )
    targets = model.construct(
        (
            _signal(aapl, SignalDirection.UP, confidence=Decimal("0.8")),
            _signal(msft, SignalDirection.UP, confidence=Decimal("0.2")),
        )
    )
    assert _percent(targets, aapl) > _percent(targets, msft)


def test_magnitude_affects_allocation() -> None:
    aapl, msft = _asset("AAPL"), _asset("MSFT")
    model = MagnitudeWeightedSignalPortfolioConstruction(
        target_gross_exposure=Decimal("1.0"), max_single_weight=Decimal("1.0")
    )
    targets = model.construct(
        (
            _signal(aapl, SignalDirection.UP, magnitude=Decimal("3")),
            _signal(msft, SignalDirection.UP, magnitude=Decimal("1")),
        )
    )
    assert _percent(targets, aapl) > _percent(targets, msft)


# ---------------------------------------------------------------------------
# HorizonAware: horizon changes target size.
# ---------------------------------------------------------------------------


class TestHorizonAware:
    """Signal.horizon changes the target size under the horizon-aware model."""

    def test_shorter_horizon_gets_smaller_size(self) -> None:
        long_h, short_h = _asset("LONG"), _asset("SHORT")
        model = HorizonAwareSignalPortfolioConstruction(
            reference_horizon=timedelta(days=4),
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )
        targets = model.construct(
            (
                _signal(long_h, SignalDirection.UP, horizon=timedelta(days=4)),
                _signal(short_h, SignalDirection.UP, horizon=timedelta(days=1)),
            )
        )
        # Identical magnitude; only horizon differs.
        assert _percent(targets, long_h) > _percent(targets, short_h)

    def test_horizon_alone_changes_single_position_size_relative_to_magnitude(self) -> None:
        """Two signals identical except horizon receive different raw shares."""
        a, b = _asset("A"), _asset("B")
        model = HorizonAwareSignalPortfolioConstruction(
            reference_horizon=timedelta(days=2),
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )
        targets = model.construct(
            (
                _signal(a, SignalDirection.UP, magnitude=Decimal("1"), horizon=timedelta(days=2)),
                _signal(b, SignalDirection.UP, magnitude=Decimal("1"), horizon=timedelta(days=1)),
            )
        )
        # A horizon factor = 1, B horizon factor = 0.5 -> share 2:1 -> 2/3 and 1/3.
        assert abs(_percent(targets, a) - Decimal("2") / Decimal("3")) < Decimal("0.0001")
        assert abs(_percent(targets, b) - Decimal("1") / Decimal("3")) < Decimal("0.0001")

    def test_horizon_beyond_reference_is_full_weight(self) -> None:
        a, b = _asset("A"), _asset("B")
        model = HorizonAwareSignalPortfolioConstruction(
            reference_horizon=timedelta(days=2),
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )
        targets = model.construct(
            (
                _signal(a, SignalDirection.UP, horizon=timedelta(days=10)),
                _signal(b, SignalDirection.UP, horizon=timedelta(days=2)),
            )
        )
        # Both clamp to factor 1 -> equal weights.
        assert abs(_percent(targets, a) - _percent(targets, b)) < Decimal("0.0001")

    def test_rejects_non_positive_reference_horizon(self) -> None:
        with pytest.raises(ValueError, match="reference_horizon must be positive"):
            HorizonAwareSignalPortfolioConstruction(reference_horizon=timedelta(0))


# ---------------------------------------------------------------------------
# VolatilityTargeted: scales inversely with volatility.
# ---------------------------------------------------------------------------


class TestVolatilityTargeted:
    """The vol-targeted model scales position size inversely with volatility."""

    def test_higher_volatility_gets_smaller_position(self) -> None:
        low_vol, high_vol = _asset("LOWVOL"), _asset("HIGHVOL")
        model = VolatilityTargetedSignalPortfolioConstruction(
            target_volatility=Decimal("0.1"), max_single_weight=Decimal("1.0")
        )
        targets = model.construct(
            (
                _signal(low_vol, SignalDirection.UP, volatility=Decimal("0.1")),
                _signal(high_vol, SignalDirection.UP, volatility=Decimal("0.4")),
            )
        )
        assert _percent(targets, low_vol) > _percent(targets, high_vol)

    def test_weight_is_inverse_proportional_to_volatility(self) -> None:
        a, b = _asset("A"), _asset("B")
        model = VolatilityTargetedSignalPortfolioConstruction(
            target_volatility=Decimal("0.1"), max_single_weight=Decimal("1.0")
        )
        targets = model.construct(
            (
                _signal(a, SignalDirection.UP, volatility=Decimal("0.1")),  # 0.1/0.1 = 1.0
                _signal(b, SignalDirection.UP, volatility=Decimal("0.2")),  # 0.1/0.2 = 0.5
            )
        )
        assert _percent(targets, a) == Decimal("1.0") * Decimal("1")  # capped at 1.0
        # Inverse relation: halving vol doubles size (before cap), so a == 2*b.
        assert abs(_percent(targets, a) - Decimal("2") * _percent(targets, b)) < Decimal("0.0001")

    def test_direction_sign_preserved(self) -> None:
        up, down = _asset("UP"), _asset("DOWN")
        model = VolatilityTargetedSignalPortfolioConstruction(
            target_volatility=Decimal("0.1"), max_single_weight=Decimal("1.0")
        )
        targets = model.construct(
            (
                _signal(up, SignalDirection.UP, volatility=Decimal("0.2")),
                _signal(down, SignalDirection.DOWN, volatility=Decimal("0.2")),
            )
        )
        assert _percent(targets, up) > Decimal("0")
        assert _percent(targets, down) < Decimal("0")

    def test_cap_binds(self) -> None:
        a = _asset("A")
        model = VolatilityTargetedSignalPortfolioConstruction(
            target_volatility=Decimal("0.1"), max_single_weight=Decimal("0.25")
        )
        targets = model.construct(
            (_signal(a, SignalDirection.UP, volatility=Decimal("0.1")),)  # raw 1.0 -> capped 0.25
        )
        assert _percent(targets, a) == Decimal("0.25")

    def test_signals_without_volatility_are_skipped(self) -> None:
        a, b = _asset("A"), _asset("B")
        model = VolatilityTargetedSignalPortfolioConstruction(
            target_volatility=Decimal("0.1"), max_single_weight=Decimal("1.0")
        )
        targets = model.construct(
            (
                _signal(a, SignalDirection.UP, volatility=Decimal("0.2")),
                _signal(b, SignalDirection.UP),  # no volatility
            )
        )
        percent_assets = {t.asset for t in targets if t.intent_type == TargetIntentType.PERCENT}
        assert a in percent_assets
        assert b not in percent_assets

    def test_flat_signals_close(self) -> None:
        a, b = _asset("A"), _asset("B")
        model = VolatilityTargetedSignalPortfolioConstruction()
        targets = model.construct(
            (
                _signal(a, SignalDirection.UP, volatility=Decimal("0.2")),
                _signal(b, SignalDirection.FLAT),
            )
        )
        close = next(t for t in targets if t.asset == b)
        assert close.intent_type == TargetIntentType.CLOSE
        assert close.value is None

    def test_rejects_non_positive_target_volatility(self) -> None:
        with pytest.raises(ValueError, match="target_volatility must be finite and positive"):
            VolatilityTargetedSignalPortfolioConstruction(target_volatility=Decimal("0"))


def test_signal_rejects_non_positive_volatility() -> None:
    with pytest.raises(ValueError, match="volatility must be positive"):
        _signal(_asset("A"), SignalDirection.UP, volatility=Decimal("0"))
