"""Unbound operator lifecycle commands return structured rejected results."""

from __future__ import annotations

from fastapi.testclient import TestClient
from qts.api.app import create_app


def test_operations_unbound_lifecycle_returns_rejected_result() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/operations/runtime/pause",
        headers={
            "Authorization": "Bearer dev-token",
            "Idempotency-Key": "pause-unbound-integration",
            "X-QTS-Operator": "tester",
            "X-QTS-Runtime-Instance-Id": "rt-unbound-integration",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "rejected"
    assert payload["reason_code"] == "RUNTIME_SESSION_NOT_BOUND"
    assert payload["evidence"]["runtime_instance_id"] == "rt-unbound-integration"
