"""Runtime event store interfaces and local implementations."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from qts.core.ids import CausationId, CorrelationId, EventId
from qts.domain.events import BaseEvent


@dataclass(frozen=True, slots=True)
class EventSequenceValidationReport:
    """Validation result for persisted event sequence numbers."""

    valid: bool
    missing_sequences: tuple[int, ...] = ()
    duplicate_sequences: tuple[int, ...] = ()


class EventStore(Protocol):
    """Append-only event store contract."""

    def append(self, event: BaseEvent) -> int:
        """Append an event to the store and return its sequence index."""
        ...

    def replay(self, *, partition_key: str | None = None) -> tuple[BaseEvent, ...]:
        """Replay events from the store, optionally filtered by partition key."""
        ...

    def replay_after(
        self,
        sequence: int,
        *,
        partition_key: str | None = None,
    ) -> tuple[BaseEvent, ...]:
        """Replay events after a persisted sequence number."""
        ...

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[BaseEvent, ...]:
        """Replay all events with a given correlation identifier."""
        ...


class InMemoryEventStore:
    """Deterministic append-only in-memory event store."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._events: list[BaseEvent] = []

    def append(self, event: BaseEvent) -> int:
        """Perform append."""
        self._events.append(event)
        return len(self._events)

    def append_many(self, events: Iterable[BaseEvent]) -> None:
        """Perform append_many."""
        for event in events:
            self.append(event)

    def replay(self, *, partition_key: str | None = None) -> tuple[BaseEvent, ...]:
        """Perform replay."""
        if partition_key is None:
            return tuple(self._events)
        return tuple(event for event in self._events if event.partition_key == partition_key)

    def replay_after(
        self,
        sequence: int,
        *,
        partition_key: str | None = None,
    ) -> tuple[BaseEvent, ...]:
        """Replay events appended after a 1-indexed sequence number."""
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        events = tuple(self._events[sequence:])
        if partition_key is None:
            return events
        return tuple(event for event in events if event.partition_key == partition_key)

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[BaseEvent, ...]:
        """Perform by_correlation_id."""
        return tuple(event for event in self._events if event.correlation_id == correlation_id)


class FileEventStore:
    """JSONL event store for local deterministic recovery tests."""

    def __init__(self, path: Path) -> None:
        """Perform __init__."""
        self._path = path

    def append(self, event: BaseEvent) -> int:
        """Perform append."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        sequence = len(self.replay()) + 1
        payload = {"sequence": sequence, "event": self._event_to_json(event)}
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
        return sequence

    def replay(self, *, partition_key: str | None = None) -> tuple[BaseEvent, ...]:
        """Perform replay."""
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

    def replay_after(
        self,
        sequence: int,
        *,
        partition_key: str | None = None,
    ) -> tuple[BaseEvent, ...]:
        """Replay persisted events after a 1-indexed sequence number."""
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not self._path.exists():
            return ()
        events: list[BaseEvent] = []
        with self._path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if int(record["sequence"]) <= sequence:
                    continue
                event = self._event_from_json(record["event"])
                if partition_key is None or event.partition_key == partition_key:
                    events.append(event)
        return tuple(events)

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[BaseEvent, ...]:
        """Perform by_correlation_id."""
        return tuple(event for event in self.replay() if event.correlation_id == correlation_id)

    def validate_sequence(self) -> EventSequenceValidationReport:
        """Detect missing or duplicate persisted sequence numbers."""

        sequences = self._read_sequences()
        seen: set[int] = set()
        duplicates: list[int] = []
        for sequence in sequences:
            if sequence in seen and sequence not in duplicates:
                duplicates.append(sequence)
            seen.add(sequence)
        highest = max(sequences, default=0)
        missing = tuple(sequence for sequence in range(1, highest + 1) if sequence not in seen)
        duplicate_tuple = tuple(sorted(duplicates))
        return EventSequenceValidationReport(
            valid=not missing and not duplicate_tuple,
            missing_sequences=missing,
            duplicate_sequences=duplicate_tuple,
        )

    @staticmethod
    def _event_to_json(event: BaseEvent) -> dict[str, Any]:
        """Perform _event_to_json."""
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
        """Perform _event_from_json."""
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

    def _read_sequences(self) -> tuple[int, ...]:
        if not self._path.exists():
            return ()
        sequences: list[int] = []
        with self._path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    sequences.append(int(json.loads(line)["sequence"]))
        return tuple(sequences)


__all__ = [
    "EventSequenceValidationReport",
    "EventStore",
    "FileEventStore",
    "InMemoryEventStore",
]
