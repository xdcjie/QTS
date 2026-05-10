"""Deterministic reconciliation snapshots and drift reports."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.execution.order_manager import OrderSide


class DriftKind(StrEnum):
    MATCHED = "matched"
    MISSING_AT_BROKER = "missing_at_broker"
    EXTRA_AT_BROKER = "extra_at_broker"
    DIVERGENT = "divergent"
    TOLERANCE_ONLY = "tolerance_only"


@dataclass(frozen=True, slots=True)
class OrderSnapshot:
    order_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    status: str

    def __post_init__(self) -> None:
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if not self.status.strip():
            raise ValueError("status must not be empty")


@dataclass(frozen=True, slots=True)
class PositionSnapshot:
    instrument_id: InstrumentId
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class CashSnapshot:
    currency: str
    balance: Decimal

    def __post_init__(self) -> None:
        if not self.currency.strip():
            raise ValueError("currency must not be empty")


@dataclass(frozen=True, slots=True)
class ReconciliationSnapshot:
    account_id: AccountId
    orders: tuple[OrderSnapshot, ...] = ()
    positions: tuple[PositionSnapshot, ...] = ()
    cash: tuple[CashSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class DriftItem:
    kind: DriftKind
    key: str
    internal: str | None
    broker: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "kind": self.kind.value,
            "key": self.key,
            "internal": self.internal,
            "broker": self.broker,
        }


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    account_id: AccountId
    items: tuple[DriftItem, ...]

    @property
    def has_drift(self) -> bool:
        return any(
            item.kind not in {DriftKind.MATCHED, DriftKind.TOLERANCE_ONLY} for item in self.items
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id.value,
            "has_drift": self.has_drift,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass(frozen=True, slots=True)
class StartupReconciliationDecision:
    """Startup gate result derived from reconciliation drift."""

    trading_enabled: bool
    report: ReconciliationReport
    reason_code: str | None = None


def startup_reconciliation_gate(report: ReconciliationReport) -> StartupReconciliationDecision:
    """Block trading on startup when reconciliation contains critical drift."""

    if report.has_drift:
        return StartupReconciliationDecision(
            trading_enabled=False,
            report=report,
            reason_code="RECONCILIATION_DRIFT",
        )
    return StartupReconciliationDecision(trading_enabled=True, report=report)


def reconcile_snapshots(
    *,
    internal: ReconciliationSnapshot,
    broker: ReconciliationSnapshot,
    tolerance: Decimal = Decimal("0"),
) -> ReconciliationReport:
    if internal.account_id != broker.account_id:
        raise ValueError("cannot reconcile different accounts")
    if tolerance < Decimal("0"):
        raise ValueError("tolerance must be non-negative")

    items = [
        *_compare_orders(internal.orders, broker.orders),
        *_compare_positions(internal.positions, broker.positions, tolerance),
        *_compare_cash(internal.cash, broker.cash, tolerance),
    ]
    return ReconciliationReport(
        account_id=internal.account_id,
        items=tuple(sorted(items, key=lambda item: _drift_sort_key(item.key))),
    )


def _compare_orders(
    internal: tuple[OrderSnapshot, ...], broker: tuple[OrderSnapshot, ...]
) -> list[DriftItem]:
    left = {item.order_id: item for item in internal}
    right = {item.order_id: item for item in broker}
    items: list[DriftItem] = []
    for order_id in sorted(left.keys() | right.keys(), key=lambda item: item.value):
        key = f"order:{order_id.value}"
        internal_order = left.get(order_id)
        broker_order = right.get(order_id)
        if internal_order is None:
            items.append(DriftItem(DriftKind.EXTRA_AT_BROKER, key, None, _order_repr(broker_order)))
        elif broker_order is None:
            items.append(
                DriftItem(DriftKind.MISSING_AT_BROKER, key, _order_repr(internal_order), None)
            )
        elif internal_order == broker_order:
            items.append(
                DriftItem(
                    DriftKind.MATCHED, key, _order_repr(internal_order), _order_repr(broker_order)
                )
            )
        else:
            items.append(
                DriftItem(
                    DriftKind.DIVERGENT, key, _order_repr(internal_order), _order_repr(broker_order)
                )
            )
    return items


def _compare_positions(
    internal: tuple[PositionSnapshot, ...],
    broker: tuple[PositionSnapshot, ...],
    tolerance: Decimal,
) -> list[DriftItem]:
    left = {item.instrument_id: item for item in internal}
    right = {item.instrument_id: item for item in broker}
    items: list[DriftItem] = []
    for instrument_id in sorted(left.keys() | right.keys(), key=lambda item: item.value):
        key = f"position:{instrument_id.value}"
        internal_position = left.get(instrument_id)
        broker_position = right.get(instrument_id)
        items.append(_quantity_item(key, internal_position, broker_position, tolerance))
    return items


def _compare_cash(
    internal: tuple[CashSnapshot, ...],
    broker: tuple[CashSnapshot, ...],
    tolerance: Decimal,
) -> list[DriftItem]:
    left = {item.currency: item for item in internal}
    right = {item.currency: item for item in broker}
    items: list[DriftItem] = []
    for currency in sorted(left.keys() | right.keys()):
        key = f"cash:{currency}"
        internal_cash = left.get(currency)
        broker_cash = right.get(currency)
        items.append(_quantity_item(key, internal_cash, broker_cash, tolerance))
    return items


def _quantity_item(
    key: str,
    internal: PositionSnapshot | CashSnapshot | None,
    broker: PositionSnapshot | CashSnapshot | None,
    tolerance: Decimal,
) -> DriftItem:
    if internal is None:
        return DriftItem(DriftKind.EXTRA_AT_BROKER, key, None, _amount_repr(broker))
    if broker is None:
        return DriftItem(DriftKind.MISSING_AT_BROKER, key, _amount_repr(internal), None)
    internal_amount = _amount(internal)
    broker_amount = _amount(broker)
    if internal_amount == broker_amount:
        kind = DriftKind.MATCHED
    elif abs(internal_amount - broker_amount) <= tolerance:
        kind = DriftKind.TOLERANCE_ONLY
    else:
        kind = DriftKind.DIVERGENT
    return DriftItem(kind, key, _amount_repr(internal), _amount_repr(broker))


def _order_repr(order: OrderSnapshot | None) -> str | None:
    if order is None:
        return None
    return f"{order.side.value}:{order.quantity}:{order.status}:{order.instrument_id.value}"


def _amount(item: PositionSnapshot | CashSnapshot) -> Decimal:
    if isinstance(item, PositionSnapshot):
        return item.quantity
    return item.balance


def _amount_repr(item: PositionSnapshot | CashSnapshot | None) -> str | None:
    if item is None:
        return None
    return str(_amount(item))


def _drift_sort_key(key: str) -> tuple[int, str]:
    prefix = key.split(":", 1)[0]
    order = {"order": 0, "position": 1, "cash": 2}
    return order[prefix], key


__all__ = [
    "CashSnapshot",
    "DriftItem",
    "DriftKind",
    "OrderSnapshot",
    "PositionSnapshot",
    "ReconciliationReport",
    "ReconciliationSnapshot",
    "StartupReconciliationDecision",
    "reconcile_snapshots",
    "startup_reconciliation_gate",
]
