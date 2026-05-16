from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path


def test_in_memory_snapshot_store_saves_and_restores_actor_state() -> None:
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.state_recovery import InMemorySnapshotStore, StateSnapshot

    actor = AccountActor(initial_cash={"USD": Decimal("10000")})
    snapshot = StateSnapshot(
        actor_id="account:acct-001",
        state_version=1,
        payload=actor.snapshot(),
    )
    store = InMemorySnapshotStore()

    store.save(snapshot)

    assert store.load("account:acct-001") == snapshot


def test_file_snapshot_store_persists_latest_actor_snapshot(tmp_path: Path) -> None:
    from qts.runtime.state_recovery import FileSnapshotStore, StateSnapshot

    path = tmp_path / "snapshots.jsonl"
    first = StateSnapshot(
        actor_id="account:acct-001",
        state_version=1,
        last_sequence=2,
        payload={"cash": {"USD": "10000"}, "positions": []},
    )
    latest = StateSnapshot(
        actor_id="account:acct-001",
        state_version=2,
        last_sequence=5,
        payload={"cash": {"USD": "9000"}, "positions": []},
    )

    store = FileSnapshotStore(path)
    store.save(first)
    store.save(latest)

    restored = FileSnapshotStore(path)
    restored_snapshot = restored.load("account:acct-001")
    assert restored_snapshot == latest
    assert restored_snapshot is not None
    assert restored_snapshot.last_sequence == 5
    assert restored.load("account:missing") is None


def test_state_snapshot_carries_recovery_manifest_metadata() -> None:
    from qts.core.ids import RuntimeRunId
    from qts.runtime.state_recovery import StateSnapshot

    snapshot = StateSnapshot(
        snapshot_id="snapshot-001",
        actor_id="account:acct-001",
        run_id=RuntimeRunId("run-001"),
        schema_version="2",
        created_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        state_version=3,
        last_sequence=8,
        topology_hash="sha256:topology",
        config_hash="sha256:config",
        payload={"cash": {"USD": "9000"}},
    )

    assert snapshot.snapshot_id == "snapshot-001"
    assert snapshot.run_id == RuntimeRunId("run-001")
    assert snapshot.schema_version == "2"
    assert snapshot.topology_hash == "sha256:topology"
    assert snapshot.config_hash == "sha256:config"


def test_file_snapshot_store_ignores_trailing_partial_snapshot(tmp_path: Path) -> None:
    from qts.runtime.state_recovery import FileSnapshotStore, StateSnapshot

    path = tmp_path / "snapshots.jsonl"
    latest = StateSnapshot(
        snapshot_id="snapshot-001",
        actor_id="account:acct-001",
        state_version=2,
        last_sequence=5,
        payload={"cash": {"USD": "9000"}},
    )
    store = FileSnapshotStore(path)
    store.save(latest)
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"snapshot_id":"partial"')

    assert FileSnapshotStore(path).load("account:acct-001") == latest


def test_file_snapshot_store_writes_complete_json_records(tmp_path: Path) -> None:
    from qts.runtime.state_recovery import FileSnapshotStore, StateSnapshot

    path = tmp_path / "snapshots.jsonl"
    snapshot = StateSnapshot(
        snapshot_id="snapshot-001",
        actor_id="account:acct-001",
        state_version=2,
        last_sequence=5,
        payload={"cash": {"USD": "9000"}},
    )

    FileSnapshotStore(path).save(snapshot)

    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert records[-1]["snapshot_id"] == "snapshot-001"
    assert records[-1]["schema_version"] == "1"
    assert records[-1]["last_event_sequence_no"] == 5


def test_snapshot_store_rejects_empty_actor_lookup(tmp_path: Path) -> None:
    import pytest
    from qts.runtime.state_recovery import FileSnapshotStore

    store = FileSnapshotStore(tmp_path / "snapshots.jsonl")

    with pytest.raises(ValueError, match="actor_id"):
        store.load(" ")


def test_recovery_gate_blocks_invalid_event_sequence() -> None:
    from qts.runtime.event_store import EventSequenceValidationReport
    from qts.runtime.state_recovery import validate_event_sequence_for_recovery

    missing = validate_event_sequence_for_recovery(
        EventSequenceValidationReport(valid=False, missing_sequences=(2,))
    )
    duplicate = validate_event_sequence_for_recovery(
        EventSequenceValidationReport(valid=False, duplicate_sequences=(3,))
    )
    clean = validate_event_sequence_for_recovery(EventSequenceValidationReport(valid=True))

    assert missing.recovery_allowed is False
    assert missing.reason_code == "EVENT_SEQUENCE_GAP"
    assert duplicate.recovery_allowed is False
    assert duplicate.reason_code == "EVENT_SEQUENCE_DUPLICATE"
    assert clean.recovery_allowed is True
    assert clean.reason_code is None


def test_live_recovery_enters_observation_before_live_orders() -> None:
    from qts.runtime.event_store import EventSequenceValidationReport
    from qts.runtime.state_recovery import (
        RuntimeRecoveryDecisionStatus,
        validate_event_sequence_for_recovery,
        validate_runtime_recovery_gate,
    )

    readiness = validate_event_sequence_for_recovery(EventSequenceValidationReport(valid=True))

    initial = validate_runtime_recovery_gate(readiness)
    reconciled_without_observation = validate_runtime_recovery_gate(
        readiness,
        reconciliation_passed=True,
    )
    ready = validate_runtime_recovery_gate(
        readiness,
        observation_entered=True,
        reconciliation_passed=True,
    )

    assert initial.status is RuntimeRecoveryDecisionStatus.ENTER_OBSERVATION
    assert initial.real_order_submission_enabled is False
    assert reconciled_without_observation.status is RuntimeRecoveryDecisionStatus.ENTER_OBSERVATION
    assert reconciled_without_observation.real_order_submission_enabled is False
    assert ready.status is RuntimeRecoveryDecisionStatus.ALLOW_LIVE
    assert ready.real_order_submission_enabled is True


def test_live_recovery_blocks_when_event_sequence_is_invalid() -> None:
    from qts.runtime.event_store import EventSequenceValidationReport
    from qts.runtime.state_recovery import (
        RuntimeRecoveryDecisionStatus,
        validate_event_sequence_for_recovery,
        validate_runtime_recovery_gate,
    )

    readiness = validate_event_sequence_for_recovery(
        EventSequenceValidationReport(valid=False, missing_sequences=(2,))
    )

    decision = validate_runtime_recovery_gate(readiness)

    assert decision.status is RuntimeRecoveryDecisionStatus.BLOCK
    assert decision.real_order_submission_enabled is False
    assert decision.reason_code == "EVENT_SEQUENCE_GAP"


def test_live_recovery_decision_writes_manifest_payload_and_runtime_event() -> None:
    from qts.runtime.state_recovery import (
        RuntimeRecoveryDecision,
        RuntimeRecoveryDecisionStatus,
    )

    decision = RuntimeRecoveryDecision(
        status=RuntimeRecoveryDecisionStatus.ENTER_OBSERVATION,
        real_order_submission_enabled=False,
        reason_code="RECOVERY_RECONCILIATION_REQUIRED",
    )

    manifest = decision.to_manifest_payload()
    event = decision.to_runtime_event()

    assert manifest == {
        "status": "enter_observation",
        "real_order_submission_enabled": False,
        "reason_code": "RECOVERY_RECONCILIATION_REQUIRED",
    }
    assert event.kind == "runtime.recovery_decision"
    assert event.payload == manifest
