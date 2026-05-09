from __future__ import annotations

import asyncio


class _Socket:
    def __init__(self, *, fail: bool = False) -> None:
        self.accepted = False
        self.sent: list[object] = []
        self.fail = fail

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: object) -> None:
        if self.fail:
            raise RuntimeError("disconnected")
        self.sent.append(data)


def test_websocket_manager_disconnects_failed_clients_without_breaking_others() -> None:
    from qts.api.websocket.manager import WebSocketConnectionManager

    manager = WebSocketConnectionManager()
    healthy = _Socket()
    failed = _Socket(fail=True)
    asyncio.run(manager.connect(healthy))
    asyncio.run(manager.connect(failed))

    asyncio.run(manager.broadcast({"event_type": "fill"}))

    assert healthy.sent == [{"event_type": "fill"}]
    assert manager.count == 1


def test_stream_event_dto_uses_public_payloads() -> None:
    from datetime import UTC, datetime

    from qts.api.websocket.dtos import StreamEventDTO

    event = StreamEventDTO(
        event_type="order.fill",
        event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        payload={"order_id": "ord-001"},
        correlation_id="corr-001",
    )

    assert event.payload == {"order_id": "ord-001"}


def test_order_fill_to_stream_dto_converts_fill_fields() -> None:
    from decimal import Decimal

    from qts.api.websocket.fill_adapter import order_fill_to_stream_dto
    from qts.core.ids import InstrumentId, OrderId
    from qts.execution.order_manager import OrderFill, OrderSide

    fill = OrderFill(
        fill_id="fill-001",
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("150.00"),
    )

    dto = order_fill_to_stream_dto(fill, correlation_id="corr-001")

    assert dto.event_type == "order.fill"
    assert dto.correlation_id == "corr-001"
    assert dto.payload["fill_id"] == "fill-001"
    assert dto.payload["order_id"] == "ord-001"
    assert dto.payload["instrument_id"] == "AAPL"
    assert dto.payload["side"] == "buy"
    assert dto.payload["quantity"] == "10"
    assert dto.payload["price"] == "150.00"
