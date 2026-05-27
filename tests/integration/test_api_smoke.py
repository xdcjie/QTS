from __future__ import annotations


def test_api_health_endpoint_works() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    response = client.get("/health/liveness")

    assert response.status_code == 200
    assert response.json() == {"status": "live"}
