"""WebSocket event stream with sequence tracking and replay support."""

from __future__ import annotations

from collections import deque
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from qts.api.auth_backend_factory import default_auth_backend
from qts.api.security import verify_websocket_authorization
from qts.api.websocket.manager import WebSocketConnectionManager
from qts.core.time import Clock, SystemClock

router = APIRouter()


manager = WebSocketConnectionManager()
_stream_sequence = 0
_stream_buffer: deque[dict[str, Any]] = deque(maxlen=128)
# Source of event timestamps. Injecting a deterministic clock lets tests
# (and any deterministic replay producer) stamp byte-identical event times;
# live serving keeps wall-clock UTC via the default SystemClock.
_clock: Clock = SystemClock()


def set_stream_clock(clock: Clock | None = None) -> None:
    """Set the clock used to stamp stream events (defaults to SystemClock)."""
    global _clock
    _clock = clock if clock is not None else SystemClock()


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
        "event_time_utc": _clock.now().isoformat(),
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
        "event_time_utc": _clock.now().isoformat(),
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
    """Build and broadcast one envelope to all active websocket clients.

    Internal-only: this is the fan-out entrypoint a future runtime event sink
    will call to push domain events onto the websocket stream. No production
    producer is wired yet, so the live ``/ws/events`` route currently serves
    only the synthetic snapshot plus client-driven replay. Wiring a real
    producer (e.g. a RuntimeEventSink) is out of scope here and tracked
    separately; the contract is locked by the unit tests in
    ``tests/unit/api/test_websocket_events_clock.py``.
    """
    event = _to_event(event_type, payload, correlation_id=correlation_id)
    await manager.broadcast(event)
    return event


@router.websocket("/ws/events")
async def event_stream(websocket: WebSocket) -> None:
    """Open a resumable event stream with sequence and replay support."""
    try:
        verify_websocket_authorization(
            default_auth_backend(),
            websocket.headers.get("authorization"),
        )
    except HTTPException as exc:
        close_code = 4403 if exc.status_code == 403 else 4401
        await websocket.close(code=close_code)
        return

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


__all__ = ["broadcast_stream_event", "router", "set_stream_clock"]
