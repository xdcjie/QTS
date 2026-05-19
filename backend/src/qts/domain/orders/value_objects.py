"""Order domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.orders.order_spec import OrderSpec


class OrderState(StrEnum):
    """Execution lifecycle states for orders."""

    CREATED = "created"
    SENT = "sent"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_REQUESTED = "cancel_requested"
    REPLACE_REQUESTED = "replace_requested"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderSide(StrEnum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """Approved order instruction before broker submission."""

    order_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    account_id: AccountId | None = None
    order_spec: OrderSpec = OrderSpec()

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")


@dataclass(frozen=True, slots=True)
class CancelIntent:
    """Intent to cancel an order through OrderManager."""

    order_id: OrderId
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReplaceIntent:
    """Intent to replace an order through OrderManager."""

    order_id: OrderId
    new_quantity: Decimal

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.new_quantity <= Decimal("0"):
            raise ValueError("new_quantity must be positive")


@dataclass(frozen=True, slots=True)
class Order:
    """Order snapshot owned by OrderManager."""

    order_id: OrderId
    intent: OrderIntent
    state: OrderState
    broker_order_id: str | None = None


class ExecutionReportStatus(StrEnum):
    """Normalized broker report status."""

    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    """Normalized broker execution report."""

    report_id: str
    broker_order_id: str
    status: ExecutionReportStatus
    filled_quantity: Decimal = Decimal("0")
    fill_price: Decimal | None = None
    fill_id: str | None = None
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")
    fill_time: datetime | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        if self.filled_quantity < Decimal("0"):
            raise ValueError("filled_quantity must be non-negative")
        if self.commission < Decimal("0"):
            raise ValueError("commission must be non-negative")
        if self.slippage < Decimal("0"):
            raise ValueError("slippage must be non-negative")


@dataclass(frozen=True, slots=True)
class OrderFill:
    """OrderManager-validated fill event."""

    fill_id: str
    order_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")
    account_id: AccountId | None = None


@dataclass(frozen=True, slots=True)
class OrderProcessingResult:
    """Events emitted by processing an execution report."""

    order: Order
    fills: tuple[OrderFill, ...] = ()


OrderManagerResult = OrderProcessingResult


@dataclass(frozen=True, slots=True)
class OrderStateSnapshot:
    """Serializable OrderManager state for reconnect/recovery."""

    orders: tuple[Order, ...]
    broker_to_order: tuple[tuple[str, OrderId], ...]
    seen_fill_ids: tuple[str, ...] = ()
    seen_report_ids: tuple[str, ...] = ()


OrderManagerSnapshot = OrderStateSnapshot


__all__ = [
    "CancelIntent",
    "ExecutionReport",
    "ExecutionReportStatus",
    "OrderManagerResult",
    "OrderManagerSnapshot",
    "OrderProcessingResult",
    "OrderState",
    "OrderStateSnapshot",
    "Order",
    "OrderFill",
    "OrderIntent",
    "OrderSide",
    "OrderSpec",
    "ReplaceIntent",
]
