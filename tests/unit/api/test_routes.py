from __future__ import annotations


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
