"""WebSocket event stream with sequence tracking and replay support."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from qts.api.websocket.manager import WebSocketConnectionManager

router = APIRouter()


manager = WebSocketConnectionManager()
_stream_sequence = 0
_stream_buffer: deque[dict[str, Any]] = deque(maxlen=128)


def _next_sequence() -> int:
    """Allocate the next global stream sequence number."""
    global _stream_sequence
    _stream_sequence += 1
    return _stream_sequence


def _to_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    replayed: bool = False,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Build a typed stream envelope and append it to the replay buffer."""
    envelope = {
        "event_type": event_type,
        "sequence_number": _next_sequence(),
        "event_time_utc": datetime.now(tz=UTC).isoformat(),
        "payload": payload,
        "replayed": replayed,
        "correlation_id": correlation_id,
    }
    _stream_buffer.append(envelope)
    return envelope


def _snapshot_event() -> dict[str, Any]:
    """Return a synthetic bootstrap snapshot payload."""
    return _to_event("snapshot", {"samples": []})


def _resync_event(from_sequence: int) -> dict[str, Any]:
    """Build a stream resync event."""
    oldest = int(_stream_buffer[0]["sequence_number"])
    return {
        "event_type": "stream.resync_required",
        "sequence_number": _next_sequence(),
        "event_time_utc": datetime.now(tz=UTC).isoformat(),
        "payload": {
            "from_sequence": from_sequence,
            "oldest_available_sequence": oldest,
            "reason": "out-of-buffer",
        },
        "replayed": False,
        "correlation_id": None,
    }


async def _emit_replay(socket: WebSocket, from_sequence: int) -> None:
    """Replay buffered events newer than `from_sequence` to the given socket."""
    if not _stream_buffer:
        return

    oldest = int(_stream_buffer[0]["sequence_number"])
    if from_sequence < oldest - 1:
        await socket.send_json(_resync_event(from_sequence))
        return

    for event in tuple(_stream_buffer):
        if int(event["sequence_number"]) > from_sequence:
            replayed = dict(event)
            replayed["replayed"] = True
            # Best-effort; if transport fails, the connection is closed upstream.
            await socket.send_json(replayed)


async def broadcast_stream_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Build and broadcast one envelope to all active websocket clients."""
    event = _to_event(event_type, payload, correlation_id=correlation_id)
    await manager.broadcast(event)
    return event


@router.websocket("/ws/events")
async def event_stream(websocket: WebSocket) -> None:
    """Open a resumable event stream with sequence and replay support."""
    await manager.connect(websocket)

    latest = _snapshot_event()
    await websocket.send_json(latest)

    try:
        while True:
            message = await websocket.receive_json()
            if not isinstance(message, dict):
                if message == "ping":
                    await websocket.send_json({"type": "pong", "ack": True})
                continue

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "ack": True})
                continue

            if message.get("type") == "replay" and isinstance(message.get("from_sequence"), int):
                await _emit_replay(websocket, int(message["from_sequence"]))
                continue
    except WebSocketDisconnect:
        manager.disconnect(websocket)


__all__ = ["router", "broadcast_stream_event"]
