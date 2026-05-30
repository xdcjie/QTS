"""Order API routes."""

from __future__ import annotations

from fastapi import APIRouter

from qts.api.mappers import map_order_status_dto
from qts.api.schemas.common import OrderStatusSchema
from qts.application.services import OrderQueryService

router = APIRouter(prefix="/orders")

# No live order source is bound to this stateless API process; the service
# derives an honest not-found status from the empty query result.
_orders = OrderQueryService()


@router.get("/{order_id}", response_model=OrderStatusSchema)
def order_status(order_id: str) -> OrderStatusSchema:
    """Return order lifecycle status from the order query service."""
    return map_order_status_dto(_orders.order_status(order_id))


__all__ = ["router"]
