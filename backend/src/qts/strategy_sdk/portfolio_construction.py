"""Strategy SDK portfolio construction models."""

from __future__ import annotations

from dataclasses import dataclass
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


__all__ = [
    "ConfidenceWeightedSignalPortfolioConstruction",
    "EqualWeightSignalPortfolioConstruction",
    "MagnitudeWeightedSignalPortfolioConstruction",
    "PortfolioConstructionModel",
    "RiskParitySignalPortfolioConstruction",
]
