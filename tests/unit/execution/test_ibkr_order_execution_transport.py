from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from threading import Event
from typing import TYPE_CHECKING, Any, cast

import pytest

if TYPE_CHECKING:
    from qts.domain.orders import ExecutionReport
    from qts.execution.broker import BrokerCommissionReport
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrAccountSummaryPayload,
        IbkrCommissionPayload,
        IbkrConnectionEvent,
        IbkrConnectionEventPayload,
        IbkrErrorPayload,
        IbkrExecutionPayload,
        IbkrOpenOrderPayload,
        IbkrOrderExecutionCallbackSink,
        IbkrOrderRequest,
        IbkrOrderStatusPayload,
        IbkrPositionPayload,
        IbkrTransportError,
    )


def test_ibkr_tws_order_execution_transport_has_split_owners() -> None:
    from qts.execution.transports.ibkr_tws_callback_dispatcher import (
        IbkrTwsCallbackDispatcher,
    )
    from qts.execution.transports.ibkr_tws_connection import IbkrTwsConnection
    from qts.execution.transports.ibkr_tws_execution_event_emitter import (
        IbkrTwsExecutionEventEmitter,
    )
    from qts.execution.transports.ibkr_tws_order_client import IbkrTwsOrderClient
    from qts.execution.transports.ibkr_tws_reconciliation_client import (
        IbkrTwsReconciliationClient,
    )

    assert IbkrTwsConnection.__module__ == "qts.execution.transports.ibkr_tws_connection"
    assert IbkrTwsOrderClient.__module__ == "qts.execution.transports.ibkr_tws_order_client"
    assert IbkrTwsReconciliationClient.__module__ == (
        "qts.execution.transports.ibkr_tws_reconciliation_client"
    )
    assert IbkrTwsCallbackDispatcher.__module__ == (
        "qts.execution.transports.ibkr_tws_callback_dispatcher"
    )
    assert IbkrTwsExecutionEventEmitter.__module__ == (
        "qts.execution.transports.ibkr_tws_execution_event_emitter"
    )


def test_execution_transports_package_exports_tws_split_owners() -> None:
    from qts.execution.transports import (
        IbkrTwsCallbackDispatcher,
        IbkrTwsConnection,
        IbkrTwsExecutionEventEmitter,
        IbkrTwsOrderClient,
        IbkrTwsReconciliationClient,
    )

    assert IbkrTwsConnection.__name__ == "IbkrTwsConnection"
    assert IbkrTwsOrderClient.__name__ == "IbkrTwsOrderClient"
    assert IbkrTwsReconciliationClient.__name__ == "IbkrTwsReconciliationClient"
    assert IbkrTwsCallbackDispatcher.__name__ == "IbkrTwsCallbackDispatcher"
    assert IbkrTwsExecutionEventEmitter.__name__ == "IbkrTwsExecutionEventEmitter"


def test_ibkr_tws_order_execution_transport_facade_delegates_split_responsibilities() -> None:
    import inspect

    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrTwsOrderExecutionTransport,
    )

    source = inspect.getsource(IbkrTwsOrderExecutionTransport)

    assert "placeOrder(" not in source
    assert "cancelOrder(" not in source
    assert "reqOpenOrders(" not in source
    assert "IbkrOrderStatusPayload(" not in source
    assert "IbkrOpenOrderPayload(" not in source
    assert "IbkrExecutionPayload(" not in source


def test_ibkr_tws_connection_does_not_create_domain_execution_reports() -> None:
    import inspect

    from qts.execution.transports.ibkr_tws_connection import IbkrTwsConnection

    source = inspect.getsource(IbkrTwsConnection)

    assert "ExecutionReport" not in source
    assert "BrokerExecutionReport" not in source
    assert "IbkrOrderStatusPayload" not in source
    assert "IbkrExecutionPayload" not in source


def test_ibkr_tws_order_client_does_not_process_callbacks_or_hold_business_state() -> None:
    import inspect

    from qts.execution.transports.ibkr_tws_order_client import IbkrTwsOrderClient

    source = inspect.getsource(IbkrTwsOrderClient)

    assert "_submitted_requests" not in source
    assert "handle_" not in source
    assert "on_order_status" not in source
    assert "on_execution" not in source
    assert "on_commission" not in source
    assert "IbkrOrderStatusPayload" not in source
    assert "IbkrExecutionPayload" not in source


