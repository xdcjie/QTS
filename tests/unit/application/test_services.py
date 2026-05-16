from __future__ import annotations

import ast
import json
from pathlib import Path


def test_application_services_return_stable_dtos_without_actor_internals() -> None:
    from qts.application.dto.backtest import BacktestRequestDTO
    from qts.application.services import BacktestService, HealthService

    health = HealthService().status()
    result = BacktestService().submit(
        BacktestRequestDTO(config_path="configs/backtest.gc_si.example.yaml")
    )

    assert health.status == "ok"
    assert result.status == "accepted"
    assert result.run_id.startswith("bt-")
    assert not hasattr(result, "actor_ref")
    assert not hasattr(result, "mailbox")


def test_backtest_service_persists_config_path_in_summary() -> None:
    from qts.application.dto.backtest import BacktestRequestDTO
    from qts.application.services import BacktestService

    config_path = "configs/backtest.gc_si.example.yaml"

    result = BacktestService().submit(BacktestRequestDTO(config_path=config_path))
    summary = json.loads(Path(result.summary_path).read_text(encoding="utf-8"))

    assert summary["schema_version"] == "1"
    assert summary["run_id"] == result.run_id
    assert summary["config_path"] == config_path
    assert summary["status"] == "completed"


def test_backtest_strategy_catalog_lists_valid_backtest_configs(tmp_path: Path) -> None:
    from qts.application.services.backtest_strategy_catalog import BacktestStrategyCatalog

    strategy_path = tmp_path / "strategies" / "example.yaml"
    strategy_path.parent.mkdir()
    strategy_path.write_text(
        """
strategy_id: example-momentum
class_path: examples.strategies.gc_si_momentum:GcSiMomentumStrategy
account_id: backtest-account
params:
  symbols:
    - GC
""".strip(),
        encoding="utf-8",
    )
    config_path = tmp_path / "backtest.example.yaml"
    config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: configs/data/historical.local.yaml
  catalog: research_futures
roots:
  - GC
symbols:
  - GC
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:05:00Z"
timeframe: 1m
initial_cash: "1000000"
strategy_config: {strategy_path}
risk_config:
  max_notional: "100000000"
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "backtest.invalid.yaml").write_text("mode: backtest", encoding="utf-8")

    options = BacktestStrategyCatalog(config_dir=tmp_path).list_options()

    assert len(options) == 1
    assert options[0].label == "example-momentum"
    assert options[0].config_path == str(config_path)


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


def test_operations_service_returns_timestamped_operator_status_without_actor_internals() -> None:
    from datetime import datetime

    from qts.application.services import OperationsService

    status = OperationsService().operator_status()

    fields = (
        status.runtime_state,
        status.runtime_mode,
        status.order_permission_state,
        status.broker_connection_state,
        status.market_data_permission_state,
        status.stale_subscriptions,
        status.open_orders,
        status.positions,
        status.cash_snapshot,
        status.kill_switch_state,
        status.last_reconciliation_result,
        status.unresolved_broker_callbacks,
        status.event_sink,
        status.latest_manifest,
    )

    for field in fields:
        assert isinstance(field.timestamp, datetime)
        assert field.timestamp.tzinfo is not None

    assert status.runtime_state.value == "running"
    assert status.runtime_mode.value == "paper"
    assert status.order_permission_state.value == "enabled"
    assert status.broker_connection_state.value == "disconnected"
    assert status.market_data_permission_state.value == "enabled"
    assert status.event_sink.value == {"path": None, "hash": None, "row_count": 0}
    assert status.latest_manifest.value == {"path": None, "hash": None}
    assert not hasattr(status, "actor_ref")
    assert not hasattr(status, "mailbox")


def test_operator_status_alerts_stale_drift_and_unresolved_callbacks() -> None:
    from datetime import UTC, datetime

    from qts.application.dto import OperatorDashboardStatusDTO, OperatorStatusFieldDTO
    from qts.application.services import OperationsService

    observed_at = datetime(2026, 5, 16, tzinfo=UTC)
    service = OperationsService(
        operator_status=OperatorDashboardStatusDTO(
            runtime_state=OperatorStatusFieldDTO(value="running", timestamp=observed_at),
            runtime_mode=OperatorStatusFieldDTO(value="paper", timestamp=observed_at),
            order_permission_state=OperatorStatusFieldDTO(value="enabled", timestamp=observed_at),
            broker_connection_state=OperatorStatusFieldDTO(
                value="connected", timestamp=observed_at
            ),
            market_data_permission_state=OperatorStatusFieldDTO(
                value="enabled",
                timestamp=observed_at,
            ),
            stale_subscriptions=OperatorStatusFieldDTO(
                value=({"subscription_id": "sub-1", "instrument_id": "FUT.CME.GC"},),
                timestamp=observed_at,
            ),
            open_orders=OperatorStatusFieldDTO(value=(), timestamp=observed_at),
            positions=OperatorStatusFieldDTO(value=(), timestamp=observed_at),
            cash_snapshot=OperatorStatusFieldDTO(value=(), timestamp=observed_at),
            kill_switch_state=OperatorStatusFieldDTO(
                value={"active": False, "scope": "global", "reason": ""},
                timestamp=observed_at,
            ),
            last_reconciliation_result=OperatorStatusFieldDTO(
                value={"status": "drift", "drift_count": 1},
                timestamp=observed_at,
            ),
            unresolved_broker_callbacks=OperatorStatusFieldDTO(
                value=({"callback_id": "cb-1", "kind": "orderStatus"},),
                timestamp=observed_at,
            ),
            event_sink=OperatorStatusFieldDTO(
                value={"path": "events.jsonl", "hash": "abc", "row_count": 3},
                timestamp=observed_at,
            ),
            latest_manifest=OperatorStatusFieldDTO(
                value={"path": "manifest.json", "hash": "def"},
                timestamp=observed_at,
            ),
        )
    )

    status = service.operator_status()

    assert {(alert.code, alert.timestamp) for alert in status.alerts} == {
        ("STALE_DATA", observed_at),
        ("RECONCILIATION_DRIFT", observed_at),
        ("UNRESOLVED_BROKER_CALLBACKS", observed_at),
    }
