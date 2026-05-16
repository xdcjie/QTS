"""Runtime durability recovery drills."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from qts.runtime.event_store import EventSequenceValidationReport, StoredEvent
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.state_recovery import (
    RecoveryReadinessDecision,
    RuntimeRecoveryDecision,
    SnapshotStore,
    StateSnapshot,
    validate_event_sequence_for_recovery,
    validate_runtime_recovery_gate,
)


class DurableEventStore(Protocol):
    """Event-store capabilities required by durability recovery."""

    def append(self, event: StoredEvent) -> int:
        """Append an event to the store and return its durable sequence."""
        ...

    def replay_after(self, sequence: int) -> tuple[StoredEvent, ...]:
        """Replay events persisted after a 1-indexed sequence number."""
        ...

    def validate_sequence(self) -> EventSequenceValidationReport:
        """Return event sequence continuity evidence."""
        ...


class SnapshotSchemaMismatch(RuntimeError):
    """Raised when a recovered snapshot uses an unsupported schema version."""


class RuntimeDurabilityStateMismatch(RuntimeError):
    """Raised when recovered state does not match crash-time state."""


@dataclass(frozen=True, slots=True)
class RuntimeDurabilityDrillConfig:
    """Configuration for a runtime durability recovery drill."""

    event_store_factory: Callable[[], DurableEventStore]
    snapshot_store_factory: Callable[[], SnapshotStore]
    actor_ids: tuple[str, ...]
    expected_snapshot_schema_version: str = "1"

    def __post_init__(self) -> None:
        if not self.actor_ids:
            raise ValueError("actor_ids must not be empty")
        if any(not actor_id.strip() for actor_id in self.actor_ids):
            raise ValueError("actor_ids must not contain empty values")
        if not self.expected_snapshot_schema_version.strip():
            raise ValueError("expected_snapshot_schema_version must not be empty")


@dataclass(frozen=True, slots=True)
class RuntimeDurabilityDrillResult:
    """Evidence produced by a runtime durability recovery drill."""

    recovered_state: dict[str, Any]
    latest_snapshot_sequence: int
    replayed_event_count: int
    recovery_readiness_decision: RecoveryReadinessDecision
    runtime_recovery_decision: RuntimeRecoveryDecision


class RuntimeDurabilityDrill:
    """Write, restart, recover, and gate runtime state from durable stores."""

    def __init__(self, config: RuntimeDurabilityDrillConfig) -> None:
        self._config = config

    def run(
        self,
        *,
        events: Iterable[RuntimeEvent],
        snapshots: Iterable[StateSnapshot],
        expected_state: Mapping[str, Any],
        observation_entered: bool = False,
        reconciliation_passed: bool = False,
    ) -> RuntimeDurabilityDrillResult:
        """Persist drill inputs, simulate restart, and recover from durable stores."""

        event_store = self._config.event_store_factory()
        for event in events:
            event_store.append(event)
        snapshot_store = self._config.snapshot_store_factory()
        for snapshot in snapshots:
            snapshot_store.save(snapshot)
        return self.recover(
            expected_state=expected_state,
            observation_entered=observation_entered,
            reconciliation_passed=reconciliation_passed,
        )

    def recover(
        self,
        *,
        expected_state: Mapping[str, Any],
        observation_entered: bool = False,
        reconciliation_passed: bool = False,
    ) -> RuntimeDurabilityDrillResult:
        """Recover state from latest snapshots and post-snapshot events."""

        event_store = self._config.event_store_factory()
        recovery_decision = validate_event_sequence_for_recovery(event_store.validate_sequence())
        if not recovery_decision.recovery_allowed:
            runtime_decision = validate_runtime_recovery_gate(
                recovery_decision,
                observation_entered=observation_entered,
                reconciliation_passed=reconciliation_passed,
            )
            return RuntimeDurabilityDrillResult(
                recovered_state={},
                latest_snapshot_sequence=0,
                replayed_event_count=0,
                recovery_readiness_decision=recovery_decision,
                runtime_recovery_decision=runtime_decision,
            )

        recovered_state, latest_snapshot_sequence = self._load_snapshot_state()
        replayed_events = event_store.replay_after(latest_snapshot_sequence)
        for event in replayed_events:
            self._apply_replayed_event(recovered_state, event)
        self._require_expected_state(recovered_state, expected_state)
        runtime_decision = validate_runtime_recovery_gate(
            recovery_decision,
            observation_entered=observation_entered,
            reconciliation_passed=reconciliation_passed,
        )
        return RuntimeDurabilityDrillResult(
            recovered_state=recovered_state,
            latest_snapshot_sequence=latest_snapshot_sequence,
            replayed_event_count=len(replayed_events),
            recovery_readiness_decision=recovery_decision,
            runtime_recovery_decision=runtime_decision,
        )

    def _load_snapshot_state(self) -> tuple[dict[str, Any], int]:
        snapshot_store = self._config.snapshot_store_factory()
        recovered_state: dict[str, Any] = {}
        latest_snapshot_sequence = 0
        for actor_id in self._config.actor_ids:
            snapshot = snapshot_store.load(actor_id)
            if snapshot is None:
                continue
            self._require_supported_schema(snapshot)
            recovered_state[actor_id] = snapshot.payload
            latest_snapshot_sequence = max(latest_snapshot_sequence, snapshot.last_sequence)
        return recovered_state, latest_snapshot_sequence

    def _require_supported_schema(self, snapshot: StateSnapshot) -> None:
        if snapshot.schema_version != self._config.expected_snapshot_schema_version:
            raise SnapshotSchemaMismatch(
                f"{snapshot.actor_id} snapshot schema version "
                f"{snapshot.schema_version!r} does not match expected "
                f"{self._config.expected_snapshot_schema_version!r}"
            )

    def _apply_replayed_event(self, recovered_state: dict[str, Any], event: StoredEvent) -> None:
        if not isinstance(event, RuntimeEvent):
            return
        state_snapshots = event.payload.get("state_snapshots")
        if not isinstance(state_snapshots, dict):
            return
        for actor_id, payload in state_snapshots.items():
            if actor_id in self._config.actor_ids:
                recovered_state[str(actor_id)] = payload

    def _require_expected_state(
        self,
        recovered_state: Mapping[str, Any],
        expected_state: Mapping[str, Any],
    ) -> None:
        for actor_id in self._config.actor_ids:
            if recovered_state.get(actor_id) != expected_state.get(actor_id):
                raise RuntimeDurabilityStateMismatch(
                    f"{actor_id} recovered state does not match pre-crash state"
                )


__all__ = [
    "DurableEventStore",
    "RuntimeDurabilityDrill",
    "RuntimeDurabilityDrillConfig",
    "RuntimeDurabilityDrillResult",
    "RuntimeDurabilityStateMismatch",
    "SnapshotSchemaMismatch",
]