def test_ibkr_tws_callback_dispatcher_does_not_submit_or_cancel_orders() -> None:
    import inspect

    from qts.execution.transports.ibkr_tws_callback_dispatcher import (
        IbkrTwsCallbackDispatcher,
    )

    source = inspect.getsource(IbkrTwsCallbackDispatcher)

    assert "placeOrder" not in source
    assert "cancelOrder" not in source
    assert "submit_order" not in source
    assert "cancel_order" not in source
    assert "IbkrTwsOrderClient" not in source


def test_ibkr_tws_execution_event_emitter_only_publishes_normalized_events() -> None:
    import inspect

    from qts.execution.transports.ibkr_tws_execution_event_emitter import (
        IbkrTwsExecutionEventEmitter,
    )

    source = inspect.getsource(IbkrTwsExecutionEventEmitter)

    assert "_sink" not in source
    assert "on_order_status" not in source
    assert "on_execution" not in source
    assert "on_commission" not in source
    assert "IbkrOrderStatusPayload" not in source
    assert "IbkrExecutionPayload" not in source


def test_ibkr_tws_order_execution_transport_facade_has_no_duplicate_business_state() -> None:
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )

    transport = IbkrTwsOrderExecutionTransport(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
        ),
        sink=_RecordingSink(),
    )

    assert set(vars(transport)) == {
        "config",
        "_reports",
        "_seen_errors",
        "_connection",
        "_order_client",
        "_reconciliation_client",
        "_event_emitter",
        "_callback_dispatcher",
    }
    assert not hasattr(transport, "_submitted_requests")
    assert not hasattr(transport, "_order_map")
    assert not hasattr(transport, "_callback_quarantine")


def test_ibkr_tws_callback_dispatcher_converts_raw_callbacks_to_payloads() -> None:
    import queue

    from qts.execution.transports.ibkr_tws_callback_dispatcher import (
        IbkrTwsCallbackDispatcher,
    )
    from qts.execution.transports.ibkr_tws_execution_event_emitter import (
        IbkrTwsExecutionEventEmitter,
    )

    class Contract:
        symbol = "AAPL"

    class Order:
        orderRef = "client-001"
        permId = 999
        action = "BUY"
        totalQuantity = Decimal("2")

    class OrderState:
        status = "Submitted"

    sink = _RecordingSink()
    emitter = IbkrTwsExecutionEventEmitter(reports=queue.Queue())
    dispatcher = IbkrTwsCallbackDispatcher(sink=sink, emitter=emitter)

    dispatcher.handle_open_order(
        order_id=123,
        contract=Contract(),
        order=Order(),
        order_state=OrderState(),
    )
    dispatcher.handle_position(account_id="DU123", contract=Contract(), position=Decimal("2"))

    open_order = sink.open_orders[0]
    position = sink.positions[0]

    assert open_order.broker_order_id == "123"
    assert open_order.client_order_id == "client-001"
    assert open_order.broker_symbol == "AAPL"
    assert position.account_id == "DU123"
    assert position.quantity == Decimal("2")


def test_ibkr_tws_order_client_submits_and_cancels_without_callback_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qts.execution.transports.ibkr_order_ids import IbkrOrderIdAllocator
    from qts.execution.transports.ibkr_tws_order_client import IbkrTwsOrderClient
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrTwsOrderExecutionTransportConfig,
    )

    class OrderCancel:
        pass

    monkeypatch.setattr(
        "qts.execution.transports.ibkr_tws_order_client._ibapi_attr",
        lambda module_name, attribute_name: OrderCancel,
    )
    app = _OrderClientApp()
    allocator = IbkrOrderIdAllocator()
    allocator.reconcile_next_valid_id(client_id=201, broker_next_valid_id=700)
    sink = _RecordingSink()
    client = IbkrTwsOrderClient(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
        ),
        sink=sink,
        order_id_allocator=allocator,
    )
    request = cast(Any, _OrderClientRequest())

    broker_order_id = client.submit_order_with_broker_id(app, request)
    client.cancel_order(app, broker_order_id)

    assert broker_order_id == "700"
    assert app.placed_orders == [(700, "contract", "order")]
    assert app.cancelled_orders[0][0] == 700
    assert sink.submitted_orders == [(request, "700")]


