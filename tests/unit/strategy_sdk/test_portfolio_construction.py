from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.context import StrategyContext
from qts.strategy_sdk.portfolio_construction import (
    ConfidenceWeightedSignalPortfolioConstruction,
    EqualWeightSignalPortfolioConstruction,
    MagnitudeWeightedSignalPortfolioConstruction,
    RiskParitySignalPortfolioConstruction,
)
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


def _signal_with_confidence(
    asset: AssetRef, direction: SignalDirection, confidence: Decimal
) -> Signal:
    return Signal(
        asset=asset,
        direction=direction,
        confidence=confidence,
        generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        horizon=timedelta(days=1),
        source_model="momentum-v1",
    )


def _signal_with_magnitude(
    asset: AssetRef, direction: SignalDirection, magnitude: Decimal
) -> Signal:
    return Signal(
        asset=asset,
        direction=direction,
        magnitude=magnitude,
        generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        horizon=timedelta(days=1),
        source_model="momentum-v1",
    )


def _gross_of(targets: tuple[TargetIntent, ...]) -> Decimal:
    """Sum of absolute values of all PERCENT targets."""
    return sum(
        (
            abs(t.value)
            for t in targets
            if t.intent_type == TargetIntentType.PERCENT and t.value is not None
        ),
        Decimal("0"),
    )


def _percent_value(targets: list[TargetIntent], asset: AssetRef) -> Decimal:
    """Extract the Decimal value from a PERCENT target for a given asset."""
    t = next(ti for ti in targets if ti.asset == asset)
    assert t.intent_type == TargetIntentType.PERCENT
    assert t.value is not None
    return t.value


# ---------------------------------------------------------------------------
# ConfidenceWeighted tests
# ---------------------------------------------------------------------------


