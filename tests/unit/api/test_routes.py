from __future__ import annotations

import ast
from pathlib import Path


def _auth_headers(**extra: str) -> dict[str, str]:
    headers = {"Authorization": "Bearer dev-token"}
    headers.update(extra)
    return headers


def test_api_strategy_account_order_routes_return_public_dtos() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    assert client.get("/strategies", headers=_auth_headers()).json()[0] == {
        "strategy_id": "strategy-001",
        "status": "stopped",
    }
    assert client.post("/strategies/strategy-001/start", headers=_auth_headers()).json() == {
        "strategy_id": "strategy-001",
        "status": "running",
    }
    # No live account source is bound to the stateless API, so the account
    # query service derives an empty cash snapshot rather than a {"USD": "0"}
    # route literal.
    assert client.get("/accounts/acct-001", headers=_auth_headers()).json() == {
        "account_id": "acct-001",
        "cash": {},
    }
    # No live order source is bound, so the order query service derives a
    # not-found status rather than an "unknown" route literal.
    assert client.get("/orders/ord-001", headers=_auth_headers()).json() == {
        "order_id": "ord-001",
        "status": "not_found",
    }


def test_operational_routes_validate_non_global_scope_id() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())
    response = client.post(
        "/operations/kill-switches",
        json={"scope": "account", "reason": "halt"},
        headers=_auth_headers(**{"X-QTS-Operator": "tester"}),
    )

    assert response.status_code == 422


def test_operational_runtime_command_routes_return_command_evidence() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    reconcile = client.post(
        "/operations/runtime/reconcile",
        headers=_auth_headers(**{"Idempotency-Key": "reconcile-1", "X-QTS-Operator": "tester"}),
    )
    duplicate = client.post(
        "/operations/runtime/reconcile",
        headers=_auth_headers(**{"Idempotency-Key": "reconcile-1", "X-QTS-Operator": "tester"}),
    )
    snapshot = client.post(
        "/operations/runtime/snapshot",
        headers=_auth_headers(**{"Idempotency-Key": "snapshot-1", "X-QTS-Operator": "tester"}),
    )

    assert reconcile.status_code == 200
    assert reconcile.json()["status"] == "rejected"
    assert reconcile.json()["idempotency_key"] == "reconcile-1"
    assert reconcile.json()["reason_code"] == "RUNTIME_SESSION_NOT_BOUND"
    assert duplicate.json() == reconcile.json()
    assert snapshot.status_code == 200
    assert snapshot.json()["status"] == "rejected"
    assert snapshot.json()["reason_code"] == "RUNTIME_SESSION_NOT_BOUND"


def test_operational_runtime_lifecycle_and_observation_routes() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    from tests.support.operations import bound_operations_service

    client = TestClient(create_app(operations_service=bound_operations_service()))

    started = client.post(
        "/operations/runtime/start",
        headers=_auth_headers(**{"Idempotency-Key": "start-1", "X-QTS-Operator": "tester"}),
    )
    stopped = client.post(
        "/operations/runtime/stop",
        headers=_auth_headers(**{"Idempotency-Key": "stop-1", "X-QTS-Operator": "tester"}),
    )
    observation = client.post(
        "/operations/runtime/enter-observation",
        headers=_auth_headers(**{"Idempotency-Key": "observation-1", "X-QTS-Operator": "tester"}),
    )
    duplicate_observation = client.post(
        "/operations/runtime/enter-observation",
        headers=_auth_headers(**{"Idempotency-Key": "observation-1", "X-QTS-Operator": "tester"}),
    )
    running = client.post(
        "/operations/runtime/exit-observation",
        headers=_auth_headers(
            **{"Idempotency-Key": "exit-observation-1", "X-QTS-Operator": "tester"}
        ),
    )

    assert started.status_code == 200
    assert started.json() == {"state": "running"}
    assert stopped.status_code == 200
    assert stopped.json() == {"state": "stopped"}
    assert observation.status_code == 200
    assert observation.json() == {"state": "observation"}
    assert duplicate_observation.json() == observation.json()
    assert running.status_code == 200
    assert running.json() == {"state": "running"}


