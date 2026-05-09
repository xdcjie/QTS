from __future__ import annotations


def test_api_can_submit_backtest_request() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    response = client.post("/backtests", json={"strategy_name": "smoke"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"].startswith("bt-")
    assert payload["status"] == "accepted"
    assert payload["strategy_name"] == "smoke"
    assert "actor_ref" not in payload
    assert "mailbox" not in payload