class TestConfidenceWeighted:
    """Tests for ConfidenceWeightedSignalPortfolioConstruction."""

    def test_higher_confidence_gets_higher_weight(self) -> None:
        """Higher confidence signals receive proportionally higher weights."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        # Use high max_single_weight so cap does not bind for proportional test.
        model = ConfidenceWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (
                _signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.8")),
                _signal_with_confidence(msft, SignalDirection.UP, Decimal("0.4")),
            )
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        aapl_weight = _percent_value(percent_targets, aapl)
        msft_weight = _percent_value(percent_targets, msft)
        assert aapl_weight > msft_weight

    def test_gross_exposure_equals_target_when_no_cap(self) -> None:
        """Total gross exposure equals target when max_single_weight does not bind."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = ConfidenceWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (
                _signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.9")),
                _signal_with_confidence(msft, SignalDirection.DOWN, Decimal("0.6")),
            )
        )

        gross = _gross_of(targets)
        assert abs(gross - Decimal("1.0")) < Decimal("0.001")

    def test_gross_within_bounds_when_cap_bind(self) -> None:
        """Gross exposure stays at or below target when cap reduces exposure."""
        aapl = _asset("AAPL")
        model = ConfidenceWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("0.25"),
        )

        targets = model.construct(
            (_signal_with_confidence(aapl, SignalDirection.UP, Decimal("1.0")),)
        )

        gross = _gross_of(targets)
        assert gross <= Decimal("1.0")
        assert gross > Decimal("0")

    def test_max_single_weight_cap(self) -> None:
        """No single weight exceeds max_single_weight."""
        aapl = _asset("AAPL")
        # Only one signal: all weight on one asset, capped at 0.25.
        model = ConfidenceWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("0.25"),
        )

        targets = model.construct(
            (_signal_with_confidence(aapl, SignalDirection.UP, Decimal("1.0")),)
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        assert len(percent_targets) == 1
        assert abs(_percent_value(percent_targets, aapl)) <= Decimal("0.25")

    def test_flat_signals_produce_close_intents(self) -> None:
        """FLAT signals produce CLOSE intents regardless of confidence."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = ConfidenceWeightedSignalPortfolioConstruction()

        targets = model.construct(
            (
                _signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.8")),
                _signal(msft, SignalDirection.FLAT),
            )
        )

        flat_target = next(t for t in targets if t.asset == msft)
        assert flat_target.intent_type == TargetIntentType.CLOSE
        assert flat_target.value is None

    def test_zero_confidence_directional_produces_no_targets(self) -> None:
        """All-zero confidence directional signals produce no targets."""
        aapl = _asset("AAPL")
        model = ConfidenceWeightedSignalPortfolioConstruction()

        targets = model.construct(
            (_signal_with_confidence(aapl, SignalDirection.UP, Decimal("0")),)
        )

        # Zero confidence: total_raw = 0, returns empty flat_targets.
        assert len(targets) == 0

    def test_no_directional_signals_returns_flat_targets(self) -> None:
        """Only FLAT signals produce only CLOSE intents."""
        aapl = _asset("AAPL")
        model = ConfidenceWeightedSignalPortfolioConstruction()

        targets = model.construct((_signal(aapl, SignalDirection.FLAT),))

        assert len(targets) == 1
        assert targets[0].intent_type == TargetIntentType.CLOSE

    def test_up_positive_down_negative(self) -> None:
        """UP signals get positive weights, DOWN signals get negative weights."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = ConfidenceWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (
                _signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.6")),
                _signal_with_confidence(msft, SignalDirection.DOWN, Decimal("0.6")),
            )
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        aapl_weight = _percent_value(percent_targets, aapl)
        msft_weight = _percent_value(percent_targets, msft)
        assert aapl_weight > Decimal("0")
        assert msft_weight < Decimal("0")

    def test_rejects_invalid_target_gross_exposure(self) -> None:
        """Rejects zero or non-finite target_gross_exposure."""
        with pytest.raises(ValueError, match="target_gross_exposure must be finite and positive"):
            ConfidenceWeightedSignalPortfolioConstruction(target_gross_exposure=Decimal("0"))

        with pytest.raises(ValueError, match="target_gross_exposure must be finite and positive"):
            ConfidenceWeightedSignalPortfolioConstruction(target_gross_exposure=Decimal("NaN"))

    def test_rejects_invalid_max_single_weight(self) -> None:
        """Rejects zero or non-finite max_single_weight."""
        with pytest.raises(ValueError, match="max_single_weight must be finite and positive"):
            ConfidenceWeightedSignalPortfolioConstruction(max_single_weight=Decimal("0"))

        with pytest.raises(ValueError, match="max_single_weight must be finite and positive"):
            ConfidenceWeightedSignalPortfolioConstruction(max_single_weight=Decimal("NaN"))


# ---------------------------------------------------------------------------
# MagnitudeWeighted tests
# ---------------------------------------------------------------------------