def test_operational_kill_switch_deactivate_route_is_idempotent() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    from tests.support.operations import bound_operations_service

    client = TestClient(create_app(operations_service=bound_operations_service()))

    active = client.post(
        "/operations/kill-switches",
        json={"scope": "global", "reason": "operator stop"},
        headers=_auth_headers(**{"Idempotency-Key": "kill-on-1", "X-QTS-Operator": "tester"}),
    )
    inactive = client.post(
        "/operations/kill-switches/deactivate",
        json={"scope": "global", "reason": "operator resume"},
        headers={
            "Authorization": "Bearer dev-token",
            "Idempotency-Key": "kill-off-1",
            "X-QTS-Operator": "tester",
        },
    )
    duplicate = client.post(
        "/operations/kill-switches/deactivate",
        json={"scope": "global", "reason": "different reason"},
        headers={
            "Authorization": "Bearer dev-token",
            "Idempotency-Key": "kill-off-1",
            "X-QTS-Operator": "tester",
        },
    )

    assert active.status_code == 200
    assert active.json()["active"] is True
    assert inactive.status_code == 200
    assert inactive.json()["active"] is False
    assert inactive.json()["reason"] == "operator resume"
    assert duplicate.json() == inactive.json()


def test_operational_kill_switch_deactivate_route_requires_safety_scope() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    response = client.post(
        "/operations/kill-switches/deactivate",
        json={"scope": "global", "reason": "operator resume"},
        headers={
            "Authorization": "Bearer read-token",
            "Idempotency-Key": "kill-off-denied",
            "X-QTS-Operator": "tester",
        },
    )

    assert response.status_code == 403


def test_operational_routes_scope_idempotency_by_command_kind() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    from tests.support.operations import bound_operations_service

    client = TestClient(create_app(operations_service=bound_operations_service()))

    pause = client.post(
        "/operations/runtime/pause",
        headers=_auth_headers(
            **{"Idempotency-Key": "shared-command-key", "X-QTS-Operator": "tester"}
        ),
    )
    reconcile = client.post(
        "/operations/runtime/reconcile",
        headers=_auth_headers(
            **{"Idempotency-Key": "shared-command-key", "X-QTS-Operator": "tester"}
        ),
    )

    assert pause.status_code == 200
    assert reconcile.status_code == 200
    assert reconcile.json()["idempotency_key"] == "shared-command-key"
    assert reconcile.json()["evidence"]["reconciliation"] == "completed"


def test_operator_status_route_returns_timestamped_dashboard_dto() -> None:
    from datetime import datetime

    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    response = client.get(
        "/operations/operator-status",
        headers=_auth_headers(**{"X-QTS-Operator": "tester"}),
    )

    assert response.status_code == 200
    payload = response.json()
    fields = (
        "runtime_state",
        "runtime_mode",
        "order_permission_state",
        "broker_connection_state",
        "market_data_permission_state",
        "stale_subscriptions",
        "open_orders",
        "positions",
        "cash_snapshot",
        "kill_switch_state",
        "last_reconciliation_result",
        "unresolved_broker_callbacks",
        "event_sink",
        "latest_manifest",
    )
    for field_name in fields:
        assert "value" in payload[field_name]
        datetime.fromisoformat(payload[field_name]["timestamp"])

    assert payload["runtime_state"]["value"] in {"running", "stopped", "paused", "observation"}
    assert payload["event_sink"]["value"] == {"path": None, "hash": None, "row_count": 0}
    assert payload["latest_manifest"]["value"] == {"path": None, "hash": None}
    assert payload["alerts"] == []


def test_operational_routes_do_not_import_runtime_internals() -> None:
    tree = ast.parse(Path("backend/src/qts/api/routes/operations.py").read_text(encoding="utf-8"))

    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module.startswith(("qts.runtime", "qts.risk")):
                forbidden.append(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(("qts.runtime", "qts.risk")):
                    forbidden.append(alias.name)

    assert forbidden == []
