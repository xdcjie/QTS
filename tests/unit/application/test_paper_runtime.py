from __future__ import annotations

from pathlib import Path

import pytest
from qts.runtime.mode import RuntimeMode

from tests.support.runtime_launch import runtime_launch_fixture


def test_start_runtime_rejects_paper_simulated_without_session_builder(tmp_path: Path) -> None:
    from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime

    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="paper-local",
    )
    runtime = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="paper-local",
            idempotency_key="paper-local-1",
            reason="unit test",
        ),
        launch_plan_store=launch.store,
    )

    assert runtime.status == "rejected"
    assert runtime.runtime_mode is RuntimeMode.PAPER_SIMULATED
    assert runtime.evidence["reason_code"] == "RUNTIME_SESSION_BUILDER_REQUIRED"
    assert runtime.evidence["session_constructed"] is False
    assert not runtime.order_submission_enabled
    assert not runtime.live_order_submission_enabled


@pytest.mark.parametrize(
    "runtime_mode",
    [
        "backtest",
        "paper_broker",
        "paper_simulated",
        "live_observation",
    ],
)
def test_start_runtime_rejects_sessionless_modes(runtime_mode: str) -> None:
    from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
    from qts.runtime.launch_plan import RuntimeLaunchPlanStore

    runtime = start_runtime(
        StartRuntimeCommand(
            runtime_mode=runtime_mode,
            runtime_instance_id=f"runtime-{runtime_mode}",
            config_ref="launch-plan://missing/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            launch_plan_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            operator_id="ops",
            idempotency_key=f"start-{runtime_mode}",
            reason="mode acceptance",
        ),
        launch_plan_store=RuntimeLaunchPlanStore(Path("/tmp/qts-missing-launch-plans")),
    )

    assert runtime.status == "rejected"
    assert runtime.evidence["reason_code"] == "RUNTIME_LAUNCH_PLAN_INVALID"
    assert runtime.evidence["session_constructed"] is False


def test_start_runtime_live_orders_require_session_builder_before_order_enablement(
    tmp_path: Path,
) -> None:
    from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime

    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.LIVE,
        runtime_instance_id="live-start",
    )
    runtime = start_runtime(
        StartRuntimeCommand(
            runtime_mode="live",
            runtime_instance_id="live-start",
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="live-start",
            reason="live startup",
        ),
        launch_plan_store=launch.store,
    )

    assert runtime.status == "rejected"
    assert runtime.evidence["reason_code"] == "RUNTIME_SESSION_BUILDER_REQUIRED"
    assert not runtime.order_submission_enabled
    assert not runtime.live_order_submission_enabled
