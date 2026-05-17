from __future__ import annotations


def test_state_changing_api_requires_bearer_authentication() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    response = client.post("/operations/runtime/start", headers={"X-QTS-Operator": "alice"})

    assert response.status_code == 401
