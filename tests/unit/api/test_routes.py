from __future__ import annotations

import ast
from pathlib import Path


def test_api_strategy_account_order_routes_return_public_dtos() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    assert client.get("/strategies").json()[0] == {
        "strategy_id": "strategy-001",
        "status": "stopped",
    }
    assert client.post("/strategies/strategy-001/start").json() == {
        "strategy_id": "strategy-001",
        "status": "running",
    }
    assert client.get("/accounts/acct-001").json() == {
        "account_id": "acct-001",
        "cash": {"USD": "0"},
    }
    assert client.get("/orders/ord-001").json() == {
        "order_id": "ord-001",
        "status": "unknown",
    }


def test_operational_routes_validate_non_global_scope_id() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())
    response = client.post(
        "/operations/kill-switches",
        json={"scope": "account", "reason": "halt"},
        headers={"X-QTS-Operator": "tester"},
    )

    assert response.status_code == 422


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
