"""Snapshot value objects for reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.execution.order_manager import OrderSide


@dataclass(frozen=True, slots=True)
class OrderSnapshot:
    """Normalized representation of an internal or broker order."""

    order_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    status: str

    def __post_init__(self) -> None:
        """Validate normalized order snapshot values."""
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if not self.status.strip():
            raise ValueError("status must not be empty")


@dataclass(frozen=True, slots=True)
class ReconciliationPositionSnapshot:
    """Normalized position entry used for reconciliation."""

    instrument_id: InstrumentId
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class ReconciliationCashSnapshot:
    """Normalized cash entry used for reconciliation."""

    currency: str
    balance: Decimal

    def __post_init__(self) -> None:
        """Validate normalized cash snapshot values."""
        if not self.currency.strip():
            raise ValueError("currency must not be empty")


@dataclass(frozen=True, slots=True)
class ReconciliationSnapshot:
    """Normalized account snapshot used by the reconciliation engine."""

    account_id: AccountId
    orders: tuple[OrderSnapshot, ...] = ()
    positions: tuple[ReconciliationPositionSnapshot, ...] = ()
    cash: tuple[ReconciliationCashSnapshot, ...] = ()


__all__ = [
    "OrderSnapshot",
    "ReconciliationCashSnapshot",
    "ReconciliationPositionSnapshot",
    "ReconciliationSnapshot",
]
