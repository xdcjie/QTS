from __future__ import annotations

from decimal import Decimal


def test_websocket_event_stream_connects_and_emits_synthetic_event() -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    client = TestClient(create_app())

    with client.websocket_connect("/ws/events") as websocket:
        assert websocket.receive_json() == {
            "event_type": "system.synthetic",
            "message": "connected",
        }


def test_fill_event_can_be_transformed_into_stream_dto_and_delivered() -> None:
    """A fill event can be transformed into stream DTO and delivered."""
    from qts.api.websocket.fill_adapter import order_fill_to_stream_dto
    from qts.core.ids import InstrumentId, OrderId
    from qts.execution.order_manager import OrderFill, OrderSide

    # Create a domain fill event
    fill = OrderFill(
        fill_id="fill-001",
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("150.00"),
    )

    # Transform to stream DTO
    dto = order_fill_to_stream_dto(fill, correlation_id="corr-001")

    # Verify DTO fields are correct and no actor internals leak
    assert dto.event_type == "order.fill"
    assert dto.payload["fill_id"] == "fill-001"
    assert dto.payload["order_id"] == "ord-001"
    assert "broker_symbol" not in dto.payload
    assert "contract_spec" not in dto.payload

    # Verify DTO can be serialized for WebSocket delivery
    import dataclasses

    payload = {k: v for k, v in dataclasses.asdict(dto).items() if k != "event_time"}
    assert payload["event_type"] == "order.fill"
    assert payload["correlation_id"] == "corr-001"
