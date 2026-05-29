"""Strategy SDK portfolio construction models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Protocol

from qts.strategy_sdk.signals import Signal, SignalDirection
from qts.strategy_sdk.target import TargetIntent, TargetIntentType


class PortfolioConstructionModel(Protocol):
    """Converts active strategy signals into target intents."""

    def construct(self, signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
        """Construct target intents from active signals."""
        ...


def _apply_weight_cap(
    weights: dict[Signal, Decimal], max_single_weight: Decimal
) -> dict[Signal, Decimal]:
    """Cap each absolute weight at max_single_weight, preserving sign."""
    capped: dict[Signal, Decimal] = {}
    for signal, weight in weights.items():
        if abs(weight) > max_single_weight:
            capped[signal] = max_single_weight if weight > Decimal("0") else -max_single_weight
        else:
            capped[signal] = weight
    return capped


def _build_targets(
    flat_targets: tuple[TargetIntent, ...],
    final_weights: dict[Signal, Decimal],
) -> tuple[TargetIntent, ...]:
    """Build target intents from flat targets and final directional weights."""
    targets: list[TargetIntent] = list(flat_targets)
    for signal, weight in final_weights.items():
        targets.append(
            TargetIntent(
                asset=signal.asset,
                intent_type=TargetIntentType.PERCENT,
                value=weight,
            )
        )
    return tuple(targets)


def _flat_close_targets(signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
    """Build CLOSE intents for all FLAT signals."""
    return tuple(
        TargetIntent(
            asset=signal.asset,
            intent_type=TargetIntentType.CLOSE,
            value=None,
        )
        for signal in signals
        if signal.direction == SignalDirection.FLAT
    )


@dataclass(frozen=True, slots=True)
class EqualWeightSignalPortfolioConstruction:
    """Map directional signals to equal gross percent targets."""

    gross_exposure: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        """Validate portfolio construction configuration."""
        object.__setattr__(self, "gross_exposure", Decimal(str(self.gross_exposure)))
        if not self.gross_exposure.is_finite() or self.gross_exposure <= Decimal("0"):
            raise ValueError("gross_exposure must be finite and positive")

    def construct(self, signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
        """Convert UP/DOWN/FLAT signals into percent or close target intents."""
        directional = tuple(
            signal for signal in signals if signal.direction != SignalDirection.FLAT
        )
        if not directional:
            return tuple(
                TargetIntent(
                    asset=signal.asset,
                    intent_type=TargetIntentType.CLOSE,
                    value=None,
                )
                for signal in signals
                if signal.direction == SignalDirection.FLAT
            )

        unit = self.gross_exposure / Decimal(len(directional))
        targets: list[TargetIntent] = []
        for signal in signals:
            if signal.direction == SignalDirection.FLAT:
                targets.append(
                    TargetIntent(
                        asset=signal.asset,
                        intent_type=TargetIntentType.CLOSE,
                        value=None,
                    )
                )
            elif signal.direction == SignalDirection.UP:
                targets.append(
                    TargetIntent(
                        asset=signal.asset,
                        intent_type=TargetIntentType.PERCENT,
                        value=unit,
                    )
                )
            else:
                targets.append(
                    TargetIntent(
                        asset=signal.asset,
                        intent_type=TargetIntentType.PERCENT,
                        value=-unit,
                    )
                )
        return tuple(targets)


@dataclass(frozen=True, slots=True)
class ConfidenceWeightedSignalPortfolioConstruction:
    """Map directional signals to confidence-scaled percent targets.

    Base weight = target_gross_exposure / num_directional_signals.
    Each directional signal's weight is scaled by its confidence.
    Weights are normalized so total gross equals target_gross_exposure,
    then capped at max_single_weight. Gross stays at or below target
    when capping reduces total exposure.
    """

    target_gross_exposure: Decimal = Decimal("1.0")
    max_single_weight: Decimal = Decimal("0.25")

    def __post_init__(self) -> None:
        """Validate portfolio construction configuration."""
        object.__setattr__(self, "target_gross_exposure", Decimal(str(self.target_gross_exposure)))
        object.__setattr__(self, "max_single_weight", Decimal(str(self.max_single_weight)))
        if not self.target_gross_exposure.is_finite() or self.target_gross_exposure <= Decimal("0"):
            raise ValueError("target_gross_exposure must be finite and positive")
        if not self.max_single_weight.is_finite() or self.max_single_weight <= Decimal("0"):
            raise ValueError("max_single_weight must be finite and positive")

    def construct(self, signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
        """Convert UP/DOWN/FLAT signals into confidence-weighted percent or close intents."""
        directional = tuple(
            signal for signal in signals if signal.direction != SignalDirection.FLAT
        )
        flat_targets = _flat_close_targets(signals)

        if not directional:
            return flat_targets

        # Compute direction-signed, confidence-scaled raw weights.
        raw_weights: dict[Signal, Decimal] = {}
        for signal in directional:
            direction_sign = (
                Decimal("1") if signal.direction == SignalDirection.UP else Decimal("-1")
            )
            raw_weights[signal] = direction_sign * signal.confidence

        # Normalize so total gross equals target.
        total_raw = sum(abs(w) for w in raw_weights.values())
        if total_raw == Decimal("0"):
            return flat_targets

        norm_factor = self.target_gross_exposure / total_raw
        normalized: dict[Signal, Decimal] = {}
        for signal, weight in raw_weights.items():
            normalized[signal] = weight * norm_factor

        # Cap at max_single_weight; gross stays at or below target.
        final_weights = _apply_weight_cap(normalized, self.max_single_weight)

        return _build_targets(flat_targets, final_weights)


@dataclass(frozen=True, slots=True)
class MagnitudeWeightedSignalPortfolioConstruction:
    """Map directional signals to magnitude-scaled percent targets.

    Higher magnitude signals receive proportionally higher weights.
    Weights are normalized so total gross equals target_gross_exposure,
    then capped at max_single_weight. Gross stays at or below target
    when capping reduces total exposure.
    """

    target_gross_exposure: Decimal = Decimal("1.0")
    max_single_weight: Decimal = Decimal("0.25")

    def __post_init__(self) -> None:
        """Validate portfolio construction configuration."""
        object.__setattr__(self, "target_gross_exposure", Decimal(str(self.target_gross_exposure)))
        object.__setattr__(self, "max_single_weight", Decimal(str(self.max_single_weight)))
        if not self.target_gross_exposure.is_finite() or self.target_gross_exposure <= Decimal("0"):
            raise ValueError("target_gross_exposure must be finite and positive")
        if not self.max_single_weight.is_finite() or self.max_single_weight <= Decimal("0"):
            raise ValueError("max_single_weight must be finite and positive")

    def construct(self, signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
        """Convert UP/DOWN/FLAT signals into magnitude-weighted percent or close intents."""
        directional = tuple(
            signal for signal in signals if signal.direction != SignalDirection.FLAT
        )
        flat_targets = _flat_close_targets(signals)

        if not directional:
            return flat_targets

        # Use magnitude; default to Decimal("1") if not set so equal weight fallback.
        magnitudes: list[Decimal] = []
        for signal in directional:
            mag = signal.magnitude if signal.magnitude is not None else Decimal("1")
            magnitudes.append(mag)

        total_magnitude = sum(magnitudes)
        if total_magnitude == Decimal("0"):
            return flat_targets

        # Raw weight per signal proportional to its magnitude.
        raw_weights: dict[Signal, Decimal] = {}
        for signal, mag in zip(directional, magnitudes, strict=True):
            direction_sign = (
                Decimal("1") if signal.direction == SignalDirection.UP else Decimal("-1")
            )
            raw_weights[signal] = (
                direction_sign * (mag / total_magnitude) * self.target_gross_exposure
            )

        # Cap at max_single_weight; gross stays at or below target.
        final_weights = _apply_weight_cap(raw_weights, self.max_single_weight)

        return _build_targets(flat_targets, final_weights)


@dataclass(frozen=True, slots=True)
class RiskParitySignalPortfolioConstruction:
    """Map directional signals to risk-parity-scaled percent targets.

    Uses signal confidence as a proxy for inverse volatility:
    weight proportional to (1 / confidence), so lower confidence
    (proxy for higher risk/volatility) receives higher weight for
    diversification. Weights are normalized so total gross equals
    target_gross_exposure, then capped at max_single_weight. Gross
    stays at or below target when capping reduces total exposure.
    """

    target_gross_exposure: Decimal = Decimal("1.0")
    max_single_weight: Decimal = Decimal("0.25")

    def __post_init__(self) -> None:
        """Validate portfolio construction configuration."""
        object.__setattr__(self, "target_gross_exposure", Decimal(str(self.target_gross_exposure)))
        object.__setattr__(self, "max_single_weight", Decimal(str(self.max_single_weight)))
        if not self.target_gross_exposure.is_finite() or self.target_gross_exposure <= Decimal("0"):
            raise ValueError("target_gross_exposure must be finite and positive")
        if not self.max_single_weight.is_finite() or self.max_single_weight <= Decimal("0"):
            raise ValueError("max_single_weight must be finite and positive")

    def construct(self, signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
        """Convert UP/DOWN/FLAT signals into risk-parity percent or close intents."""
        directional = tuple(
            signal for signal in signals if signal.direction != SignalDirection.FLAT
        )
        flat_targets = _flat_close_targets(signals)

        if not directional:
            return flat_targets

        # Inverse-confidence: lower confidence -> higher weight.
        # Guard against zero confidence (use epsilon to avoid division by zero).
        epsilon = Decimal("0.01")
        inv_confidences: list[Decimal] = []
        for signal in directional:
            inv = Decimal("1") / max(signal.confidence, epsilon)
            inv_confidences.append(inv)

        total_inv = sum(inv_confidences)
        if total_inv == Decimal("0"):
            return flat_targets

        # Raw weight proportional to inverse confidence.
        raw_weights: dict[Signal, Decimal] = {}
        for signal, inv in zip(directional, inv_confidences, strict=True):
            direction_sign = (
                Decimal("1") if signal.direction == SignalDirection.UP else Decimal("-1")
            )
            raw_weights[signal] = direction_sign * (inv / total_inv) * self.target_gross_exposure

        # Cap at max_single_weight; gross stays at or below target.
        final_weights = _apply_weight_cap(raw_weights, self.max_single_weight)

        return _build_targets(flat_targets, final_weights)


@dataclass(frozen=True, slots=True)
class HorizonAwareSignalPortfolioConstruction:
    """Scale magnitude-weighted targets by each signal's forecast horizon.

    A shorter forecast horizon means the signal is expected to be acted on for
    less time, so it earns a smaller share of risk budget. Each directional
    signal's raw weight is its magnitude scaled by a horizon factor:

        horizon_factor = min(1, horizon / reference_horizon)

    so a horizon at or beyond ``reference_horizon`` keeps full size while shorter
    horizons are linearly down-weighted toward zero. Weights are normalized so
    total gross equals target_gross_exposure, then capped at max_single_weight.
    """

    reference_horizon: timedelta = timedelta(days=1)
    target_gross_exposure: Decimal = Decimal("1.0")
    max_single_weight: Decimal = Decimal("0.25")

    def __post_init__(self) -> None:
        """Validate portfolio construction configuration."""
        object.__setattr__(self, "target_gross_exposure", Decimal(str(self.target_gross_exposure)))
        object.__setattr__(self, "max_single_weight", Decimal(str(self.max_single_weight)))
        if self.reference_horizon <= timedelta(0):
            raise ValueError("reference_horizon must be positive")
        if not self.target_gross_exposure.is_finite() or self.target_gross_exposure <= Decimal("0"):
            raise ValueError("target_gross_exposure must be finite and positive")
        if not self.max_single_weight.is_finite() or self.max_single_weight <= Decimal("0"):
            raise ValueError("max_single_weight must be finite and positive")

    def construct(self, signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
        """Convert UP/DOWN/FLAT signals into horizon-scaled percent or close intents."""
        directional = tuple(
            signal for signal in signals if signal.direction != SignalDirection.FLAT
        )
        flat_targets = _flat_close_targets(signals)

        if not directional:
            return flat_targets

        raw_weights: dict[Signal, Decimal] = {}
        for signal in directional:
            mag = signal.magnitude if signal.magnitude is not None else Decimal("1")
            direction_sign = (
                Decimal("1") if signal.direction == SignalDirection.UP else Decimal("-1")
            )
            raw_weights[signal] = direction_sign * abs(mag) * self._horizon_factor(signal)

        total_raw = sum(abs(w) for w in raw_weights.values())
        if total_raw == Decimal("0"):
            return flat_targets

        norm_factor = self.target_gross_exposure / total_raw
        normalized = {signal: weight * norm_factor for signal, weight in raw_weights.items()}

        final_weights = _apply_weight_cap(normalized, self.max_single_weight)
        return _build_targets(flat_targets, final_weights)

    def _horizon_factor(self, signal: Signal) -> Decimal:
        """Return the linear horizon down-weight in (0, 1]."""
        ratio = Decimal(signal.horizon.total_seconds()) / Decimal(
            self.reference_horizon.total_seconds()
        )
        return min(Decimal("1"), ratio)


@dataclass(frozen=True, slots=True)
class VolatilityTargetedSignalPortfolioConstruction:
    """Size positions inversely to forecast volatility to target unit risk.

    For each directional signal with a positive ``volatility`` (a per-asset
    realized/forecast standard deviation), the raw position weight is

        weight = direction_sign * (target_volatility / signal.volatility)

    so a higher-volatility asset receives a proportionally smaller position and
    every position carries roughly the same risk contribution. This is a true
    volatility target, not the confidence proxy used by RiskParity. Signals that
    do not carry a volatility are skipped. Weights are then capped at
    max_single_weight; gross is not renormalized so the realized portfolio
    volatility tracks ``target_volatility`` per position rather than a fixed
    gross.
    """

    target_volatility: Decimal = Decimal("0.1")
    max_single_weight: Decimal = Decimal("0.25")

    def __post_init__(self) -> None:
        """Validate portfolio construction configuration."""
        object.__setattr__(self, "target_volatility", Decimal(str(self.target_volatility)))
        object.__setattr__(self, "max_single_weight", Decimal(str(self.max_single_weight)))
        if not self.target_volatility.is_finite() or self.target_volatility <= Decimal("0"):
            raise ValueError("target_volatility must be finite and positive")
        if not self.max_single_weight.is_finite() or self.max_single_weight <= Decimal("0"):
            raise ValueError("max_single_weight must be finite and positive")

    def construct(self, signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
        """Convert UP/DOWN/FLAT signals into vol-targeted percent or close intents."""
        directional = tuple(
            signal
            for signal in signals
            if signal.direction != SignalDirection.FLAT and signal.volatility is not None
        )
        flat_targets = _flat_close_targets(signals)

        if not directional:
            return flat_targets

        raw_weights: dict[Signal, Decimal] = {}
        for signal in directional:
            assert signal.volatility is not None  # filtered above
            direction_sign = (
                Decimal("1") if signal.direction == SignalDirection.UP else Decimal("-1")
            )
            raw_weights[signal] = direction_sign * (self.target_volatility / signal.volatility)

        final_weights = _apply_weight_cap(raw_weights, self.max_single_weight)
        return _build_targets(flat_targets, final_weights)


__all__ = [
    "ConfidenceWeightedSignalPortfolioConstruction",
    "EqualWeightSignalPortfolioConstruction",
    "HorizonAwareSignalPortfolioConstruction",
    "MagnitudeWeightedSignalPortfolioConstruction",
    "PortfolioConstructionModel",
    "RiskParitySignalPortfolioConstruction",
    "VolatilityTargetedSignalPortfolioConstruction",
]
