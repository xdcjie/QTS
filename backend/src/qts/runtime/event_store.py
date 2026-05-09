"""Runtime event store interfaces."""

from __future__ import annotations

from qts.domain.events import BaseEvent


class InMemoryEventStore:
    """Deterministic append-only in-memory event store."""

    def __init__(self) -> None:
        self._events: list[BaseEvent] = []

    def append(self, event: BaseEvent) -> None:
        self._events.append(event)

    def replay(self, *, partition_key: str | None = None) -> tuple[BaseEvent, ...]:
        if partition_key is None:
            return tuple(self._events)
        return tuple(event for event in self._events if event.partition_key == partition_key)


__all__ = ["InMemoryEventStore"]
