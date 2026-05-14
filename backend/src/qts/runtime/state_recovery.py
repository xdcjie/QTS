"""State snapshot and recovery interfaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from qts.core.hashing import stable_json_default
from qts.runtime.event_store import EventSequenceValidationReport


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    """Serialized actor state snapshot envelope."""

    actor_id: str
    state_version: int
    payload: Any
    last_sequence: int = 0

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.actor_id.strip():
            raise ValueError("actor_id must not be empty")
        if self.state_version < 0:
            raise ValueError("state_version must be non-negative")
        if self.last_sequence < 0:
            raise ValueError("last_sequence must be non-negative")


class SnapshotStore(Protocol):
    """Durable snapshot store contract for actor recovery."""

    def save(self, snapshot: StateSnapshot) -> None:
        """Persist an actor state snapshot."""
        ...

    def load(self, actor_id: str) -> StateSnapshot | None:
        """Load the latest snapshot for an actor."""
        ...


class LiveRecoveryDecisionStatus(StrEnum):
    """Safety decision for live runtime recovery."""

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
class LiveRecoveryDecision:
    """Recovery safety decision before live order submission resumes."""

    status: LiveRecoveryDecisionStatus
    real_order_submission_enabled: bool
    reason_code: str | None = None

    def __post_init__(self) -> None:
        if self.status is LiveRecoveryDecisionStatus.ALLOW_LIVE:
            if not self.real_order_submission_enabled:
                raise ValueError("ALLOW_LIVE requires real_order_submission_enabled")
            if self.reason_code is not None:
                raise ValueError("ALLOW_LIVE decision must not have a reason_code")
        elif self.real_order_submission_enabled:
            raise ValueError("blocked or observation recovery cannot enable real orders")


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
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    self._snapshot_to_json(snapshot),
                    default=stable_json_default,
                    sort_keys=True,
                )
            )
            handle.write("\n")

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
                snapshot = self._snapshot_from_json(json.loads(line))
                if snapshot.actor_id == actor_id:
                    latest = snapshot
        return latest

    @staticmethod
    def _snapshot_to_json(snapshot: StateSnapshot) -> dict[str, Any]:
        return {
            "actor_id": snapshot.actor_id,
            "state_version": snapshot.state_version,
            "last_sequence": snapshot.last_sequence,
            "payload": snapshot.payload,
        }

    @staticmethod
    def _snapshot_from_json(payload: dict[str, Any]) -> StateSnapshot:
        return StateSnapshot(
            actor_id=str(payload["actor_id"]),
            state_version=int(payload["state_version"]),
            last_sequence=int(payload.get("last_sequence", 0)),
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


def validate_live_recovery_gate(
    readiness: RecoveryReadinessDecision,
    *,
    observation_entered: bool = False,
    reconciliation_passed: bool = False,
) -> LiveRecoveryDecision:
    """Require observation and broker reconciliation before live orders resume."""

    if not readiness.recovery_allowed:
        return LiveRecoveryDecision(
            status=LiveRecoveryDecisionStatus.BLOCK,
            real_order_submission_enabled=False,
            reason_code=readiness.reason_code,
        )
    if not observation_entered:
        return LiveRecoveryDecision(
            status=LiveRecoveryDecisionStatus.ENTER_OBSERVATION,
            real_order_submission_enabled=False,
            reason_code="RECOVERY_OBSERVATION_REQUIRED",
        )
    if not reconciliation_passed:
        return LiveRecoveryDecision(
            status=LiveRecoveryDecisionStatus.ENTER_OBSERVATION,
            real_order_submission_enabled=False,
            reason_code="RECOVERY_RECONCILIATION_REQUIRED",
        )
    return LiveRecoveryDecision(
        status=LiveRecoveryDecisionStatus.ALLOW_LIVE,
        real_order_submission_enabled=True,
    )


__all__ = [
    "DurableSnapshotStore",
    "FileSnapshotStore",
    "InMemorySnapshotStore",
    "LiveRecoveryDecision",
    "LiveRecoveryDecisionStatus",
    "RecoveryReadinessDecision",
    "SnapshotFrequencyPolicy",
    "SnapshotStore",
    "StateSnapshot",
    "validate_event_sequence_for_recovery",
    "validate_live_recovery_gate",
]
