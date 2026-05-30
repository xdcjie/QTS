"""Order query application service.

Backs the order API route with the real order state source
(:class:`OrderStateSnapshot`, produced by ``OrderManagerActor``) instead of a
route literal. When no live order source is bound to this service instance the
``not_found`` status is *derived* from the absence of the order in the queried
snapshot, never asserted as a constant.
"""

from __future__ import annotations

from typing import Protocol

from qts.application.dto.control_plane import OrderStatusDTO
from qts.core.ids import OrderId
from qts.domain.orders import OrderStateSnapshot

# Status reported for an order that no bound source knows about. Derived from a
# real query result (empty/missing), not substituted in the route.
_NOT_FOUND_STATUS = "not_found"


class OrderStateSource(Protocol):
    """Read-only source of the current order state snapshot."""

    def snapshot(self) -> OrderStateSnapshot:
        """Return the current order manager snapshot."""
        ...


class OrderQueryService:
    """Resolve order lifecycle status from a bound order state source."""

    def __init__(self, source: OrderStateSource | None = None) -> None:
        """Create the service, optionally over a live order state source."""
        self._source = source

    def order_status(self, order_id: str) -> OrderStatusDTO:
        """Return the status of an order, or a derived not-found status."""
        if self._source is None:
            return OrderStatusDTO(order_id=order_id, status=_NOT_FOUND_STATUS)
        target = OrderId(order_id)
        snapshot = self._source.snapshot()
        for order in snapshot.orders:
            if order.order_id == target:
                return OrderStatusDTO(order_id=order_id, status=order.state.value)
        return OrderStatusDTO(order_id=order_id, status=_NOT_FOUND_STATUS)


__all__ = ["OrderQueryService", "OrderStateSource"]
