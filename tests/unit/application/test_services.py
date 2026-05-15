from __future__ import annotations

import ast
from pathlib import Path


def test_application_services_return_stable_dtos_without_actor_internals() -> None:
    from qts.application.dto.backtest import BacktestRequestDTO
    from qts.application.services import BacktestService, HealthService

    health = HealthService().status()
    result = BacktestService().submit(BacktestRequestDTO(strategy_name="smoke"))

    assert health.status == "ok"
    assert result.status == "accepted"
    assert result.run_id.startswith("bt-")
    assert not hasattr(result, "actor_ref")
    assert not hasattr(result, "mailbox")


def test_operations_service_keeps_private_mapping_logic_inside_the_service() -> None:
    tree = ast.parse(
        Path("backend/src/qts/application/services/operations.py").read_text(encoding="utf-8")
    )

    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_scope_from_command" not in private_functions


def test_operations_service_routes_runtime_controls_through_idempotent_commands() -> None:
    from qts.application.services import OperationsService

    service = OperationsService()

    paused = service.pause_runtime(operator_id="ops-a", idempotency_key="pause-key")
    running = service.resume_runtime(operator_id="ops-a", idempotency_key="resume-key")
    duplicate_pause = service.pause_runtime(operator_id="ops-a", idempotency_key="pause-key")

    assert paused.state == "paused"
    assert running.state == "running"
    assert duplicate_pause.state == "paused"


def test_operations_service_routes_kill_switch_through_idempotent_commands() -> None:
    from qts.application.dto import KillSwitchCommandDTO
    from qts.application.services import OperationsService

    service = OperationsService()

    first = service.activate_kill_switch(
        KillSwitchCommandDTO(scope="global", reason="operator stop"),
        operator_id="ops-a",
        idempotency_key="kill-switch-key",
    )
    duplicate = service.activate_kill_switch(
        KillSwitchCommandDTO(scope="global", reason="different reason"),
        operator_id="ops-a",
        idempotency_key="kill-switch-key",
    )

    assert first.active is True
    assert first.reason == "operator stop"
    assert duplicate == first


def test_operations_service_exposes_reconcile_and_snapshot_command_results() -> None:
    from qts.application.services import OperationsService

    service = OperationsService()

    reconcile = service.reconcile_runtime(
        operator_id="ops-a",
        idempotency_key="reconcile-key",
    )
    duplicate_reconcile = service.reconcile_runtime(
        operator_id="ops-a",
        idempotency_key="reconcile-key",
    )
    snapshot = service.snapshot_runtime(
        operator_id="ops-a",
        idempotency_key="snapshot-key",
    )

    assert reconcile.status == "completed"
    assert reconcile.evidence["reconciliation"] == "requested"
    assert duplicate_reconcile == reconcile
    assert snapshot.status == "completed"
    assert snapshot.evidence["snapshot"] == "requested"


def test_operations_service_routes_lifecycle_and_observation_commands() -> None:
    from qts.application.services import OperationsService

    service = OperationsService()

    started = service.start_runtime(operator_id="ops-a", idempotency_key="start-key")
    stopped = service.stop_runtime(operator_id="ops-a", idempotency_key="stop-key")
    observation = service.enter_observation(
        operator_id="ops-a",
        idempotency_key="observation-key",
    )
    running = service.exit_observation(
        operator_id="ops-a",
        idempotency_key="exit-observation-key",
    )
    duplicate_observation = service.enter_observation(
        operator_id="ops-a",
        idempotency_key="observation-key",
    )

    assert started.state == "running"
    assert stopped.state == "stopped"
    assert observation.state == "observation"
    assert running.state == "running"
    assert duplicate_observation == observation


def test_operations_service_deactivates_kill_switch_through_idempotent_command() -> None:
    from qts.application.dto import KillSwitchCommandDTO
    from qts.application.services import OperationsService

    service = OperationsService()
    command = KillSwitchCommandDTO(scope="global", reason="operator stop")

    active = service.activate_kill_switch(
        command,
        operator_id="ops-a",
        idempotency_key="kill-switch-on",
    )
    inactive = service.deactivate_kill_switch(
        KillSwitchCommandDTO(scope="global", reason="operator resume"),
        operator_id="ops-a",
        idempotency_key="kill-switch-off",
        authorization_scope="runtime:safety:write",
    )
    duplicate_inactive = service.deactivate_kill_switch(
        KillSwitchCommandDTO(scope="global", reason="different reason"),
        operator_id="ops-a",
        idempotency_key="kill-switch-off",
        authorization_scope="runtime:safety:write",
    )

    assert active.active is True
    assert inactive.active is False
    assert inactive.reason == "operator resume"
    assert duplicate_inactive == inactive


def test_operations_service_rejects_kill_switch_deactivate_without_safety_scope() -> None:
    from qts.application.dto import KillSwitchCommandDTO
    from qts.application.services import OperationsService

    service = OperationsService()
    service.activate_kill_switch(
        KillSwitchCommandDTO(scope="global", reason="operator stop"),
        operator_id="ops-a",
        idempotency_key="kill-switch-on",
    )

    result = service.deactivate_kill_switch_result(
        KillSwitchCommandDTO(scope="global", reason="operator resume"),
        operator_id="ops-a",
        idempotency_key="kill-switch-off",
    )

    assert result.status == "rejected"
    assert result.reason_code == "COMMAND_PERMISSION_DENIED"


def test_operations_service_scopes_runtime_command_idempotency_by_operator() -> None:
    from qts.application.services import OperationsService

    service = OperationsService()

    first = service.reconcile_runtime(operator_id="ops-a", idempotency_key="shared-key")
    second = service.reconcile_runtime(operator_id="ops-b", idempotency_key="shared-key")

    assert first.command_id != second.command_id
    assert first.evidence["operator_id"] == "ops-a"
    assert second.evidence["operator_id"] == "ops-b"
