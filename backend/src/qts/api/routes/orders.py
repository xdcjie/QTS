"""Order API routes."""

from __future__ import annotations

from fastapi import APIRouter

from qts.api.schemas.common import OrderStatusSchema

router = APIRouter(prefix="/orders")


@router.get("/{order_id}", response_model=OrderStatusSchema)
def order_status(order_id: str) -> OrderStatusSchema:
    """Perform order_status."""
    return OrderStatusSchema(order_id=order_id, status="unknown")


__all__ = ["router"]
