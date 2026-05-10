"""Adapters for converting domain events to WebSocket stream DTOs."""

from __future__ import annotations

from datetime import UTC, datetime

from qts.api.websocket.dtos import StreamEventDTO
from qts.application.dto import OrderFillDTO


def order_fill_to_stream_dto(
    fill: OrderFillDTO,
    *,
    correlation_id: str | None = None,
) -> StreamEventDTO:
    """Convert an OrderManager-validated fill into a public stream event DTO."""
    return StreamEventDTO(
        event_type="order.fill",
        event_time=datetime.now(tz=UTC),
        payload={
            "fill_id": fill.fill_id,
            "order_id": fill.order_id,
            "instrument_id": fill.instrument_id,
            "side": fill.side,
            "quantity": str(fill.quantity),
            "price": str(fill.price),
        },
        correlation_id=correlation_id,
    )


__all__ = ["order_fill_to_stream_dto"]
