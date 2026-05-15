"""Runtime event store interfaces and local implementations."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from qts.core.ids import (
    AccountId,
    CausationId,
    CorrelationId,
    EventId,
    InstrumentId,
    RuntimeRunId,
    StrategyId,
)
from qts.domain.events import BaseEvent
from qts.runtime.sinks.base import RuntimeEvent

StoredEvent = BaseEvent | RuntimeEvent


@dataclass(frozen=True, slots=True)
class EventSequenceValidationReport:
    """Validation result for persisted event sequence numbers."""

    valid: bool
    missing_sequences: tuple[int, ...] = ()
    duplicate_sequences: tuple[int, ...] = ()


class EventStore(Protocol):
    """Append-only event store contract."""

    def append(self, event: StoredEvent) -> int:
        """Append an event to the store and return its sequence index."""
        ...

    def replay(self, *, partition_key: str | None = None) -> tuple[StoredEvent, ...]:
        """Replay events from the store, optionally filtered by partition key."""
        ...

    def replay_after(
        self,
        sequence: int,
        *,
        partition_key: str | None = None,
    ) -> tuple[StoredEvent, ...]:
        """Replay events after a persisted sequence number."""
        ...

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[StoredEvent, ...]:
        """Replay all events with a given correlation identifier."""
        ...


class InMemoryEventStore:
    """Deterministic append-only in-memory event store."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._events: list[StoredEvent] = []

    def append(self, event: StoredEvent) -> int:
        """Perform append."""
        self._events.append(event)
        return len(self._events)

    def append_many(self, events: Iterable[StoredEvent]) -> None:
        """Perform append_many."""
        for event in events:
            self.append(event)

    def replay(self, *, partition_key: str | None = None) -> tuple[StoredEvent, ...]:
        """Perform replay."""
        if partition_key is None:
            return tuple(self._events)
        return tuple(event for event in self._events if self._partition_key(event) == partition_key)

    def replay_after(
        self,
        sequence: int,
        *,
        partition_key: str | None = None,
    ) -> tuple[StoredEvent, ...]:
        """Replay events appended after a 1-indexed sequence number."""
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        events = tuple(self._events[sequence:])
        if partition_key is None:
            return events
        return tuple(event for event in events if self._partition_key(event) == partition_key)

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[StoredEvent, ...]:
        """Perform by_correlation_id."""
        return tuple(event for event in self._events if event.correlation_id == correlation_id)

    @staticmethod
    def _partition_key(event: StoredEvent) -> str | None:
        if isinstance(event, BaseEvent):
            return event.partition_key
        if event.payload.get("partition_key") is not None:
            return str(event.payload["partition_key"])
        if event.payload.get("order_id") is not None:
            return str(event.payload["order_id"])
        return event.kind


class FileEventStore:
    """JSONL event store for local deterministic recovery tests."""

    def __init__(self, path: Path) -> None:
        """Perform __init__."""
        self._path = path

    def append(self, event: StoredEvent) -> int:
        """Perform append."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        sequence = len(self.replay()) + 1
        if isinstance(event, RuntimeEvent):
            RuntimeEvent.require_canonical_envelope(event.to_envelope(sequence_no=sequence))
            payload = {
                "sequence": sequence,
                "runtime_event": self._runtime_event_to_json(event),
            }
        else:
            payload = {"sequence": sequence, "event": self._event_to_json(event)}
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        return sequence

    def replay(self, *, partition_key: str | None = None) -> tuple[StoredEvent, ...]:
        """Perform replay."""
        if not self._path.exists():
            return ()
        events: list[StoredEvent] = []
        with self._path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = self._event_from_record(json.loads(line))
                if partition_key is None or self._partition_key(event) == partition_key:
                    events.append(event)
        return tuple(events)

    def replay_after(
        self,
        sequence: int,
        *,
        partition_key: str | None = None,
    ) -> tuple[StoredEvent, ...]:
        """Replay persisted events after a 1-indexed sequence number."""
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not self._path.exists():
            return ()
        events: list[StoredEvent] = []
        with self._path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if int(record["sequence"]) <= sequence:
                    continue
                event = self._event_from_record(record)
                if partition_key is None or self._partition_key(event) == partition_key:
                    events.append(event)
        return tuple(events)

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[StoredEvent, ...]:
        """Perform by_correlation_id."""
        return tuple(event for event in self.replay() if event.correlation_id == correlation_id)

    @staticmethod
    def _partition_key(event: StoredEvent) -> str | None:
        return InMemoryEventStore._partition_key(event)

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

    @staticmethod
    def _runtime_event_to_json(event: RuntimeEvent) -> dict[str, Any]:
        return event.to_envelope()

    @staticmethod
    def _event_from_record(record: dict[str, Any]) -> StoredEvent:
        if "runtime_event" in record:
            return FileEventStore._runtime_event_from_json(record["runtime_event"])
        return FileEventStore._event_from_json(record["event"])

    @staticmethod
    def _runtime_event_from_json(payload: dict[str, Any]) -> RuntimeEvent:
        return RuntimeEvent(
            event_id=EventId(str(payload["event_id"])),
            parent_event_id=(
                None
                if payload.get("parent_event_id") is None
                else EventId(str(payload["parent_event_id"]))
            ),
            kind=str(payload["kind"]),
            payload=dict(payload["payload"]),
            run_id=RuntimeRunId(str(payload["run_id"])),
            mode=str(payload["runtime_mode"]),
            sequence_no=int(payload["sequence_no"]),
            ts_event=datetime.fromisoformat(str(payload["ts_event"])),
            ts_ingest=datetime.fromisoformat(str(payload["ts_ingest"])),
            account_id=(
                None if payload.get("account_id") is None else AccountId(str(payload["account_id"]))
            ),
            strategy_id=(
                None
                if payload.get("strategy_id") is None
                else StrategyId(str(payload["strategy_id"]))
            ),
            instrument_id=(
                None
                if payload.get("instrument_id") is None
                else InstrumentId(str(payload["instrument_id"]))
            ),
            correlation_id=(
                None
                if payload.get("correlation_id") is None
                else CorrelationId(str(payload["correlation_id"]))
            ),
            causation_id=(
                None
                if payload.get("causation_id") is None
                else CausationId(str(payload["causation_id"]))
            ),
            execution_environment=(
                None
                if payload.get("execution_environment") is None
                else str(payload["execution_environment"])
            ),
            payload_schema_version=str(payload["payload_schema_version"]),
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
    "StoredEvent",
]
