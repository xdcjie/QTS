from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal


def test_ib_async_order_execution_transport_normalizes_fill_with_commission() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.domain.orders import (
        ExecutionReportStatus,
        OrderIntent,
        OrderSide,
        OrderType,
    )
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.transports.ib_async_order_execution_transport import (
        IbAsyncOrderExecutionTransport,
        IbAsyncOrderExecutionTransportConfig,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderContractSpec
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
    fake_ib = _FakeIb()
    transport = IbAsyncOrderExecutionTransport(
        config=IbAsyncOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            timeout_seconds=1,
        ),
        sink=adapter,
        ib_factory=lambda: fake_ib,
    )
    request = adapter.to_order_request(
        OrderIntent(
            order_id=OrderId("ord-001"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        ),
        client_order_id="client-ord-001",
        order_type=OrderType.LIMIT,
        limit_price=Decimal("101.25"),
        outside_regular_trading_hours=True,
        contract=IbkrOrderContractSpec.stock("AAPL", primary_exchange="ISLAND"),
    )

    transport.connect()
    broker_order_id = transport.submit_order_with_broker_id(request)
    accepted = transport.wait_for_order_status(
        broker_order_id,
        statuses={ExecutionReportStatus.ACCEPTED},
        timeout_seconds=1,
    )
    fill = transport.wait_for_fill_report(broker_order_id, timeout_seconds=1)
    transport.disconnect()

    placed_order = fake_ib.placed_orders[0]
    assert broker_order_id == "77"
    assert fake_ib.qualified_contracts == ["AAPL"]
    assert accepted.status is ExecutionReportStatus.ACCEPTED
    assert fill.status is ExecutionReportStatus.FILLED
    assert fill.fill_id == "exec-001"
    assert fill.filled_quantity == Decimal("1")
    assert fill.fill_price == Decimal("101.25")
    assert fill.commission == Decimal("1.23")
    assert placed_order.account == "DU1234567"
    assert placed_order.outsideRth is True
    assert placed_order.orderType == "LMT"
    assert not transport.connected


def test_ib_async_order_execution_transport_raises_broker_error() -> None:
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
    from qts.execution.transports.ib_async_order_execution_transport import (
        IbAsyncOrderExecutionTransport,
        IbAsyncOrderExecutionTransportConfig,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderContractSpec
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
    fake_ib = _FakeIb(error_on_place=(201, "Potential Pattern Day Trade"))
    transport = IbAsyncOrderExecutionTransport(
        config=IbAsyncOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            timeout_seconds=1,
        ),
        sink=adapter,
        ib_factory=lambda: fake_ib,
    )
    request = adapter.to_order_request(
        OrderIntent(
            order_id=OrderId("ord-001"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        ),
        client_order_id="client-ord-001",
        order_type=OrderType.LIMIT,
        limit_price=Decimal("101.25"),
        contract=IbkrOrderContractSpec.stock("AAPL", primary_exchange="ISLAND"),
    )

    transport.connect()
    broker_order_id = transport.submit_order_with_broker_id(request)

    import pytest

    with pytest.raises(RuntimeError, match="Potential Pattern Day Trade"):
        transport.wait_for_fill_report(broker_order_id, timeout_seconds=1)


def test_ib_async_order_execution_transport_records_submitted_order_mapping() -> None:
    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        OrderIntent,
        OrderSide,
        OrderType,
    )
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.transports.ib_async_order_execution_transport import (
        IbAsyncOrderExecutionTransport,
        IbAsyncOrderExecutionTransportConfig,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderContractSpec
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    order_map = BrokerOrderMap()
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
    fake_ib = _FakeIb()
    transport = IbAsyncOrderExecutionTransport(
        config=IbAsyncOrderExecutionTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            timeout_seconds=1,
        ),
        sink=adapter,
        ib_factory=lambda: fake_ib,
    )
    request = adapter.to_order_request(
        OrderIntent(
            order_id=OrderId("ord-001"),
            account_id=AccountId("acct-ibkr"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        ),
        client_order_id="client-ord-001",
        strategy_id=StrategyId("strategy-ibkr"),
        order_type=OrderType.LIMIT,
        limit_price=Decimal("101.25"),
        contract=IbkrOrderContractSpec.stock("AAPL", primary_exchange="ISLAND"),
    )

    transport.connect()
    broker_order_id = transport.submit_order_with_broker_id(request)

    record = order_map.by_ibkr_order_id(broker_order_id)
    assert record.internal_order_id == OrderId("ord-001")
    assert record.client_order_id == "client-ord-001"
    assert record.account_id == AccountId("acct-ibkr")
    assert record.strategy_id == StrategyId("strategy-ibkr")
    assert fake_ib.placed_orders[0].orderRef == "client-ord-001"


@dataclass(slots=True)
class _FakeContract:
    symbol: str


@dataclass(slots=True)
class _FakeOrder:
    action: str
    totalQuantity: Decimal
    orderType: str
    lmtPrice: float | None = None
    account: str = ""
    tif: str = "DAY"
    orderRef: str = ""
    outsideRth: bool = False
    orderId: int = 77


@dataclass(slots=True)
class _FakeOrderStatus:
    status: str = "Submitted"


@dataclass(slots=True)
class _FakeExecution:
    execId: str = "exec-001"
    orderId: int = 77
    shares: float = 1
    price: float = 101.25


@dataclass(slots=True)
class _FakeCommissionReport:
    execId: str = "exec-001"
    commission: float = 1.23
    currency: str = "USD"


@dataclass(slots=True)
class _FakeFill:
    execution: _FakeExecution = field(default_factory=_FakeExecution)
    commissionReport: _FakeCommissionReport = field(default_factory=_FakeCommissionReport)


@dataclass(slots=True)
class _FakeTrade:
    contract: _FakeContract
    order: _FakeOrder
    orderStatus: _FakeOrderStatus = field(default_factory=_FakeOrderStatus)
    fills: list[_FakeFill] = field(default_factory=list)


@dataclass(slots=True)
class _FakeIb:
    connected: bool = False
    placed_orders: list[_FakeOrder] = field(default_factory=list)
    qualified_contracts: list[str] = field(default_factory=list)
    error_on_place: tuple[int, str] | None = None
    errorEvent: _FakeEvent = field(default_factory=lambda: _FakeEvent())

    def connect(self, host: str, port: int, clientId: int, timeout: float) -> None:
        del host, port, clientId, timeout
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def isConnected(self) -> bool:
        return self.connected

    def managedAccounts(self) -> list[str]:
        return ["DU1234567"]

    def qualifyContracts(self, contract: _FakeContract) -> list[_FakeContract]:
        self.qualified_contracts.append(contract.symbol)
        return [contract]

    def placeOrder(self, contract: _FakeContract, order: _FakeOrder) -> _FakeTrade:
        order.orderId = 77
        self.placed_orders.append(order)
        if self.error_on_place is not None:
            code, message = self.error_on_place
            self.errorEvent.emit(77, code, message, contract)
            return _FakeTrade(contract=contract, order=order, fills=[])
        return _FakeTrade(contract=contract, order=order, fills=[_FakeFill()])

    def cancelOrder(self, order: _FakeOrder) -> _FakeTrade:
        return _FakeTrade(contract=_FakeContract(symbol="AAPL"), order=order)

    def sleep(self, seconds: float) -> None:
        del seconds


@dataclass(slots=True)
class _FakeEvent:
    handlers: list[Callable[..., None]] = field(default_factory=list)

    def __iadd__(self, handler: Callable[..., None]) -> _FakeEvent:
        self.handlers.append(handler)
        return self

    def emit(self, *args: object) -> None:
        for handler in self.handlers:
            handler(*args)
