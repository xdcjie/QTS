"""Risk request models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.core.time import require_aware_datetime


@dataclass(frozen=True, slots=True)
class OrderRiskRequest:
    """Pre-trade risk input for a proposed order."""

    instrument_id: InstrumentId
    quantity: Decimal
    price: Decimal
    multiplier: Decimal
    order_time: datetime | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if self.price < Decimal("0"):
            raise ValueError("price must be non-negative")
        if self.multiplier <= Decimal("0"):
            raise ValueError("multiplier must be positive")
        if self.order_time is not None:
            require_aware_datetime(self.order_time, name="order_time")

    @property
    def notional(self) -> Decimal:
        """Perform notional."""
        return self.quantity * self.price * self.multiplier


__all__ = ["OrderRiskRequest"]
