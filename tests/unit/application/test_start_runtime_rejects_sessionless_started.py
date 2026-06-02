"""Final-state runtime start truth tests."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.application.services import RuntimeSessionBuilder
from qts.runtime.control_plane import RuntimeSessionKey, RuntimeSessionRegistry
from qts.runtime.mode import RuntimeMode
from qts.runtime.session import RuntimeSession

from tests.support.runtime_launch import runtime_launch_fixture


def test_start_runtime_rejects_sessionless_production_start(tmp_path: Path) -> None:
    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="runtime-sessionless",
    )
    command = StartRuntimeCommand(
        runtime_mode="paper_simulated",
        runtime_instance_id=launch.runtime_instance_id,
        config_ref=launch.config_ref,
        launch_plan_hash=launch.launch_plan_hash,
        operator_id="operator-1",
        idempotency_key="start-1",
        reason="final state start",
    )

    result = start_runtime(command, launch_plan_store=launch.store)

    assert result.status == "rejected"
    assert result.session is None
    assert result.evidence["session_constructed"] is False
    assert result.evidence["reason_code"] == "RUNTIME_SESSION_BUILDER_REQUIRED"


def test_start_runtime_rejects_duplicate_runtime_instance_before_building(
    tmp_path: Path,
) -> None:
    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="runtime-duplicate",
    )
    registry = RuntimeSessionRegistry()
    key = RuntimeSessionKey(runtime_instance_id=launch.runtime_instance_id)
    existing_session = cast(RuntimeSession, object())
    registry.register(key, existing_session)

    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="operator-1",
            idempotency_key="start-duplicate",
            reason="duplicate start must fail closed",
        ),
        session_builder=cast(RuntimeSessionBuilder, object()),
        session_registry=registry,
        launch_plan_store=launch.store,
    )

    assert result.status == "rejected"
    assert result.session is None
    assert result.evidence["session_constructed"] is False
    assert result.evidence["reason_code"] == "RUNTIME_SESSION_ALREADY_BOUND"
    assert registry.resolve(key) is existing_session


def test_runtime_start_result_forbids_started_without_session() -> None:
    from qts.application.commands.start_runtime import RuntimeStartResult

    with pytest.raises(ValueError, match="started requires a RuntimeSession"):
        RuntimeStartResult(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id="runtime-bad-result",
            config_ref="launch-plan://candidate/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            launch_plan_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            operator_id="operator-1",
            idempotency_key="start-1",
            status="started",
            order_submission_enabled=True,
            live_order_submission_enabled=False,
            reason="bad result",
        )
