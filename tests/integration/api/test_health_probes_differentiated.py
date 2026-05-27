"""Anchor: differentiated health probes carry distinct semantics.

Domain fact: an orchestrator (k8s) makes different decisions for liveness
vs readiness vs startup. Collapsing them under one endpoint forces the
orchestrator to choose poorly between "restart the pod" and "remove from
load balancer".

Owner: ``qts.api.routes.health`` exposes three endpoints.

Forbidden shortcut: returning identical state from all three probes;
gating any probe behind auth (Prometheus convention, same as /metrics).
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from qts.api.app import create_app


def test_health_liveness_returns_200_without_auth() -> None:
    client = TestClient(create_app())
    response = client.get("/health/liveness")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "live"


def test_health_readiness_returns_a_status() -> None:
    client = TestClient(create_app())
    response = client.get("/health/readiness")
    # 200 or 503 are both valid depending on runtime state; both must
    # surface a JSON body with a "ready" boolean for orchestrators.
    assert response.status_code in {200, 503}
    body = response.json()
    assert "ready" in body
    assert isinstance(body["ready"], bool)


def test_health_startup_returns_200_in_backtest_mode() -> None:
    client = TestClient(create_app())
    response = client.get("/health/startup")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "started"


def test_health_probes_bypass_authentication() -> None:
    client = TestClient(create_app())
    for path in ("/health/liveness", "/health/readiness", "/health/startup"):
        response = client.get(path)
        # 401/403 means the auth middleware caught it — these must bypass.
        assert response.status_code not in {401, 403}, path
