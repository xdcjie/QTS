from __future__ import annotations

import pytest


def test_start_runtime_accepts_paper_simulated_without_real_broker_credentials() -> None:
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

    assert runtime.status == "started"
    assert runtime.runtime_mode is RuntimeMode.PAPER_SIMULATED
    assert runtime.order_submission_enabled
    assert not runtime.live_order_submission_enabled


@pytest.mark.parametrize(
    "runtime_mode, order_enabled",
    [
        ("backtest", True),
        ("paper_broker", True),
        ("paper_simulated", True),
        ("live_observation", False),
    ],
)
def test_start_runtime_supports_required_modes(runtime_mode: str, order_enabled: bool) -> None:
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

    assert runtime.status == "started"
    assert runtime.order_submission_enabled is order_enabled
    assert runtime.evidence["startup_gate_checked"] is False


def test_start_runtime_live_orders_require_startup_decision() -> None:
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

    assert runtime.status == "started"
    assert not runtime.order_submission_enabled
    assert not runtime.live_order_submission_enabled
