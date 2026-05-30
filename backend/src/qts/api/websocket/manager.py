"""WebSocket connection manager."""

from __future__ import annotations

from typing import Protocol


class JsonWebSocket(Protocol):
    """Minimal WebSocket protocol used by the connection manager."""

    async def accept(self) -> None:
        """Accept the WebSocket connection."""
        ...

    async def send_json(self, data: object) -> None:
        """Send a JSON-serializable payload."""
        ...


class WebSocketConnectionManager:
    """Track WebSocket clients and broadcast JSON payloads."""

    def __init__(self) -> None:
        self._connections: list[JsonWebSocket] = []

    @property
    def count(self) -> int:
        """Return the number of currently tracked connections."""
        return len(self._connections)

    async def connect(self, websocket: JsonWebSocket) -> None:
        """Accept the WebSocket and add it to the tracked connections."""
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: JsonWebSocket) -> None:
        """Remove the WebSocket from the tracked connections if present."""
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, payload: object) -> None:
        """Send the payload to every connection, dropping ones that fail to send."""
        stale: list[JsonWebSocket] = []
        for websocket in tuple(self._connections):
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)


__all__ = ["JsonWebSocket", "WebSocketConnectionManager"]
