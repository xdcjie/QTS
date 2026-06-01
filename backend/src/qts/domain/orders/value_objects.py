"""Order domain value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.orders.order_spec import OrderSide, OrderSpec


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


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """Approved order instruction before broker submission."""

    order_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    account_id: AccountId | None = None
    order_spec: OrderSpec = field(default_factory=OrderSpec)
    intent_id: str | None = None

    def __post_init__(self) -> None:
        """Validate quantity is positive and intent_id, if present, is non-empty."""
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if self.intent_id is not None and not self.intent_id.strip():
            raise ValueError("intent_id must not be empty if provided")


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
        """Validate the replacement quantity is positive."""
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
    reason_code: str | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate report/order ids are non-empty and quantities are non-negative."""
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
        if self.status is ExecutionReportStatus.REJECTED:
            if self.reason_code is None or not self.reason_code.strip():
                raise ValueError("reason_code is required for rejected execution reports")
            if self.failure_reason is None or not self.failure_reason.strip():
                raise ValueError("failure_reason is required for rejected execution reports")


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
    intent_id: str | None = None

    def __post_init__(self) -> None:
        """Validate optional intent correlation id."""
        if self.intent_id is not None and not self.intent_id.strip():
            raise ValueError("intent_id must not be empty if provided")


@dataclass(frozen=True, slots=True)
class OrderProcessingResult:
    """Events emitted by processing an execution report."""

    order: Order
    fills: tuple[OrderFill, ...] = ()


@dataclass(frozen=True, slots=True)
class OrderStateSnapshot:
    """Serializable OrderManager state for reconnect/recovery.

    ``seen_fill_ids`` / ``seen_report_ids`` are the global idempotency sets.
    ``fill_ids_by_order`` / ``report_ids_by_order`` carry the per-order ownership
    of those ids so that, after restore, compaction (``discard_terminal_order``)
    can remove only the ids belonging to a discarded order. Both default to
    empty for backward compatibility with snapshots produced before per-order
    ownership was tracked; ids absent from these maps are treated as
    global-non-compactable on restore (retained, never removed by discard).
    """

    orders: tuple[Order, ...]
    broker_to_order: tuple[tuple[str, OrderId], ...]
    seen_fill_ids: tuple[str, ...] = ()
    seen_report_ids: tuple[str, ...] = ()
    fill_ids_by_order: tuple[tuple[OrderId, tuple[str, ...]], ...] = ()
    report_ids_by_order: tuple[tuple[OrderId, tuple[str, ...]], ...] = ()


__all__ = [
    "CancelIntent",
    "ExecutionReport",
    "ExecutionReportStatus",
    "Order",
    "OrderFill",
    "OrderIntent",
    "OrderProcessingResult",
    "OrderSide",
    "OrderSpec",
    "OrderState",
    "OrderStateSnapshot",
    "ReplaceIntent",
]