def test_ibkr_tws_reconciliation_client_requests_broker_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrTwsOrderExecutionTransportConfig,
    )
    from qts.execution.transports.ibkr_tws_reconciliation_client import (
        IbkrTwsReconciliationClient,
    )

    class ExecutionFilter:
        pass

    monkeypatch.setattr(
        "qts.execution.transports.ibkr_tws_reconciliation_client._ibapi_attr",
        lambda module_name, attribute_name: ExecutionFilter,
    )
    app = _StartupReconciliationApp()
    client = IbkrTwsReconciliationClient(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            request_all_open_orders_on_reconnect=True,
        )
    )

    client.request_startup_reconciliation(app)

    assert app.calls[0] == ("reqOpenOrders",)
    assert app.calls[1] == ("reqAllOpenOrders",)
    assert app.calls[2] == ("reqPositions",)
    assert app.calls[3][0] == "reqExecutions"
    assert app.calls[3][1] == 1
    assert app.calls[4][0] == "reqAccountSummary"
    assert app.calls[4][1] == 2


def test_ibkr_order_execution_transport_dispatches_callbacks_to_adapter() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.domain.orders import (
        ExecutionReport,
        OrderIntent,
        OrderSide,
    )
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrCommissionPayload,
        IbkrConnectionEventPayload,
        IbkrErrorPayload,
        IbkrExecutionPayload,
        IbkrOrderExecutionTransport,
        IbkrOrderRequest,
        IbkrOrderStatusPayload,
    )
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
    request = adapter.to_order_request(intent, client_order_id="client-ord-001")
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
    assert accepted is not None
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
    from qts.domain.orders import (
        OrderIntent,
        OrderSide,
        OrderType,
    )
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrOrderContractSpec,
        IbkrOrderStatusPayload,
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )
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
        client_order_id="client-ord-002",
        order_type=OrderType.LIMIT,
        limit_price=Decimal("0.01"),
        outside_regular_trading_hours=True,
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
    assert order.orderRef == "client-ord-002"
    assert order.outsideRth is True
    assert cancel_report is not None
    assert cancel_report.status.value == "cancelled"
    assert cancel_report.broker_order_id == "777"


def test_ibkr_order_contract_spec_builds_future_contract_month(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrOrderContractSpec,
    )

    class Contract:
        pass

    monkeypatch.setattr(
        "qts.execution.transports.ibkr_tws_order_execution_transport._ibapi_attr",
        lambda module_name, attribute_name: Contract,
    )

    contract = IbkrOrderContractSpec.future(
        "MES",
        exchange="CME",
        currency="USD",
        last_trade_date_or_contract_month="202606",
    ).to_ibapi_contract()

    assert contract.symbol == "MES"
    assert contract.secType == "FUT"
    assert contract.exchange == "CME"
    assert contract.currency == "USD"
    assert contract.lastTradeDateOrContractMonth == "202606"


