from __future__ import annotations


def test_api_can_submit_backtest_request() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    config_path = "configs/backtest.gc_si.example.yaml"

    client = TestClient(create_app())

    response = client.post("/backtests", json={"config_path": config_path})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"].startswith("bt-")
    assert payload["manifest_path"].endswith(".manifest.json")
    assert payload["equity_curve_path"].endswith(".equity_curve.ndjson")
    assert payload["orders_path"].endswith(".orders.ndjson")
    assert payload["fills_path"].endswith(".fills.ndjson")
    assert {"equity_curve", "orders", "fills"} <= set(payload["artifact_hashes"])
    assert "metrics" in payload
    assert "status" not in payload
    assert "config_path" not in payload
    assert "actor_ref" not in payload
    assert "mailbox" not in payload


def test_api_can_list_backtest_runs() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    config_path = "configs/backtest.gc_si.example.yaml"

    client = TestClient(create_app())
    client.post("/backtests", json={"config_path": config_path})
    response = client.get("/backtests?limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload
    assert {"run_id", "config_path", "status"} <= set(payload[0].keys())


def test_api_can_list_backtest_strategy_options() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    response = client.get("/backtests/strategy-options")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert {
        "label": "gc-si-momentum",
        "config_path": "configs/backtest.gc_si.example.yaml",
    } in payload
