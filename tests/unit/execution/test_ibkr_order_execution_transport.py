from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qts.execution.adapters.ibkr_transport import (
        IbkrCommissionPayload,
        IbkrCommissionReport,
        IbkrConnectionEvent,
        IbkrConnectionEventPayload,
        IbkrErrorPayload,
        IbkrExecutionPayload,
        IbkrOrderExecutionCallbackSink,
        IbkrOrderRequest,
        IbkrOrderStatusPayload,
        IbkrTransportError,
    )
    from qts.execution.order_manager import ExecutionReport


def test_ibkr_order_execution_transport_dispatches_callbacks_to_adapter() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_transport import (
        IbkrCommissionPayload,
        IbkrConnectionEventPayload,
        IbkrErrorPayload,
        IbkrExecutionPayload,
        IbkrOrderExecutionTransport,
        IbkrOrderRequest,
        IbkrOrderStatusPayload,
    )
    from qts.execution.order_manager import ExecutionReport, OrderIntent, OrderSide
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )
    fake_transport = _FakeOrderExecutionTransport(sink=adapter)
    transport: IbkrOrderExecutionTransport = fake_transport
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    transport.connect()
    request = adapter.to_order_request(intent)
    transport.submit_order(request)
    accepted = transport.emit_order_status(
        IbkrOrderStatusPayload(
            report_id="status-001",
            broker_order_id="ibkr-001",
            status="Submitted",
        )
    )
    fill = transport.emit_execution(
        IbkrExecutionPayload(
            report_id="exec-001",
            broker_order_id="ibkr-001",
            execution_id="fill-001",
            filled_quantity=Decimal("10"),
            fill_price=Decimal("101.25"),
        )
    )
    completed_fill = transport.emit_commission(
        IbkrCommissionPayload(
            execution_id="fill-001",
            commission=Decimal("1.23"),
            currency="USD",
        )
    )
    error = transport.emit_error(
        IbkrErrorPayload(request_id=7, code=1100, message="Connectivity between IB and TWS lost")
    )
    disconnect = transport.emit_disconnect(IbkrConnectionEventPayload(reason="socket closed"))
    reconnect = transport.emit_reconnect(IbkrConnectionEventPayload(reason="socket restored"))
    transport.disconnect()

    assert fake_transport.submitted_requests == [request]
    assert isinstance(request, IbkrOrderRequest)
    assert accepted.broker_order_id == "ibkr-001"
    assert accepted.status.value == "accepted"
    assert fill is None
    assert isinstance(completed_fill, ExecutionReport)
    assert completed_fill.fill_id == "fill-001"
    assert completed_fill.filled_quantity == Decimal("10")
    assert completed_fill.commission == Decimal("1.23")
    assert error.code == 1100
    assert disconnect.kind == "disconnect"
    assert reconnect.kind == "reconnect"
    assert not transport.connected


def test_ibkr_tws_order_execution_transport_builds_limit_order_and_normalizes_cancel() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_transport import (
        IbkrOrderContractSpec,
        IbkrOrderStatusPayload,
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )
    from qts.execution.broker import BrokerOrderType
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )
    transport = IbkrTwsOrderExecutionTransport(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
        ),
        sink=adapter,
    )
    request = adapter.to_order_request(
        OrderIntent(
            order_id=OrderId("ord-002"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        ),
        order_type=BrokerOrderType.LIMIT,
        limit_price=Decimal("0.01"),
        contract=IbkrOrderContractSpec.stock("AAPL", primary_exchange="ISLAND"),
    )

    contract = request.to_ibapi_contract()
    order = request.to_ibapi_order()
    cancel_report = transport.emit_order_status(
        IbkrOrderStatusPayload(
            report_id="status-002",
            broker_order_id="777",
            status="Cancelled",
        )
    )

    assert contract.symbol == "AAPL"
    assert contract.secType == "STK"
    assert contract.exchange == "SMART"
    assert contract.primaryExchange == "ISLAND"
    assert order.action == "BUY"
    assert order.orderType == "LMT"
    assert order.totalQuantity == Decimal("1")
    assert order.lmtPrice == 0.01
    assert order.account == "DU1234567"
    assert cancel_report.status.value == "cancelled"
    assert cancel_report.broker_order_id == "777"


@dataclass(slots=True)
class _FakeOrderExecutionTransport:
    sink: IbkrOrderExecutionCallbackSink
    connected: bool = False
    submitted_requests: list[IbkrOrderRequest] = field(default_factory=list)

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def submit_order(self, request: IbkrOrderRequest) -> None:
        self.submitted_requests.append(request)

    def cancel_order(self, broker_order_id: str) -> None:
        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")

    def emit_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport:
        return self.sink.on_order_status(payload)

    def emit_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        return self.sink.on_execution(payload)

    def emit_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | IbkrCommissionReport:
        return self.sink.on_commission(payload)

    def emit_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        return self.sink.on_error(payload)

    def emit_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        return self.sink.on_disconnect(payload)

    def emit_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        return self.sink.on_reconnect(payload)
