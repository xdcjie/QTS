"""WebSocket event stream skeleton."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/ws/events")
async def event_stream(websocket: WebSocket) -> None:
    """Perform event_stream."""
    await websocket.accept()
    await websocket.send_json(
        {
            "event_type": "system.synthetic",
            "message": "connected",
        }
    )
    await websocket.close()


__all__ = ["router"]
