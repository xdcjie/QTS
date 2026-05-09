from __future__ import annotations


def test_websocket_event_stream_connects_and_emits_synthetic_event() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    with client.websocket_connect("/ws/events") as websocket:
        assert websocket.receive_json() == {
            "event_type": "system.synthetic",
            "message": "connected",
        }
