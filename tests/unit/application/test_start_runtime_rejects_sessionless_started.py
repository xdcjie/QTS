"""Final-state runtime start truth tests."""

from __future__ import annotations

import pytest
from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime


def test_start_runtime_rejects_sessionless_production_start() -> None:
    command = StartRuntimeCommand(
        runtime_mode="paper_simulated",
        config_ref="launch-plan://candidate/hash",
        operator_id="operator-1",
        idempotency_key="start-1",
        reason="final state start",
    )

    result = start_runtime(command)

    assert result.status == "rejected"
    assert result.session is None
    assert result.evidence["session_constructed"] is False
    assert result.evidence["reason_code"] == "RUNTIME_SESSION_BUILDER_REQUIRED"


def test_runtime_start_result_forbids_started_without_session() -> None:
    from qts.application.commands.start_runtime import RuntimeStartResult
    from qts.runtime.mode import RuntimeMode

    with pytest.raises(ValueError, match="started requires a RuntimeSession"):
        RuntimeStartResult(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            config_ref="launch-plan://candidate/hash",
            operator_id="operator-1",
            idempotency_key="start-1",
            status="started",
            order_submission_enabled=True,
            live_order_submission_enabled=False,
            reason="bad result",
        )