class TestMagnitudeWeighted:
    """Tests for MagnitudeWeightedSignalPortfolioConstruction."""

    def test_higher_magnitude_gets_higher_weight(self) -> None:
        """Higher magnitude signals receive proportionally higher weights."""
        # Use max_single_weight=1.0 so cap does not bind for proportional test.
        assets = [_asset(f"S{i}") for i in range(6)]
        model = MagnitudeWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        signals = (
            _signal_with_magnitude(assets[0], SignalDirection.UP, Decimal("3")),
            _signal_with_magnitude(assets[1], SignalDirection.UP, Decimal("1")),
            _signal_with_magnitude(assets[2], SignalDirection.UP, Decimal("1")),
            _signal_with_magnitude(assets[3], SignalDirection.UP, Decimal("1")),
            _signal_with_magnitude(assets[4], SignalDirection.UP, Decimal("1")),
            _signal_with_magnitude(assets[5], SignalDirection.UP, Decimal("1")),
        )

        targets = model.construct(signals)

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        high_mag_weight = _percent_value(percent_targets, assets[0])
        low_mag_weight = _percent_value(percent_targets, assets[1])
        assert high_mag_weight > low_mag_weight

    def test_gross_exposure_equals_target_when_no_cap(self) -> None:
        """Total gross exposure equals target when max_single_weight does not bind."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = MagnitudeWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (
                _signal_with_magnitude(aapl, SignalDirection.UP, Decimal("2")),
                _signal_with_magnitude(msft, SignalDirection.DOWN, Decimal("1")),
            )
        )

        gross = _gross_of(targets)
        assert abs(gross - Decimal("1.0")) < Decimal("0.001")

    def test_gross_within_bounds_when_cap_bind(self) -> None:
        """Gross exposure stays at or below target when cap reduces exposure."""
        aapl = _asset("AAPL")
        model = MagnitudeWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("0.25"),
        )

        targets = model.construct((_signal_with_magnitude(aapl, SignalDirection.UP, Decimal("5")),))

        gross = _gross_of(targets)
        assert gross <= Decimal("1.0")
        assert gross > Decimal("0")

    def test_max_single_weight_cap(self) -> None:
        """No single weight exceeds max_single_weight."""
        assets = [_asset(f"S{i}") for i in range(5)]
        model = MagnitudeWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("0.25"),
        )

        signals = tuple(
            _signal_with_magnitude(assets[0], SignalDirection.UP, Decimal("10"))
            if i == 0
            else _signal_with_magnitude(assets[i], SignalDirection.UP, Decimal("1"))
            for i in range(5)
        )

        targets = model.construct(signals)

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        for t in percent_targets:
            assert abs(_percent_value(percent_targets, t.asset)) <= Decimal("0.25")

    def test_flat_signals_produce_close_intents(self) -> None:
        """FLAT signals produce CLOSE intents."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = MagnitudeWeightedSignalPortfolioConstruction()

        targets = model.construct(
            (
                _signal_with_magnitude(aapl, SignalDirection.UP, Decimal("2")),
                _signal(msft, SignalDirection.FLAT),
            )
        )

        flat_target = next(t for t in targets if t.asset == msft)
        assert flat_target.intent_type == TargetIntentType.CLOSE
        assert flat_target.value is None

    def test_no_magnitude_defaults_to_equal_weight(self) -> None:
        """Signals without magnitude field default to magnitude=1 (equal weight)."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = MagnitudeWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (_signal(aapl, SignalDirection.UP), _signal(msft, SignalDirection.UP))
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        aapl_weight = _percent_value(percent_targets, aapl)
        msft_weight = _percent_value(percent_targets, msft)
        assert abs(aapl_weight - msft_weight) < Decimal("0.001")

    def test_zero_magnitudes_produce_no_targets(self) -> None:
        """All zero magnitudes produce no directional targets."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = MagnitudeWeightedSignalPortfolioConstruction()

        targets = model.construct(
            (
                _signal_with_magnitude(aapl, SignalDirection.UP, Decimal("0")),
                _signal_with_magnitude(msft, SignalDirection.DOWN, Decimal("0")),
            )
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        assert len(percent_targets) == 0

    def test_no_directional_signals_returns_flat_targets(self) -> None:
        """Only FLAT signals produce only CLOSE intents."""
        aapl = _asset("AAPL")
        model = MagnitudeWeightedSignalPortfolioConstruction()

        targets = model.construct((_signal(aapl, SignalDirection.FLAT),))

        assert len(targets) == 1
        assert targets[0].intent_type == TargetIntentType.CLOSE

    def test_up_positive_down_negative(self) -> None:
        """UP signals get positive weights, DOWN signals get negative weights."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = MagnitudeWeightedSignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (
                _signal_with_magnitude(aapl, SignalDirection.UP, Decimal("2")),
                _signal_with_magnitude(msft, SignalDirection.DOWN, Decimal("1")),
            )
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        aapl_weight = _percent_value(percent_targets, aapl)
        msft_weight = _percent_value(percent_targets, msft)
        assert aapl_weight > Decimal("0")
        assert msft_weight < Decimal("0")

    def test_rejects_invalid_target_gross_exposure(self) -> None:
        """Rejects zero or non-finite target_gross_exposure."""
        with pytest.raises(ValueError, match="target_gross_exposure must be finite and positive"):
            MagnitudeWeightedSignalPortfolioConstruction(target_gross_exposure=Decimal("0"))

        with pytest.raises(ValueError, match="target_gross_exposure must be finite and positive"):
            MagnitudeWeightedSignalPortfolioConstruction(target_gross_exposure=Decimal("NaN"))

    def test_rejects_invalid_max_single_weight(self) -> None:
        """Rejects zero or non-finite max_single_weight."""
        with pytest.raises(ValueError, match="max_single_weight must be finite and positive"):
            MagnitudeWeightedSignalPortfolioConstruction(max_single_weight=Decimal("0"))

        with pytest.raises(ValueError, match="max_single_weight must be finite and positive"):
            MagnitudeWeightedSignalPortfolioConstruction(max_single_weight=Decimal("NaN"))


# ---------------------------------------------------------------------------
# RiskParity tests
# ---------------------------------------------------------------------------


class TestRiskParity:
    """Tests for RiskParitySignalPortfolioConstruction."""

    def test_diversification_principle(self) -> None:
        """Lower confidence signals receive higher weight (inverse-confidence weighting)."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        # Use high max_single_weight so cap does not bind for proportional test.
        # With 2 signals, each weight ~0.5 > 0.25 default cap.
        model = RiskParitySignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (
                _signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.9")),
                _signal_with_confidence(msft, SignalDirection.UP, Decimal("0.5")),
            )
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        aapl_weight = _percent_value(percent_targets, aapl)
        msft_weight = _percent_value(percent_targets, msft)
        # Lower confidence (0.5) -> 1/0.5 = 2; Higher confidence (0.9) -> 1/0.9 ~ 1.11
        # msft_weight should be higher because lower confidence -> higher inverse
        assert msft_weight > aapl_weight

    def test_gross_exposure_equals_target_when_no_cap(self) -> None:
        """Total gross exposure equals target when max_single_weight does not bind."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = RiskParitySignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (
                _signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.8")),
                _signal_with_confidence(msft, SignalDirection.DOWN, Decimal("0.4")),
            )
        )

        gross = _gross_of(targets)
        assert abs(gross - Decimal("1.0")) < Decimal("0.001")

    def test_gross_within_bounds_when_cap_bind(self) -> None:
        """Gross exposure stays at or below target when cap reduces exposure."""
        aapl = _asset("AAPL")
        model = RiskParitySignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("0.25"),
        )

        targets = model.construct(
            (_signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.8")),)
        )

        gross = _gross_of(targets)
        assert gross <= Decimal("1.0")
        assert gross > Decimal("0")

    def test_max_single_weight_cap(self) -> None:
        """No single weight exceeds max_single_weight."""
        aapl = _asset("AAPL")
        # Only one signal: all weight on one asset, capped at 0.25.
        model = RiskParitySignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("0.25"),
        )

        targets = model.construct(
            (_signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.8")),)
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        assert len(percent_targets) == 1
        assert abs(_percent_value(percent_targets, aapl)) <= Decimal("0.25")

    def test_flat_signals_produce_close_intents(self) -> None:
        """FLAT signals produce CLOSE intents."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = RiskParitySignalPortfolioConstruction()

        targets = model.construct(
            (
                _signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.7")),
                _signal(msft, SignalDirection.FLAT),
            )
        )

        flat_target = next(t for t in targets if t.asset == msft)
        assert flat_target.intent_type == TargetIntentType.CLOSE
        assert flat_target.value is None

    def test_zero_confidence_handled_with_epsilon(self) -> None:
        """Zero confidence uses epsilon (0.01) to avoid division by zero."""
        aapl = _asset("AAPL")
        model = RiskParitySignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (_signal_with_confidence(aapl, SignalDirection.UP, Decimal("0")),)
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        assert len(percent_targets) == 1
        # Should produce a valid weight (not infinity or crash)
        assert _percent_value(percent_targets, aapl) > Decimal("0")

    def test_no_directional_signals_returns_flat_targets(self) -> None:
        """Only FLAT signals produce only CLOSE intents."""
        aapl = _asset("AAPL")
        model = RiskParitySignalPortfolioConstruction()

        targets = model.construct((_signal(aapl, SignalDirection.FLAT),))

        assert len(targets) == 1
        assert targets[0].intent_type == TargetIntentType.CLOSE

    def test_up_positive_down_negative(self) -> None:
        """UP signals get positive weights, DOWN signals get negative weights."""
        aapl = _asset("AAPL")
        msft = _asset("MSFT")
        model = RiskParitySignalPortfolioConstruction(
            target_gross_exposure=Decimal("1.0"),
            max_single_weight=Decimal("1.0"),
        )

        targets = model.construct(
            (
                _signal_with_confidence(aapl, SignalDirection.UP, Decimal("0.6")),
                _signal_with_confidence(msft, SignalDirection.DOWN, Decimal("0.6")),
            )
        )

        percent_targets = [t for t in targets if t.intent_type == TargetIntentType.PERCENT]
        aapl_weight = _percent_value(percent_targets, aapl)
        msft_weight = _percent_value(percent_targets, msft)
        assert aapl_weight > Decimal("0")
        assert msft_weight < Decimal("0")

    def test_rejects_invalid_target_gross_exposure(self) -> None:
        """Rejects zero or non-finite target_gross_exposure."""
        with pytest.raises(ValueError, match="target_gross_exposure must be finite and positive"):
            RiskParitySignalPortfolioConstruction(target_gross_exposure=Decimal("0"))

        with pytest.raises(ValueError, match="target_gross_exposure must be finite and positive"):
            RiskParitySignalPortfolioConstruction(target_gross_exposure=Decimal("NaN"))

    def test_rejects_invalid_max_single_weight(self) -> None:
        """Rejects zero or non-finite max_single_weight."""
        with pytest.raises(ValueError, match="max_single_weight must be finite and positive"):
            RiskParitySignalPortfolioConstruction(max_single_weight=Decimal("0"))

        with pytest.raises(ValueError, match="max_single_weight must be finite and positive"):
            RiskParitySignalPortfolioConstruction(max_single_weight=Decimal("NaN"))


# ---------------------------------------------------------------------------
# EqualWeight tests (original)
# ---------------------------------------------------------------------------


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

    assert len(targets) == 1
    target = targets[0]
    assert target.asset == aapl
    assert target.intent_type == TargetIntentType.CLOSE
    assert target.value is None


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
    assert len(targets) == 1
    assert targets[0].asset == aapl
    assert targets[0].intent_type == TargetIntentType.PERCENT
    assert targets[0].value == Decimal("1")
    assert ctx.intents == targets


def test_strategy_context_construct_targets_consumes_pending_signals_once() -> None:
    aapl = _asset("AAPL")
    ctx = StrategyContext()
    ctx.emit_signal(_signal(aapl, SignalDirection.UP))

    first = ctx.construct_targets(EqualWeightSignalPortfolioConstruction())
    second = ctx.construct_targets(EqualWeightSignalPortfolioConstruction())

    assert len(first) == 1
    assert first[0].asset == aapl
    assert first[0].intent_type == TargetIntentType.PERCENT
    assert first[0].value == Decimal("1")
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

    assert len(up_targets) == 1
    assert up_targets[0].asset == aapl
    assert up_targets[0].intent_type == TargetIntentType.PERCENT
    assert up_targets[0].value == Decimal("1")
    assert len(down_targets) == 1
    assert down_targets[0].asset == aapl
    assert down_targets[0].intent_type == TargetIntentType.PERCENT
    assert down_targets[0].value == Decimal("-1")
    assert ctx.intents == up_targets + down_targets
    assert ctx.signals == ()
