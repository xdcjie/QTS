"""WebSocket connection manager."""

from __future__ import annotations

from typing import Protocol


class JsonWebSocket(Protocol):
    async def accept(self) -> None: ...

    async def send_json(self, data: object) -> None: ...


class WebSocketConnectionManager:
    """Track WebSocket clients and broadcast JSON payloads."""

    def __init__(self) -> None:
        self._connections: list[JsonWebSocket] = []

    @property
    def count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: JsonWebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: JsonWebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, payload: object) -> None:
        stale: list[JsonWebSocket] = []
        for websocket in tuple(self._connections):
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)


__all__ = ["JsonWebSocket", "WebSocketConnectionManager"]
