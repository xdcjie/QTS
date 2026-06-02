"""Anchor tests for final-state runtime launch verification."""

from __future__ import annotations

from pathlib import Path

from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.runtime.mode import RuntimeMode

from tests.support.runtime_launch import runtime_launch_fixture


def test_runtime_start_rejects_missing_launch_plan_store(tmp_path: Path) -> None:
    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="rt-missing-store",
    )

    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="start-missing-store",
            reason="anchor",
        )
    )

    assert result.status == "rejected"
    assert result.evidence["reason_code"] == "RUNTIME_LAUNCH_PLAN_STORE_REQUIRED"
    assert result.evidence["session_constructed"] is False


def test_runtime_start_rejects_launch_plan_hash_mismatch(tmp_path: Path) -> None:
    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="rt-hash-mismatch",
    )

    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            operator_id="ops",
            idempotency_key="start-hash-mismatch",
            reason="anchor",
        ),
        launch_plan_store=launch.store,
    )

    assert result.status == "rejected"
    assert result.evidence["reason_code"] == "RUNTIME_LAUNCH_PLAN_INVALID"
    assert result.evidence["launch_plan_verified"] is False


def test_runtime_start_rejects_launch_plan_runtime_instance_mismatch(
    tmp_path: Path,
) -> None:
    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="rt-plan",
    )

    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id="rt-command",
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="start-runtime-mismatch",
            reason="anchor",
        ),
        launch_plan_store=launch.store,
    )

    assert result.status == "rejected"
    assert result.evidence["reason_code"] == "RUNTIME_LAUNCH_PLAN_COMMAND_MISMATCH"
    assert result.evidence["launch_plan_verified"] is False


def test_runtime_start_rejects_launch_plan_runtime_mode_mismatch(tmp_path: Path) -> None:
    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="rt-mode-mismatch",
    )

    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.LIVE_OBSERVATION,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="start-mode-mismatch",
            reason="anchor",
        ),
        launch_plan_store=launch.store,
    )

    assert result.status == "rejected"
    assert result.evidence["reason_code"] == "RUNTIME_LAUNCH_PLAN_COMMAND_MISMATCH"
    assert result.evidence["launch_plan_verified"] is False