def test_ibkr_order_request_builds_bracket_parent_and_oco_children(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.domain.orders import BracketLeg, OrderSide, OrderType, TimeInForce
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderRequest

    class Order:
        pass

    monkeypatch.setattr(
        "qts.execution.transports.ibkr_tws_order_execution_transport._ibapi_attr",
        lambda module_name, attribute_name: Order,
    )
    request = IbkrOrderRequest(
        internal_order_id=OrderId("ord-bracket"),
        client_order_id="client-bracket",
        internal_account_id=AccountId("acct-1"),
        strategy_id=StrategyId("strategy-1"),
        account_id="DU1234567",
        broker_symbol="AAPL",
        side=OrderSide.BUY.value,
        quantity=Decimal("1"),
        order_type=OrderType.BRACKET,
        time_in_force=TimeInForce.GTC,
        limit_price=Decimal("0.01"),
        bracket_legs=(
            BracketLeg(
                order_type=OrderType.LIMIT,
                side=OrderSide.SELL.value,
                quantity=Decimal("1"),
                limit_price=Decimal("9999"),
            ),
            BracketLeg(
                order_type=OrderType.STOP,
                side=OrderSide.SELL.value,
                quantity=Decimal("1"),
                stop_price=Decimal("0.01"),
            ),
        ),
    )

    parent, take_profit, stop_loss = request.to_ibapi_bracket_orders(
        parent_order_id=700,
        child_order_ids=(701, 702),
    )

    assert parent.orderId == 700
    assert parent.orderType == "LMT"
    assert parent.lmtPrice == 0.01
    assert parent.whatIf is False
    assert parent.transmit is False
    assert take_profit.orderId == 701
    assert take_profit.parentId == 700
    assert take_profit.orderType == "LMT"
    assert take_profit.lmtPrice == 9999.0
    assert take_profit.whatIf is False
    assert take_profit.transmit is False
    assert stop_loss.orderId == 702
    assert stop_loss.parentId == 700
    assert stop_loss.orderType == "STP"
    assert stop_loss.auxPrice == 0.01
    assert stop_loss.whatIf is False
    assert stop_loss.transmit is True


def test_ibkr_order_request_builds_what_if_bracket_with_transmit_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.domain.orders import BracketLeg, OrderSide, OrderType
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderRequest

    class Order:
        pass

    monkeypatch.setattr(
        "qts.execution.transports.ibkr_tws_order_execution_transport._ibapi_attr",
        lambda module_name, attribute_name: Order,
    )
    request = IbkrOrderRequest(
        internal_order_id=OrderId("ord-bracket-what-if"),
        client_order_id="client-bracket-what-if",
        internal_account_id=AccountId("acct-1"),
        strategy_id=StrategyId("strategy-1"),
        account_id="DU1234567",
        broker_symbol="AAPL",
        side=OrderSide.BUY.value,
        quantity=Decimal("1"),
        order_type=OrderType.BRACKET,
        limit_price=Decimal("0.01"),
        what_if=True,
        bracket_legs=(
            BracketLeg(
                order_type=OrderType.LIMIT,
                side=OrderSide.SELL.value,
                quantity=Decimal("1"),
                limit_price=Decimal("9999"),
            ),
            BracketLeg(
                order_type=OrderType.STOP,
                side=OrderSide.SELL.value,
                quantity=Decimal("1"),
                stop_price=Decimal("0.01"),
            ),
        ),
    )

    orders = request.to_ibapi_bracket_orders(parent_order_id=700, child_order_ids=(701, 702))

    assert [order.whatIf for order in orders] == [True, True, True]
    assert [order.transmit for order in orders] == [True, True, True]


def test_ibkr_tws_order_client_submits_bracket_as_parent_and_children() -> None:
    from qts.execution.transports.ibkr_order_ids import IbkrOrderIdAllocator
    from qts.execution.transports.ibkr_tws_order_client import IbkrTwsOrderClient
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrTwsOrderExecutionTransportConfig,
    )

    app = _OrderClientApp()
    allocator = IbkrOrderIdAllocator()
    allocator.reconcile_next_valid_id(client_id=201, broker_next_valid_id=700)
    sink = _RecordingSink()
    client = IbkrTwsOrderClient(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
        ),
        sink=sink,
        order_id_allocator=allocator,
    )
    request = cast(Any, _BracketOrderClientRequest())

    broker_order_id = client.submit_order_with_broker_id(app, request)

    assert broker_order_id == "700"
    assert app.placed_orders == [
        (700, "contract", _FakeIbkrOrder(orderId=700, label="parent")),
        (701, "contract", _FakeIbkrOrder(orderId=701, label="take_profit")),
        (702, "contract", _FakeIbkrOrder(orderId=702, label="stop_loss")),
    ]
    assert sink.submitted_orders == [(request, "700")]


def test_ibkr_tws_order_execution_transport_handles_older_commission_report() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.domain.orders import ExecutionReport
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrExecutionPayload,
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    class OlderCommissionReport:
        execId = "fill-001"
        commission = 1.25
        currency = "USD"

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
    transport.emit_execution(
        IbkrExecutionPayload(
            report_id="exec-001",
            broker_order_id="1",
            execution_id="fill-001",
            filled_quantity=Decimal("1"),
            fill_price=Decimal("294.42"),
        )
    )

    transport.handle_commission_report(OlderCommissionReport())
    completed = transport.wait_for_fill_report("1", timeout_seconds=1)

    assert isinstance(completed, ExecutionReport)
    assert completed.fill_id == "fill-001"
    assert completed.commission == Decimal("1.25")


def test_ibkr_tws_order_execution_transport_waits_through_transient_connectivity_status() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.domain.orders import ExecutionReportStatus
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrErrorPayload,
        IbkrOrderStatusPayload,
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )
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
    transport.emit_error(
        IbkrErrorPayload(
            request_id=-1,
            code=2110,
            message=(
                "Connectivity between TWS and server is broken. It will be restored automatically."
            ),
        )
    )
    transport.emit_error(
        IbkrErrorPayload(
            request_id=-1,
            code=1104,
            message="Pending to create 1 orders: 777",
        )
    )
    transport.emit_order_status(
        IbkrOrderStatusPayload(
            report_id="status-001",
            broker_order_id="777",
            status="Submitted",
        )
    )

    report = transport.wait_for_order_status(
        "777",
        statuses={ExecutionReportStatus.ACCEPTED},
        timeout_seconds=1,
    )

    assert report.broker_order_id == "777"
    assert report.status is ExecutionReportStatus.ACCEPTED


