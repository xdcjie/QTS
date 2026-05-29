"""Runtime event store interfaces and local implementations."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
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
from qts.core.time import Clock, SystemClock
from qts.domain.events import BaseEvent
from qts.runtime.sinks.base import RuntimeEvent

StoredEvent = BaseEvent | RuntimeEvent

MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]


class SingleWriterViolation(RuntimeError):
    """Raised when a second writer tries to open an already-locked store."""


class SchemaMigrationMissing(KeyError):
    """Raised when an event's stored schema version has no registered migration."""


class SchemaMigrationRegistry:
    """Registry of (kind, from_version) -> migration that advances to to_version.

    Owner of the schema-evolution contract on the read path. Migrations are
    chained: an event tagged ``from_version="0"`` will be advanced through
    every registered hop until no further migration matches the current
    version. The final version becomes the event's ``payload_schema_version``.

    Unknown historical versions raise :class:`SchemaMigrationMissing`; events
    already at the current version pass through unchanged.
    """

    def __init__(self) -> None:
        self._migrations: dict[tuple[str, str], tuple[str, MigrationFn]] = {}

    def register(
        self,
        *,
        kind: str,
        from_version: str,
        to_version: str,
        migrate: MigrationFn,
    ) -> None:
        """Register a migration hop for one event kind/version pair."""
        if from_version == to_version:
            raise ValueError("from_version and to_version must differ")
        key = (kind, from_version)
        if key in self._migrations:
            raise ValueError(
                f"migration already registered for kind={kind!r} from_version={from_version!r}"
            )
        self._migrations[key] = (to_version, migrate)

    def size(self) -> int:
        """Return the number of registered migration hops."""
        return len(self._migrations)

    def registered_keys(self) -> frozenset[tuple[str, str]]:
        """Return the (kind, from_version) keys currently registered."""
        return frozenset(self._migrations.keys())

    def apply(self, event: RuntimeEvent) -> RuntimeEvent:
        """Advance one event through every registered migration hop in order.

        Termination rule:
        - apply hops while available for ``(kind, current_version)``;
        - once no hop matches, return the event as-is **unless** no hop
          was applied and the stored version differs from the canonical
          ``RuntimeEvent.SCHEMA_VERSION`` — in that case the registry is
          incomplete and :class:`SchemaMigrationMissing` is raised.

        This lets chained migrations terminate naturally at the final
        version even if it overshoots the current constant, while still
        catching historical events whose schema has no migration path at all.
        """
        current = event
        seen_versions: set[str] = set()
        applied_any = False
        while True:
            version = current.payload_schema_version
            if version in seen_versions:
                raise SchemaMigrationMissing(
                    f"migration cycle detected for kind={current.kind!r} version={version!r}"
                )
            seen_versions.add(version)
            key = (current.kind, version)
            hop = self._migrations.get(key)
            if hop is None:
                if not applied_any and version != RuntimeEvent.SCHEMA_VERSION:
                    raise SchemaMigrationMissing(
                        f"no migration registered for kind={current.kind!r} "
                        f"from_version={version!r}"
                    )
                return current
            applied_any = True
            to_version, migrate = hop
            current = replace(
                current,
                payload=migrate(dict(current.payload)),
                payload_schema_version=to_version,
            )


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

    def __init__(self, *, migration_registry: SchemaMigrationRegistry | None = None) -> None:
        """Perform __init__.

        When ``migration_registry`` is omitted, defaults to the canonical
        production registry from ``qts.runtime.event_migrations`` so a fresh
        production event store gets schema-aware replay out of the box.
        """
        self._events: list[StoredEvent] = []
        if migration_registry is None:
            from qts.runtime.event_migrations import canonical_runtime_event_migrations

            migration_registry = canonical_runtime_event_migrations()
        self._migration_registry = migration_registry

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
            return tuple(self._with_migration(event) for event in self._events)
        return tuple(
            self._with_migration(event)
            for event in self._events
            if self._partition_key(event) == partition_key
        )

    def replay_after(
        self,
        sequence: int,
        *,
        partition_key: str | None = None,
    ) -> tuple[StoredEvent, ...]:
        """Replay events appended after a 1-indexed sequence number."""
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        candidates = tuple(self._events[sequence:])
        if partition_key is None:
            return tuple(self._with_migration(event) for event in candidates)
        return tuple(
            self._with_migration(event)
            for event in candidates
            if self._partition_key(event) == partition_key
        )

    def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[StoredEvent, ...]:
        """Perform by_correlation_id."""
        return tuple(
            self._with_migration(event)
            for event in self._events
            if event.correlation_id == correlation_id
        )

    def _with_migration(self, event: StoredEvent) -> StoredEvent:
        """Apply registered schema migrations to RuntimeEvent payloads."""
        if self._migration_registry is None or not isinstance(event, RuntimeEvent):
            return event
        return self._migration_registry.apply(event)

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
    """JSONL event store for local deterministic recovery tests.

    On open the store seeds a monotonic sequence counter from the highest
    persisted sequence so each :meth:`append` is O(1) (no full-file re-read).
    A single-writer contract is enforced with an advisory ``flock`` acquired
    on the first :meth:`append` and held for the store's lifetime: a second
    writer that appends to the same path is rejected while the first is open.
    Read-only callers never acquire the lock. Persisted ingest timestamps come
    from an injected :class:`Clock` so a deterministic run produces
    byte-identical files.
    """

    def __init__(
        self,
        path: Path,
        *,
        clock: Clock | None = None,
        single_writer: bool = True,
    ) -> None:
        """Open the store and seed the monotonic sequence counter once."""
        self._path = path
        self._clock = clock if clock is not None else SystemClock()
        self._single_writer = single_writer
        self._lock_handle: Any | None = None
        self._next_sequence = self._highest_sequence() + 1

    def append(self, event: StoredEvent) -> int:
        """Append one event with a seeded O(1) sequence and clock-stamped ingest time."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._single_writer and self._lock_handle is None:
            self._acquire_writer_lock()
        sequence = self._next_sequence
        if isinstance(event, RuntimeEvent):
            event = replace(event, ts_ingest=self._clock.now())
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
        self._next_sequence = sequence + 1
        return sequence

    def close(self) -> None:
        """Release the advisory writer lock, allowing another writer to open."""
        handle = self._lock_handle
        if handle is None:
            return
        self._lock_handle = None
        try:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()

    def __del__(self) -> None:
        """Release the writer lock if the store is garbage-collected without close."""
        try:
            self.close()
        except Exception:
            pass

    def _acquire_writer_lock(self) -> None:
        """Acquire an exclusive advisory lock on a sidecar, held until close."""
        import fcntl

        self._path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self._path.with_name(self._path.name + ".lock")
        handle = lock_path.open("w", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            handle.close()
            raise SingleWriterViolation(
                f"another writer holds the event store lock for {self._path}"
            ) from error
        self._lock_handle = handle

    def _highest_sequence(self) -> int:
        """Return the highest persisted sequence number, or 0 when empty."""
        return max(self._read_sequences(), default=0)

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
    "Clock",
    "EventSequenceValidationReport",
    "EventStore",
    "FileEventStore",
    "InMemoryEventStore",
    "SingleWriterViolation",
    "StoredEvent",
    "SystemClock",
]
