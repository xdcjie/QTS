"""Adapters for converting domain events to WebSocket stream DTOs."""

from __future__ import annotations

from datetime import UTC, datetime

from qts.api.websocket.dtos import StreamEventDTO
from qts.execution.order_manager import OrderFill


def order_fill_to_stream_dto(
    fill: OrderFill,
    *,
    correlation_id: str | None = None,
) -> StreamEventDTO:
    """Convert an OrderManager-validated fill into a public stream event DTO."""
    return StreamEventDTO(
        event_type="order.fill",
        event_time=datetime.now(tz=UTC),
        payload={
            "fill_id": fill.fill_id,
            "order_id": str(fill.order_id.value),
            "instrument_id": str(fill.instrument_id.value),
            "side": fill.side.value,
            "quantity": str(fill.quantity),
            "price": str(fill.price),
        },
        correlation_id=correlation_id,
    )


__all__ = ["order_fill_to_stream_dto"]