def test_ibkr_tws_order_execution_transport_does_not_queue_unknown_status() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.domain.orders import ExecutionReportStatus
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrOrderStatusPayload,
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )
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
        order_map=BrokerOrderMap(),
    )
    transport = IbkrTwsOrderExecutionTransport(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            timeout_seconds=0.01,
        ),
        sink=adapter,
    )
    status = IbkrOrderStatusPayload(
        report_id="status-unknown",
        broker_order_id="999",
        status="Submitted",
    )

    result = transport.emit_order_status(status)

    assert result is None
    assert adapter.quarantined_order_statuses == (status,)
    with pytest.raises(TimeoutError, match="timed out waiting"):
        transport.wait_for_order_status(
            "999",
            statuses={ExecutionReportStatus.ACCEPTED},
            timeout_seconds=0.01,
        )


def test_ibkr_tws_order_execution_transport_handles_open_order_callback() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    class OpenOrder:
        orderRef = "client-ord-001"
        permId = 99001

    class OpenOrderState:
        status = "Submitted"

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="client-ord-001",
        account_id=AccountId("acct-ibkr"),
        strategy_id=StrategyId("strategy-ibkr"),
        submitted_at=datetime(2026, 5, 14, 12, 0, tzinfo=UTC),
    )
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
        order_map=order_map,
    )
    transport = IbkrTwsOrderExecutionTransport(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
        ),
        sink=adapter,
    )

    transport.handle_open_order(order_id=100, order=OpenOrder(), order_state=OpenOrderState())

    assert order_map.by_ibkr_order_id("100").client_order_id == "client-ord-001"
    assert order_map.by_perm_id("99001").status == "Submitted"


def test_ibkr_tws_order_execution_transport_requests_startup_reconciliation() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )
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
    app = _StartupReconciliationApp()
    transport = IbkrTwsOrderExecutionTransport(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            request_all_open_orders_on_reconnect=True,
        ),
        sink=adapter,
    )
    transport._app = app

    transport.request_startup_reconciliation()

    assert app.calls[0] == ("reqOpenOrders",)
    assert app.calls[1] == ("reqAllOpenOrders",)
    assert app.calls[2] == ("reqPositions",)
    assert app.calls[3][0] == "reqExecutions"
    assert app.calls[3][1] == 1
    assert app.calls[4] == (
        "reqAccountSummary",
        2,
        "All",
        "NetLiquidation,TotalCashValue,AvailableFunds",
    )

    default_app = _StartupReconciliationApp()
    default_transport = IbkrTwsOrderExecutionTransport(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
        ),
        sink=adapter,
    )
    default_transport._app = default_app

    default_transport.request_startup_reconciliation()

    assert ("reqAllOpenOrders",) not in default_app.calls


def test_ibkr_tws_order_execution_transport_bounds_blocking_ibapi_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )
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
    app = _BlockingConnectApp()
    monkeypatch.setattr(
        "qts.execution.transports.ibkr_tws_order_execution_transport._new_order_execution_app",
        lambda owner: app,
    )
    transport = IbkrTwsOrderExecutionTransport(
        config=IbkrTwsOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            timeout_seconds=0.01,
        ),
        sink=adapter,
    )

    with pytest.raises(TimeoutError, match="timed out connecting"):
        transport.connect()

    assert app.disconnect_called
    assert not transport.connected


