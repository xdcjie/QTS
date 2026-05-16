"""State snapshot and recovery interfaces."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from qts.core.hashing import stable_json_default
from qts.core.ids import RuntimeRunId
from qts.runtime.event_store import EventSequenceValidationReport
from qts.runtime.sinks.base import RuntimeEvent


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    """Serialized actor state snapshot envelope."""

    actor_id: str
    state_version: int
    payload: Any
    snapshot_id: str | None = None
    run_id: RuntimeRunId | None = None
    schema_version: str = "1"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_sequence: int = 0
    topology_hash: str | None = None
    config_hash: str | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.snapshot_id is not None and not self.snapshot_id.strip():
            raise ValueError("snapshot_id must not be empty")
        if not self.actor_id.strip():
            raise ValueError("actor_id must not be empty")
        if not self.schema_version.strip():
            raise ValueError("schema_version must not be empty")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.state_version < 0:
            raise ValueError("state_version must be non-negative")
        if self.last_sequence < 0:
            raise ValueError("last_sequence must be non-negative")
        if self.topology_hash is not None and not self.topology_hash.strip():
            raise ValueError("topology_hash must not be empty")
        if self.config_hash is not None and not self.config_hash.strip():
            raise ValueError("config_hash must not be empty")


class SnapshotStore(Protocol):
    """Durable snapshot store contract for actor recovery."""

    def save(self, snapshot: StateSnapshot) -> None:
        """Persist an actor state snapshot."""
        ...

    def load(self, actor_id: str) -> StateSnapshot | None:
        """Load the latest snapshot for an actor."""
        ...


class RuntimeRecoveryDecisionStatus(StrEnum):
    """Safety decision for runtime recovery."""

    ENTER_OBSERVATION = "enter_observation"
    ALLOW_LIVE = "allow_live"
    BLOCK = "block"


@dataclass(frozen=True, slots=True)
class RecoveryReadinessDecision:
    """Decision controlling whether event replay is safe for recovery."""

    recovery_allowed: bool
    reason_code: str | None = None
    missing_sequences: tuple[int, ...] = ()
    duplicate_sequences: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.recovery_allowed and self.reason_code is not None:
            raise ValueError("successful recovery decision must not have a reason_code")
        if not self.recovery_allowed and not self.reason_code:
            raise ValueError("blocked recovery decision requires a reason_code")


@dataclass(frozen=True, slots=True)
class RuntimeRecoveryDecision:
    """Recovery safety decision before order submission resumes."""

    status: RuntimeRecoveryDecisionStatus
    real_order_submission_enabled: bool
    reason_code: str | None = None

    def __post_init__(self) -> None:
        if self.status is RuntimeRecoveryDecisionStatus.ALLOW_LIVE:
            if not self.real_order_submission_enabled:
                raise ValueError("ALLOW_LIVE requires real_order_submission_enabled")
            if self.reason_code is not None:
                raise ValueError("ALLOW_LIVE decision must not have a reason_code")
        elif self.real_order_submission_enabled:
            raise ValueError("blocked or observation recovery cannot enable real orders")

    def to_manifest_payload(self) -> dict[str, object]:
        """Serialize recovery safety evidence for runtime manifests."""
        return {
            "status": self.status.value,
            "real_order_submission_enabled": self.real_order_submission_enabled,
            "reason_code": self.reason_code,
        }

    def to_runtime_event(self) -> RuntimeEvent:
        """Return an auditable runtime event for this recovery decision."""
        return RuntimeEvent(
            kind="runtime.recovery_decision",
            payload=self.to_manifest_payload(),
        )


class InMemorySnapshotStore:
    """In-memory snapshot store for deterministic tests and local recovery."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._snapshots: dict[str, StateSnapshot] = {}

    def save(self, snapshot: StateSnapshot) -> None:
        """Perform save."""
        self._snapshots[snapshot.actor_id] = snapshot

    def load(self, actor_id: str) -> StateSnapshot | None:
        """Perform load."""
        if not actor_id.strip():
            raise ValueError("actor_id must not be empty")
        return self._snapshots.get(actor_id)


