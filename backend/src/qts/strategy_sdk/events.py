"""User-facing Strategy SDK callback event types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.core.time import require_aware_datetime
from qts.domain.orders import OrderSide, OrderState


@dataclass(frozen=True, slots=True)
class TimerEvent:
    """Scheduled strategy timer event."""

    name: str
    time: datetime

    def __post_init__(self) -> None:
        """Validate timer event fields."""
        if not self.name.strip():
            raise ValueError("name must not be empty")
        require_aware_datetime(self.time, name="time")


@dataclass(frozen=True, slots=True)
class OrderUpdate:
    """Strategy-facing order status update."""

    order_id: OrderId
    state: OrderState
    filled_quantity: Decimal = Decimal("0")
    remaining_quantity: Decimal | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        """Validate order update quantities."""
        if self.filled_quantity < Decimal("0"):
            raise ValueError("filled_quantity must be non-negative")
        if self.remaining_quantity is not None and self.remaining_quantity < Decimal("0"):
            raise ValueError("remaining_quantity must be non-negative")


@dataclass(frozen=True, slots=True)
class Fill:
    """Strategy-facing fill event."""

    fill_id: str
    order_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")
    account_id: AccountId | None = None

    def __post_init__(self) -> None:
        """Validate fill economics."""
        if not self.fill_id.strip():
            raise ValueError("fill_id must not be empty")
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if self.price <= Decimal("0"):
            raise ValueError("price must be positive")
        if self.commission < Decimal("0"):
            raise ValueError("commission must be non-negative")
        if self.slippage < Decimal("0"):
            raise ValueError("slippage must be non-negative")


__all__ = ["Fill", "OrderUpdate", "TimerEvent"]
