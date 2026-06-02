"""Operator commands target sessions registered by start_runtime."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.application.services import OperationsService, RuntimeSessionBuilder, RuntimeStartConfig
from qts.core.ids import AccountId
from qts.runtime.control_plane import RuntimeCommandExecutor, RuntimeSessionRegistry
from qts.runtime.mode import RuntimeMode
from qts.runtime.state import RuntimeSessionState

from tests.integration.test_start_runtime_builds_session import (
    _BuyOnceStrategy,
    _instrument_registry,
)
from tests.support.runtime_launch import runtime_launch_fixture


def test_operator_command_targets_registered_runtime_session(tmp_path: Path) -> None:
    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="paper-ops-runtime-1",
    )
    registry = RuntimeSessionRegistry()
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            account_id=AccountId("acct-paper-ops"),
            initial_cash={"USD": Decimal("100000")},
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
    )

    start = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="start-paper-ops",
            reason="operator command target test",
        ),
        session_builder=builder,
        session_registry=registry,
        launch_plan_store=launch.store,
    )
    assert start.session is not None

    operations = OperationsService(command_executor=RuntimeCommandExecutor(registry))
    paused = operations.pause_runtime_result(
        runtime_instance_id=launch.runtime_instance_id,
        operator_id="ops",
        idempotency_key="pause-paper-ops",
    )

    assert paused.status == "completed"
    assert paused.evidence["runtime_instance_id"] == launch.runtime_instance_id
    assert paused.evidence["state"] == "paused"
    assert start.session.state is RuntimeSessionState.PAUSED