@dataclass(slots=True)
class _RecordingSink:
    submitted_orders: list[tuple[IbkrOrderRequest, str]] = field(default_factory=list)
    open_orders: list[IbkrOpenOrderPayload] = field(default_factory=list)
    positions: list[IbkrPositionPayload] = field(default_factory=list)
    account_summaries: list[IbkrAccountSummaryPayload] = field(default_factory=list)

    def record_submitted_order(
        self,
        request: IbkrOrderRequest,
        *,
        ibkr_order_id: str,
        submitted_at: object | None = None,
    ) -> None:
        del submitted_at
        self.submitted_orders.append((request, ibkr_order_id))

    def on_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        del payload
        return None

    def on_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        self.open_orders.append(payload)

    def on_position(self, payload: IbkrPositionPayload) -> None:
        self.positions.append(payload)

    def on_account_summary(self, payload: IbkrAccountSummaryPayload) -> None:
        self.account_summaries.append(payload)

    def on_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        del payload
        return None

    def on_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | BrokerCommissionReport:
        from qts.execution.broker import BrokerCommissionReport

        return BrokerCommissionReport(
            execution_id=payload.execution_id,
            commission=payload.commission,
            currency=payload.currency,
        )

    def on_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        from qts.execution.transports.ibkr_tws_order_execution_transport import (
            IbkrTransportError,
        )

        return IbkrTransportError(
            request_id=payload.request_id,
            code=payload.code,
            message=payload.message,
        )

    def on_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        from qts.execution.transports.ibkr_tws_order_execution_transport import (
            IbkrConnectionEvent,
        )

        return IbkrConnectionEvent(kind="disconnect", reason=payload.reason)

    def on_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        from qts.execution.transports.ibkr_tws_order_execution_transport import (
            IbkrConnectionEvent,
        )

        return IbkrConnectionEvent(kind="reconnect", reason=payload.reason)


@dataclass(slots=True)
class _OrderClientApp:
    placed_orders: list[tuple[int, object, object]] = field(default_factory=list)
    cancelled_orders: list[tuple[int, object]] = field(default_factory=list)

    def placeOrder(self, order_id: int, contract: object, order: object) -> None:
        self.placed_orders.append((order_id, contract, order))

    def cancelOrder(self, order_id: int, order_cancel: object) -> None:
        self.cancelled_orders.append((order_id, order_cancel))


class _OrderClientRequest:
    from qts.domain.orders import OrderType

    order_type = OrderType.MARKET

    def to_ibapi_contract(self) -> str:
        return "contract"

    def to_ibapi_order(self) -> str:
        return "order"


class _BracketOrderClientRequest:
    from qts.domain.orders import OrderType

    order_type = OrderType.BRACKET
    bracket_legs = ("take_profit", "stop_loss")

    def to_ibapi_contract(self) -> str:
        return "contract"

    def to_ibapi_bracket_orders(
        self,
        *,
        parent_order_id: int,
        child_order_ids: tuple[int, ...],
    ) -> tuple[object, ...]:
        assert parent_order_id == 700
        assert child_order_ids == (701, 702)
        return (
            _FakeIbkrOrder(orderId=700, label="parent"),
            _FakeIbkrOrder(orderId=701, label="take_profit"),
            _FakeIbkrOrder(orderId=702, label="stop_loss"),
        )


@dataclass(frozen=True, slots=True)
class _FakeIbkrOrder:
    orderId: int
    label: str


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

    def emit_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        return self.sink.on_order_status(payload)

    def emit_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        return self.sink.on_execution(payload)

    def emit_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | BrokerCommissionReport:
        return self.sink.on_commission(payload)

    def emit_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        return self.sink.on_error(payload)

    def emit_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        return self.sink.on_disconnect(payload)

    def emit_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        return self.sink.on_reconnect(payload)


class _BlockingConnectApp:
    def __init__(self) -> None:
        self._disconnected = Event()
        self.disconnect_called = False

    def connect(self, host: str, port: int, client_id: int) -> None:
        del host, port, client_id
        self._disconnected.wait(timeout=5)

    def disconnect(self) -> None:
        self.disconnect_called = True
        self._disconnected.set()

    def isConnected(self) -> bool:
        return False

    def run(self) -> None:
        return None


@dataclass(slots=True)
class _StartupReconciliationApp:
    calls: list[tuple[object, ...]] = field(default_factory=list)

    def isConnected(self) -> bool:
        return True

    def reqOpenOrders(self) -> None:
        self.calls.append(("reqOpenOrders",))

    def reqAllOpenOrders(self) -> None:
        self.calls.append(("reqAllOpenOrders",))

    def reqPositions(self) -> None:
        self.calls.append(("reqPositions",))

    def reqExecutions(self, request_id: int, execution_filter: object) -> None:
        self.calls.append(("reqExecutions", request_id, type(execution_filter).__name__))

    def reqAccountSummary(self, request_id: int, group_name: str, tags: str) -> None:
        self.calls.append(("reqAccountSummary", request_id, group_name, tags))
