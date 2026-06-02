"""Anchor: runtime start requires verified immutable launch-plan evidence."""

from __future__ import annotations

from pathlib import Path

from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.runtime.mode import RuntimeMode

from tests.support.runtime_launch import runtime_launch_fixture


def test_start_runtime_command_requires_launch_plan_hash() -> None:
    try:
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id="rt-hash-required",
            config_ref="launch-plan://candidate/hash",
            launch_plan_hash="",
            operator_id="ops",
            idempotency_key="start-hash-required",
            reason="hash gate",
        )
    except ValueError as exc:
        assert "launch_plan_hash must not be empty" in str(exc)
    else:
        raise AssertionError("StartRuntimeCommand accepted an empty launch_plan_hash")


def test_start_runtime_rejects_mismatched_launch_plan_hash(tmp_path: Path) -> None:
    fixture = runtime_launch_fixture(tmp_path)
    command = StartRuntimeCommand(
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id=fixture.runtime_instance_id,
        config_ref=fixture.config_ref,
        launch_plan_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        operator_id="ops",
        idempotency_key="start-mismatched-hash",
        reason="hash gate",
    )

    result = start_runtime(command, launch_plan_store=fixture.store)

    assert result.status == "rejected"
    assert result.evidence["launch_plan_verified"] is False
    assert result.evidence["session_constructed"] is False
