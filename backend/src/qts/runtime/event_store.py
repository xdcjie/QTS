"""Runtime event store interfaces and local implementations."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from qts.core.ids import CausationId, CorrelationId, EventId
from qts.domain.events import BaseEvent


class EventStore(Protocol):
    """Append-only event store contract."""

    def append(self, event: BaseEvent) -> int: ...

    def replay(self, *, partition_key: str | None = None) -> tuple[BaseEvent, ...]: ...

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[BaseEvent, ...]: ...


class InMemoryEventStore:
    """Deterministic append-only in-memory event store."""

    def __init__(self) -> None:
        self._events: list[BaseEvent] = []

    def append(self, event: BaseEvent) -> int:
        self._events.append(event)
        return len(self._events)

    def append_many(self, events: Iterable[BaseEvent]) -> None:
        for event in events:
            self.append(event)

    def replay(self, *, partition_key: str | None = None) -> tuple[BaseEvent, ...]:
        if partition_key is None:
            return tuple(self._events)
        return tuple(event for event in self._events if event.partition_key == partition_key)

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[BaseEvent, ...]:
        return tuple(event for event in self._events if event.correlation_id == correlation_id)


class FileEventStore:
    """JSONL event store for local deterministic recovery tests."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, event: BaseEvent) -> int:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        sequence = len(self.replay()) + 1
        payload = {"sequence": sequence, "event": self._event_to_json(event)}
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
        return sequence

    def replay(self, *, partition_key: str | None = None) -> tuple[BaseEvent, ...]:
        if not self._path.exists():
            return ()
        events: list[BaseEvent] = []
        with self._path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = self._event_from_json(json.loads(line)["event"])
                if partition_key is None or event.partition_key == partition_key:
                    events.append(event)
        return tuple(events)

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[BaseEvent, ...]:
        return tuple(event for event in self.replay() if event.correlation_id == correlation_id)

    @staticmethod
    def _event_to_json(event: BaseEvent) -> dict[str, Any]:
        return {
            "event_id": event.event_id.value,
            "event_type": event.event_type,
            "event_time": event.event_time.isoformat(),
            "source": event.source,
            "partition_key": event.partition_key,
            "correlation_id": None if event.correlation_id is None else event.correlation_id.value,
            "causation_id": None if event.causation_id is None else event.causation_id.value,
        }

    @staticmethod
    def _event_from_json(payload: dict[str, Any]) -> BaseEvent:
        correlation_id = payload["correlation_id"]
        causation_id = payload["causation_id"]
        return BaseEvent(
            event_id=EventId(str(payload["event_id"])),
            event_type=str(payload["event_type"]),
            event_time=datetime.fromisoformat(str(payload["event_time"])),
            source=str(payload["source"]),
            partition_key=str(payload["partition_key"]),
            correlation_id=None if correlation_id is None else CorrelationId(str(correlation_id)),
            causation_id=None if causation_id is None else CausationId(str(causation_id)),
        )


__all__ = ["EventStore", "FileEventStore", "InMemoryEventStore"]
