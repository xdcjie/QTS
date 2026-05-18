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


@dataclass(frozen=True, slots=True)
class EqualWeightSignalPortfolioConstruction:
    """Map directional signals to equal gross percent targets."""

    gross_exposure: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        """Validate portfolio construction configuration."""
        object.__setattr__(self, "gross_exposure", Decimal(str(self.gross_exposure)))
        if self.gross_exposure <= Decimal("0"):
            raise ValueError("gross_exposure must be positive")

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


__all__ = ["EqualWeightSignalPortfolioConstruction", "PortfolioConstructionModel"]
