"""WebSocket handshake auth and scope enforcement."""

from __future__ import annotations

import hashlib

import pytest
from qts.api.security import Principal, StaticTokenAuthBackend
from starlette.websockets import WebSocketDisconnect


def test_websocket_handshake_rejects_missing_bearer_token() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws/events"):
        pass


def test_websocket_handshake_rejects_unknown_bearer_token() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(
            "/ws/events",
            headers={"Authorization": "Bearer not-a-real-token"},
        ),
    ):
        pass


def test_websocket_handshake_accepts_authorized_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import qts.api.app as app_module
    import qts.api.websocket.events as events_module
    from fastapi.testclient import TestClient

    monkeypatch.setattr(app_module, "default_auth_backend", _local_dev_backend)
    monkeypatch.setattr(events_module, "default_auth_backend", _local_dev_backend)
    client = TestClient(app_module.create_app())

    with client.websocket_connect(
        "/ws/events",
        headers={"Authorization": "Bearer dev-token"},
    ) as ws:
        bootstrap = ws.receive_json()
        assert bootstrap["event_type"] == "snapshot"


def test_websocket_handshake_rejects_principal_without_read_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import qts.api.app as app_module
    import qts.api.websocket.events as events_module
    from fastapi.testclient import TestClient

    def _no_scope_backend() -> StaticTokenAuthBackend:
        backend = StaticTokenAuthBackend.__new__(StaticTokenAuthBackend)
        backend._principals = {
            hashlib.sha256(b"empty-token").hexdigest(): Principal(
                id="no-scope",
                kind="service",
                scopes=frozenset(),
            ),
        }
        return backend

    monkeypatch.setattr(app_module, "default_auth_backend", _no_scope_backend)
    monkeypatch.setattr(events_module, "default_auth_backend", _no_scope_backend)
    client = TestClient(app_module.create_app())

    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(
            "/ws/events",
            headers={"Authorization": "Bearer empty-token"},
        ),
    ):
        pass


def _local_dev_backend() -> StaticTokenAuthBackend:
    backend = StaticTokenAuthBackend.__new__(StaticTokenAuthBackend)
    backend._principals = {
        hashlib.sha256(b"dev-token").hexdigest(): Principal(
            id="ws-test",
            kind="human",
            scopes=frozenset({"runtime:read"}),
        ),
    }
    return backend
