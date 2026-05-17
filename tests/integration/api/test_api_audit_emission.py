"""Anchor: every auth decision emits exactly one api.auth_decision audit event."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from qts.api.routes import (
    accounts_router,
    backtests_router,
    health_router,
    operations_router,
    orders_router,
    strategies_router,
)
from qts.api.security import ApiSecurityMiddleware, default_auth_backend
from qts.api.websocket import events_router
from qts.observability.audit_sink import InMemoryAuditSink


@pytest.fixture
def sink() -> InMemoryAuditSink:
    return InMemoryAuditSink()


def _app_with_sink(sink: InMemoryAuditSink) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-QTS-Operator"],
    )
    app.add_middleware(
        ApiSecurityMiddleware,
        auth_backend=default_auth_backend(),
        audit_sink=sink,
    )
    app.include_router(health_router)
    app.include_router(backtests_router)
    app.include_router(strategies_router)
    app.include_router(accounts_router)
    app.include_router(orders_router)
    app.include_router(operations_router)
    app.include_router(events_router)
    return app


def test_rejected_auth_emits_single_audit_event(sink: InMemoryAuditSink) -> None:
    client = TestClient(_app_with_sink(sink))
    response = client.post(
        "/operations/runtime/start",
        headers={"X-QTS-Operator": "alice"},
    )
    assert response.status_code == 401
    events = sink.events()
    assert len(events) == 1
    event = events[0]
    assert event.event_type == "api.auth_decision"
    assert "401" in event.message
    assert "POST" in event.message
    assert "/operations/runtime/start" in event.message


def test_authorized_call_emits_audit_event_with_principal_id(sink: InMemoryAuditSink) -> None:
    client = TestClient(_app_with_sink(sink))
    response = client.get(
        "/operations/operator-status",
        headers={
            "Authorization": "Bearer dev-token",
            "X-QTS-Operator": "alice",
        },
    )
    assert response.status_code == 200
    events = sink.events()
    assert len(events) == 1
    assert events[0].event_type == "api.auth_decision"
    assert events[0].actor == "local-dev"
    assert "200" in events[0].message


def test_insufficient_scope_emits_403_audit_event(sink: InMemoryAuditSink) -> None:
    client = TestClient(_app_with_sink(sink))
    response = client.post(
        "/operations/runtime/start",
        headers={
            "Authorization": "Bearer read-token",
            "X-QTS-Operator": "alice",
        },
    )
    assert response.status_code == 403
    events = sink.events()
    assert len(events) == 1
    assert "403" in events[0].message
    assert events[0].actor == "local-read"
