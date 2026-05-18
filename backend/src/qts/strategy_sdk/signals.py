"""Strategy SDK signal value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from qts.core.time import require_aware_datetime
from qts.strategy_sdk.asset_ref import AssetRef


class SignalDirection(StrEnum):
    """Forecast direction expressed by a strategy signal."""

    UP = "up"
    DOWN = "down"
    FLAT = "flat"


@dataclass(frozen=True, slots=True)
class Signal:
    """Forecast emitted by a strategy before portfolio construction."""

    asset: AssetRef
    direction: SignalDirection
    generated_at: datetime
    horizon: timedelta
    source_model: str
    confidence: Decimal = Decimal("1")
    magnitude: Decimal | None = None
    weight: Decimal | None = None
    group_id: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize signal metadata."""
        try:
            direction = SignalDirection(self.direction)
        except ValueError as exc:
            raise ValueError("direction must be one of: up, down, flat") from exc
        object.__setattr__(self, "direction", direction)
        confidence = Decimal(str(self.confidence))
        if not confidence.is_finite():
            raise ValueError("confidence must be finite")
        object.__setattr__(self, "confidence", confidence)
        if self.magnitude is not None:
            magnitude = Decimal(str(self.magnitude))
            if not magnitude.is_finite():
                raise ValueError("magnitude must be finite")
            object.__setattr__(self, "magnitude", magnitude)
        if self.weight is not None:
            weight = Decimal(str(self.weight))
            if not weight.is_finite():
                raise ValueError("weight must be finite")
            object.__setattr__(self, "weight", weight)

        require_aware_datetime(self.generated_at, name="generated_at")
        if self.horizon <= timedelta(0):
            raise ValueError("horizon must be positive")
        if not self.source_model.strip():
            raise ValueError("source_model is required")
        if self.confidence < Decimal("0") or self.confidence > Decimal("1"):
            raise ValueError("confidence must be in [0, 1]")


__all__ = ["Signal", "SignalDirection"]
