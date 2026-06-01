from __future__ import annotations

import pytest


def test_start_runtime_rejects_paper_simulated_without_session_builder() -> None:
    from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
    from qts.runtime.mode import RuntimeMode

    runtime = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            config_ref="configs/paper_simulated.yaml",
            operator_id="paper-local",
            idempotency_key="paper-local-1",
            reason="unit test",
        )
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

    runtime = start_runtime(
        StartRuntimeCommand(
            runtime_mode=runtime_mode,
            config_ref=f"configs/{runtime_mode}.yaml",
            operator_id="ops",
            idempotency_key=f"start-{runtime_mode}",
            reason="mode acceptance",
        )
    )

    assert runtime.status == "rejected"
    assert runtime.evidence["reason_code"] == "RUNTIME_SESSION_BUILDER_REQUIRED"
    assert runtime.evidence["session_constructed"] is False


def test_start_runtime_live_orders_require_session_builder_before_order_enablement() -> None:
    from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime

    runtime = start_runtime(
        StartRuntimeCommand(
            runtime_mode="live",
            config_ref="configs/live.yaml",
            operator_id="ops",
            idempotency_key="live-start",
            reason="live startup",
        )
    )

    assert runtime.status == "rejected"
    assert runtime.evidence["reason_code"] == "RUNTIME_SESSION_BUILDER_REQUIRED"
    assert not runtime.order_submission_enabled
    assert not runtime.live_order_submission_enabled