class FileSnapshotStore:
    """Append-only JSONL snapshot store for local durable recovery."""

    def __init__(self, path: Path) -> None:
        """Perform __init__."""
        self._path = path

    def save(self, snapshot: StateSnapshot) -> None:
        """Perform save."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        existing = self._path.read_text(encoding="utf-8") if self._path.exists() else ""
        line = (
            json.dumps(
                self._snapshot_to_json(snapshot),
                default=stable_json_default,
                sort_keys=True,
            )
            + "\n"
        )
        tmp_path = self._path.with_name(f".{self._path.name}.tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(existing)
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, self._path)

    def load(self, actor_id: str) -> StateSnapshot | None:
        """Perform load."""
        if not actor_id.strip():
            raise ValueError("actor_id must not be empty")
        if not self._path.exists():
            return None
        latest: StateSnapshot | None = None
        with self._path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    snapshot = self._snapshot_from_json(json.loads(line))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue
                if snapshot.actor_id == actor_id:
                    latest = snapshot
        return latest

    @staticmethod
    def _snapshot_to_json(snapshot: StateSnapshot) -> dict[str, Any]:
        return {
            "snapshot_id": snapshot.snapshot_id,
            "actor_id": snapshot.actor_id,
            "run_id": None if snapshot.run_id is None else snapshot.run_id.value,
            "schema_version": snapshot.schema_version,
            "created_at": snapshot.created_at.isoformat(),
            "state_version": snapshot.state_version,
            "last_sequence": snapshot.last_sequence,
            "last_event_sequence_no": snapshot.last_sequence,
            "topology_hash": snapshot.topology_hash,
            "config_hash": snapshot.config_hash,
            "payload": snapshot.payload,
        }

    @staticmethod
    def _snapshot_from_json(payload: dict[str, Any]) -> StateSnapshot:
        return StateSnapshot(
            snapshot_id=(
                None if payload.get("snapshot_id") is None else str(payload["snapshot_id"])
            ),
            actor_id=str(payload["actor_id"]),
            run_id=None if payload.get("run_id") is None else RuntimeRunId(str(payload["run_id"])),
            schema_version=str(payload.get("schema_version", "1")),
            created_at=(
                datetime.fromisoformat(str(payload["created_at"]))
                if payload.get("created_at") is not None
                else datetime.now(UTC)
            ),
            state_version=int(payload["state_version"]),
            last_sequence=int(
                payload.get("last_event_sequence_no", payload.get("last_sequence", 0))
            ),
            topology_hash=(
                None if payload.get("topology_hash") is None else str(payload["topology_hash"])
            ),
            config_hash=None if payload.get("config_hash") is None else str(payload["config_hash"]),
            payload=payload["payload"],
        )


class DurableSnapshotStore(FileSnapshotStore):
    """Durable snapshot store boundary for production-like recovery wiring."""


@dataclass(frozen=True, slots=True)
class SnapshotFrequencyPolicy:
    """Policy for deciding when actor state should be snapshotted."""

    every_event_count: int | None = None
    every_elapsed: timedelta | None = None

    def __post_init__(self) -> None:
        if self.every_event_count is not None and self.every_event_count <= 0:
            raise ValueError("every_event_count must be positive when configured")
        if self.every_elapsed is not None and self.every_elapsed <= timedelta(0):
            raise ValueError("every_elapsed must be positive when configured")
        if self.every_event_count is None and self.every_elapsed is None:
            raise ValueError("at least one snapshot frequency trigger is required")

    def should_snapshot(self, *, event_count: int, elapsed: timedelta) -> bool:
        """Return whether the configured snapshot cadence has been reached."""

        if event_count < 0:
            raise ValueError("event_count must be non-negative")
        if elapsed < timedelta(0):
            raise ValueError("elapsed must be non-negative")
        event_count_reached = (
            self.every_event_count is not None and event_count >= self.every_event_count
        )
        elapsed_reached = self.every_elapsed is not None and elapsed >= self.every_elapsed
        return event_count_reached or elapsed_reached


def validate_event_sequence_for_recovery(
    report: EventSequenceValidationReport,
) -> RecoveryReadinessDecision:
    """Convert event-store sequence validation into a recovery gate decision."""

    if report.missing_sequences:
        return RecoveryReadinessDecision(
            recovery_allowed=False,
            reason_code="EVENT_SEQUENCE_GAP",
            missing_sequences=report.missing_sequences,
        )
    if report.duplicate_sequences:
        return RecoveryReadinessDecision(
            recovery_allowed=False,
            reason_code="EVENT_SEQUENCE_DUPLICATE",
            duplicate_sequences=report.duplicate_sequences,
        )
    return RecoveryReadinessDecision(recovery_allowed=report.valid)


def validate_runtime_recovery_gate(
    readiness: RecoveryReadinessDecision,
    *,
    observation_entered: bool = False,
    reconciliation_passed: bool = False,
) -> RuntimeRecoveryDecision:
    """Require observation and broker reconciliation before live orders resume."""

    if not readiness.recovery_allowed:
        return RuntimeRecoveryDecision(
            status=RuntimeRecoveryDecisionStatus.BLOCK,
            real_order_submission_enabled=False,
            reason_code=readiness.reason_code,
        )
    if not observation_entered:
        return RuntimeRecoveryDecision(
            status=RuntimeRecoveryDecisionStatus.ENTER_OBSERVATION,
            real_order_submission_enabled=False,
            reason_code="RECOVERY_OBSERVATION_REQUIRED",
        )
    if not reconciliation_passed:
        return RuntimeRecoveryDecision(
            status=RuntimeRecoveryDecisionStatus.ENTER_OBSERVATION,
            real_order_submission_enabled=False,
            reason_code="RECOVERY_RECONCILIATION_REQUIRED",
        )
    return RuntimeRecoveryDecision(
        status=RuntimeRecoveryDecisionStatus.ALLOW_LIVE,
        real_order_submission_enabled=True,
    )


__all__ = [
    "DurableSnapshotStore",
    "FileSnapshotStore",
    "InMemorySnapshotStore",
    "RuntimeRecoveryDecision",
    "RuntimeRecoveryDecisionStatus",
    "RecoveryReadinessDecision",
    "SnapshotFrequencyPolicy",
    "SnapshotStore",
    "StateSnapshot",
    "validate_event_sequence_for_recovery",
    "validate_runtime_recovery_gate",
]
