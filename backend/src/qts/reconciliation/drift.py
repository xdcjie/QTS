"""Diff primitives for reconciliation snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from .snapshots import CashSnapshot, OrderSnapshot, PositionSnapshot


class DriftKind(StrEnum):
    """Reconciliation drift categories."""

    MATCHED = "matched"
    MISSING_AT_BROKER = "missing_at_broker"
    EXTRA_AT_BROKER = "extra_at_broker"
    DIVERGENT = "divergent"
    TOLERANCE_ONLY = "tolerance_only"


@dataclass(frozen=True, slots=True)
class DriftItem:
    """Single discrepancy item between snapshots."""

    kind: DriftKind
    key: str
    internal: str | None
    broker: str | None

    def to_dict(self) -> dict[str, str | None]:
        """Serialize drift for observability output."""
        return {
            "kind": self.kind.value,
            "key": self.key,
            "internal": self.internal,
            "broker": self.broker,
        }


def compare_orders(
    internal: tuple[OrderSnapshot, ...],
    broker: tuple[OrderSnapshot, ...],
) -> list[DriftItem]:
    """Compare order snapshots and return drift entries."""
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
                    DriftKind.DIVERGENT,
                    key,
                    _order_repr(internal_order),
                    _order_repr(broker_order),
                )
            )
    return items


def compare_positions(
    internal: tuple[PositionSnapshot, ...],
    broker: tuple[PositionSnapshot, ...],
    tolerance: Decimal,
) -> list[DriftItem]:
    """Compare position snapshots and return drift entries."""
    left = {item.instrument_id: item for item in internal}
    right = {item.instrument_id: item for item in broker}
    items: list[DriftItem] = []
    for instrument_id in sorted(left.keys() | right.keys(), key=lambda item: item.value):
        key = f"position:{instrument_id.value}"
        internal_position = left.get(instrument_id)
        broker_position = right.get(instrument_id)
        items.append(_quantity_item(key, internal_position, broker_position, tolerance))
    return items


def compare_cash(
    internal: tuple[CashSnapshot, ...],
    broker: tuple[CashSnapshot, ...],
    tolerance: Decimal,
) -> list[DriftItem]:
    """Compare cash snapshots and return drift entries."""
    left = {item.currency: item for item in internal}
    right = {item.currency: item for item in broker}
    items: list[DriftItem] = []
    for currency in sorted(left.keys() | right.keys()):
        key = f"cash:{currency}"
        internal_cash = left.get(currency)
        broker_cash = right.get(currency)
        items.append(_quantity_item(key, internal_cash, broker_cash, tolerance))
    return items


def drift_sort_key(key: str) -> tuple[int, str]:
    """Stable sort order for reconciliation drift items."""
    prefix = key.split(":", 1)[0]
    order = {"order": 0, "position": 1, "cash": 2}
    return order[prefix], key


def _quantity_item(
    key: str,
    internal: PositionSnapshot | CashSnapshot | None,
    broker: PositionSnapshot | CashSnapshot | None,
    tolerance: Decimal,
) -> DriftItem:
    """Build drift record for comparable quantity-like entries."""
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
    """Serialize one normalized order snapshot."""
    if order is None:
        return None
    return f"{order.side.value}:{order.quantity}:{order.status}:{order.instrument_id.value}"


def _amount(item: PositionSnapshot | CashSnapshot) -> Decimal:
    """Return numeric amount for an order-independent snapshot entry."""
    if isinstance(item, PositionSnapshot):
        return item.quantity
    return item.balance


def _amount_repr(item: PositionSnapshot | CashSnapshot | None) -> str | None:
    """Serialize amount for drift output."""
    if item is None:
        return None
    return str(_amount(item))


__all__ = [
    "DriftItem",
    "DriftKind",
    "compare_cash",
    "compare_orders",
    "compare_positions",
    "drift_sort_key",
]
