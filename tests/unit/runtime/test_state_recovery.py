from __future__ import annotations

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
        LiveRecoveryDecisionStatus,
        validate_event_sequence_for_recovery,
        validate_live_recovery_gate,
    )

    readiness = validate_event_sequence_for_recovery(EventSequenceValidationReport(valid=True))

    initial = validate_live_recovery_gate(readiness)
    reconciled_without_observation = validate_live_recovery_gate(
        readiness,
        reconciliation_passed=True,
    )
    ready = validate_live_recovery_gate(
        readiness,
        observation_entered=True,
        reconciliation_passed=True,
    )

    assert initial.status is LiveRecoveryDecisionStatus.ENTER_OBSERVATION
    assert initial.real_order_submission_enabled is False
    assert reconciled_without_observation.status is LiveRecoveryDecisionStatus.ENTER_OBSERVATION
    assert reconciled_without_observation.real_order_submission_enabled is False
    assert ready.status is LiveRecoveryDecisionStatus.ALLOW_LIVE
    assert ready.real_order_submission_enabled is True


def test_live_recovery_blocks_when_event_sequence_is_invalid() -> None:
    from qts.runtime.event_store import EventSequenceValidationReport
    from qts.runtime.state_recovery import (
        LiveRecoveryDecisionStatus,
        validate_event_sequence_for_recovery,
        validate_live_recovery_gate,
    )

    readiness = validate_event_sequence_for_recovery(
        EventSequenceValidationReport(valid=False, missing_sequences=(2,))
    )

    decision = validate_live_recovery_gate(readiness)

    assert decision.status is LiveRecoveryDecisionStatus.BLOCK
    assert decision.real_order_submission_enabled is False
    assert decision.reason_code == "EVENT_SEQUENCE_GAP"
