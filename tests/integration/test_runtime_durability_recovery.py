from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest
from qts.core.ids import EventId, RuntimeRunId
from qts.runtime.durability import (
    RuntimeDurabilityDrill,
    RuntimeDurabilityDrillConfig,
    RuntimeDurabilityStateMismatch,
    SnapshotSchemaMismatch,
)
from qts.runtime.event_store import FileEventStore
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.state_recovery import (
    FileSnapshotStore,
    RuntimeRecoveryDecisionStatus,
    StateSnapshot,
)


def test_durability_drill_recovers_snapshot_and_replays_post_snapshot_events(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "events.jsonl"
    snapshots_path = tmp_path / "snapshots.jsonl"
    run_id = RuntimeRunId("run-durability-001")
    events = (
        _runtime_event(run_id, 1, {"account": {"cash": {"USD": "10000"}}}),
        _runtime_event(
            run_id,
            2,
            {
                "account": {"cash": {"USD": "10000"}},
                "order_manager": {"orders": {"ord-001": "submitted"}},
                "broker_order_map": {"ord-001": "broker-001"},
            },
        ),
        _runtime_event(
            run_id,
            3,
            {
                "account": {"cash": {"USD": "98500"}, "positions": {"AAPL": "10"}},
                "order_manager": {"orders": {"ord-001": "filled"}},
            },
        ),
        _runtime_event(run_id, 4, {"broker_order_map": {"ord-001": "broker-001"}}),
    )
    snapshots = (
        StateSnapshot(
            actor_id="account",
            state_version=1,
            last_sequence=2,
            payload={"cash": {"USD": "10000"}},
        ),
        StateSnapshot(
            actor_id="order_manager",
            state_version=1,
            last_sequence=2,
            payload={"orders": {"ord-001": "submitted"}},
        ),
        StateSnapshot(
            actor_id="broker_order_map",
            state_version=1,
            last_sequence=2,
            payload={"ord-001": "broker-001"},
        ),
    )
    pre_crash_state = {
        "account": {"cash": {"USD": "98500"}, "positions": {"AAPL": "10"}},
        "order_manager": {"orders": {"ord-001": "filled"}},
        "broker_order_map": {"ord-001": "broker-001"},
    }

    result = RuntimeDurabilityDrill(
        RuntimeDurabilityDrillConfig(
            event_store_factory=lambda: FileEventStore(events_path),
            snapshot_store_factory=lambda: FileSnapshotStore(snapshots_path),
            actor_ids=("account", "order_manager", "broker_order_map"),
        ),
    ).run(
        events=events,
        snapshots=snapshots,
        expected_state=pre_crash_state,
        observation_entered=True,
        reconciliation_passed=True,
    )

    assert result.recovered_state == pre_crash_state
    assert result.replayed_event_count == 2
    assert result.latest_snapshot_sequence == 2
    assert result.recovery_readiness_decision.recovery_allowed is True
    assert result.runtime_recovery_decision.status is RuntimeRecoveryDecisionStatus.ALLOW_LIVE
    assert result.runtime_recovery_decision.real_order_submission_enabled is True


def test_durability_drill_blocks_event_sequence_gap(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    snapshots_path = tmp_path / "snapshots.jsonl"
    events_path.write_text(
        "\n".join(
            (
                '{"runtime_event": {"account_id": null, "causation_id": null, '
                '"correlation_id": null, "event_id": "evt-001", '
                '"execution_environment": null, "instrument_id": null, '
                '"kind": "runtime.state_snapshot", "mode": "live", '
                '"parent_event_id": null, "payload": {"state_snapshots": {}}, '
                '"payload_schema_version": "1", "run_id": "run-gap", '
                '"runtime_mode": "live", "sequence_no": 1, "strategy_id": null, '
                '"ts_event": "2026-01-02T14:30:00+00:00", '
                '"ts_ingest": "2026-01-02T14:30:00+00:00"}, "sequence": 1}',
                '{"runtime_event": {"account_id": null, "causation_id": null, '
                '"correlation_id": null, "event_id": "evt-003", '
                '"execution_environment": null, "instrument_id": null, '
                '"kind": "runtime.state_snapshot", "mode": "live", '
                '"parent_event_id": null, "payload": {"state_snapshots": {}}, '
                '"payload_schema_version": "1", "run_id": "run-gap", '
                '"runtime_mode": "live", "sequence_no": 3, "strategy_id": null, '
                '"ts_event": "2026-01-02T14:30:00+00:00", '
                '"ts_ingest": "2026-01-02T14:30:00+00:00"}, "sequence": 3}',
            )
        ),
        encoding="utf-8",
    )

    result = RuntimeDurabilityDrill(
        RuntimeDurabilityDrillConfig(
            event_store_factory=lambda: FileEventStore(events_path),
            snapshot_store_factory=lambda: FileSnapshotStore(snapshots_path),
            actor_ids=("account",),
        ),
    ).recover(
        expected_state={"account": {}},
        observation_entered=True,
        reconciliation_passed=True,
    )

    assert result.recovery_readiness_decision.recovery_allowed is False
    assert result.recovery_readiness_decision.reason_code == "EVENT_SEQUENCE_GAP"
    assert result.runtime_recovery_decision.status is RuntimeRecoveryDecisionStatus.BLOCK
    assert result.runtime_recovery_decision.real_order_submission_enabled is False


def test_durability_drill_blocks_snapshot_schema_version_mismatch(tmp_path: Path) -> None:
    snapshots_path = tmp_path / "snapshots.jsonl"
    store = FileSnapshotStore(snapshots_path)
    store.save(
        StateSnapshot(
            actor_id="account",
            state_version=1,
            schema_version="unsupported-v0",
            payload={},
        ),
    )

    with pytest.raises(SnapshotSchemaMismatch, match="account"):
        RuntimeDurabilityDrill(
            RuntimeDurabilityDrillConfig(
                event_store_factory=lambda: FileEventStore(tmp_path / "events.jsonl"),
                snapshot_store_factory=lambda: FileSnapshotStore(snapshots_path),
                actor_ids=("account",),
            ),
        ).recover(expected_state={"account": {}})


def test_durability_drill_requires_reconciliation_before_order_submission(
    tmp_path: Path,
) -> None:
    state = {"account": {"cash": {"USD": "10000"}}}
    result = RuntimeDurabilityDrill(
        RuntimeDurabilityDrillConfig(
            event_store_factory=lambda: FileEventStore(tmp_path / "events.jsonl"),
            snapshot_store_factory=lambda: FileSnapshotStore(tmp_path / "snapshots.jsonl"),
            actor_ids=("account",),
        ),
    ).run(
        events=(_runtime_event(RuntimeRunId("run-live-gate"), 1, state),),
        snapshots=(
            StateSnapshot(
                actor_id="account",
                state_version=1,
                last_sequence=1,
                payload=state["account"],
            ),
        ),
        expected_state=state,
        observation_entered=True,
        reconciliation_passed=False,
    )

    assert (
        result.runtime_recovery_decision.status is RuntimeRecoveryDecisionStatus.ENTER_OBSERVATION
    )
    assert result.runtime_recovery_decision.reason_code == "RECOVERY_RECONCILIATION_REQUIRED"
    assert result.runtime_recovery_decision.real_order_submission_enabled is False


def test_durability_drill_detects_recovered_state_mismatch(tmp_path: Path) -> None:
    state = {"account": {"cash": {"USD": "10000"}}}

    with pytest.raises(RuntimeDurabilityStateMismatch, match="account"):
        RuntimeDurabilityDrill(
            RuntimeDurabilityDrillConfig(
                event_store_factory=lambda: FileEventStore(tmp_path / "events.jsonl"),
                snapshot_store_factory=lambda: FileSnapshotStore(tmp_path / "snapshots.jsonl"),
                actor_ids=("account",),
            ),
        ).run(
            events=(_runtime_event(RuntimeRunId("run-mismatch"), 1, state),),
            snapshots=(
                StateSnapshot(
                    actor_id="account",
                    state_version=1,
                    last_sequence=1,
                    payload=state["account"],
                ),
            ),
            expected_state={"account": {"cash": {"USD": "9999"}}},
        )


def _runtime_event(
    run_id: RuntimeRunId,
    sequence_no: int,
    state_snapshots: Mapping[str, object],
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=EventId(f"evt-{sequence_no:03d}"),
        kind="runtime.state_snapshot",
        payload={"state_snapshots": state_snapshots},
        run_id=run_id,
        mode="live",
        sequence_no=sequence_no,
    )
