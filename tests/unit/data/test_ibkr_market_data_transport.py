from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from threading import Event
from typing import TYPE_CHECKING, Any

import pytest

from tests.support.ibkr_transports import requires_official_ibapi

if TYPE_CHECKING:
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrBarPayload,
        IbkrMarketDataCallbackSink,
        IbkrQuotePayload,
        IbkrTickPayload,
    )
    from qts.domain.market_data import Bar, Quote, Tick


def test_ibkr_market_data_transport_dispatches_raw_callbacks_to_adapter() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrBarPayload,
        IbkrMarketDataTransport,
        IbkrQuotePayload,
        IbkrTickPayload,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    fake_transport = _FakeMarketDataTransport(sink=adapter)
    transport: IbkrMarketDataTransport = fake_transport

    transport.connect()
    tick = transport.emit_tick(
        IbkrTickPayload(
            broker_symbol="AAPL",
            time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            price=Decimal("101.25"),
            size=Decimal("10"),
        )
    )
    quote = transport.emit_quote(
        IbkrQuotePayload(
            broker_symbol="AAPL",
            time=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
            bid_price=Decimal("101.20"),
            ask_price=Decimal("101.30"),
            bid_size=Decimal("20"),
            ask_size=Decimal("30"),
        )
    )
    bar = transport.emit_bar(
        IbkrBarPayload(
            broker_symbol="AAPL",
            start_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            end_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal("101.00"),
            high=Decimal("101.50"),
            low=Decimal("100.90"),
            close=Decimal("101.25"),
            volume=Decimal("1000"),
            is_complete=True,
        )
    )
    transport.disconnect()

    assert tick.instrument_id == instrument_id
    assert quote.instrument_id == instrument_id
    assert bar.instrument_id == instrument_id
    assert bar.is_complete
    assert not fake_transport.connected


@requires_official_ibapi
def test_ibkr_tws_market_data_transport_builds_stock_contract_and_normalizes_tick() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrMarketDataContractSpec,
        IbkrTwsMarketDataTransport,
        IbkrTwsMarketDataTransportConfig,
    )
    from qts.domain.market_data import Tick
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    contract_spec = IbkrMarketDataContractSpec.stock("AAPL", primary_exchange="ISLAND")
    contract = contract_spec.to_ibapi_contract()
    transport = IbkrTwsMarketDataTransport(
        config=IbkrTwsMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
        ),
        sink=adapter,
    )

    transport.register_market_data_request(77, broker_symbol="AAPL")
    tick = transport.handle_tick_price(77, tick_type=4, price=101.25)

    assert contract.symbol == "AAPL"
    assert contract.secType == "STK"
    assert contract.exchange == "SMART"
    assert contract.primaryExchange == "ISLAND"
    assert contract.currency == "USD"
    assert isinstance(tick, Tick)
    assert tick.instrument_id == instrument_id
    assert tick.price == Decimal("101.25")


def test_ibkr_tws_market_data_transport_waits_through_transient_connectivity_status() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrTwsMarketDataTransport,
        IbkrTwsMarketDataTransportConfig,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    transport = IbkrTwsMarketDataTransport(
        config=IbkrTwsMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
        ),
        sink=adapter,
    )
    transport.register_market_data_request(77, broker_symbol="AAPL")
    transport.handle_error(
        request_id=-1,
        code=2110,
        message="Connectivity between TWS and server is broken. It will be restored automatically.",
    )
    transport.handle_tick_price(77, tick_type=4, price=101.25)

    tick = transport.wait_for_event(timeout_seconds=1)

    from qts.domain.market_data import Tick

    assert isinstance(tick, Tick)
    assert tick.instrument_id == instrument_id
    assert tick.price == Decimal("101.25")


def test_ibkr_tws_market_data_transport_permission_error_fails_fast() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrTwsMarketDataTransport,
        IbkrTwsMarketDataTransportConfig,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    transport = IbkrTwsMarketDataTransport(
        config=IbkrTwsMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
        ),
        sink=adapter,
    )
    transport.handle_error(
        request_id=77,
        code=10167,
        message="Requested market data is not subscribed. Delayed market data is available.",
    )

    with pytest.raises(RuntimeError, match="permission"):
        transport.wait_for_event(timeout_seconds=1)


def test_ibkr_tws_market_data_transport_pacing_violation_enters_backoff() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrMarketDataContractSpec,
        IbkrTwsMarketDataTransport,
        IbkrTwsMarketDataTransportConfig,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    transport = IbkrTwsMarketDataTransport(
        config=IbkrTwsMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            pacing_backoff_seconds=30,
        ),
        sink=adapter,
    )
    transport._app = _MarketDataReconnectApp()
    transport.handle_error(request_id=77, code=420, message="pacing violation")

    with pytest.raises(RuntimeError, match="pacing backoff"):
        transport.subscribe_market_data(IbkrMarketDataContractSpec.stock("AAPL"))


def test_ibkr_tws_market_data_transport_ignores_late_ticks_after_unsubscribe() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrTwsMarketDataTransport,
        IbkrTwsMarketDataTransportConfig,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    transport = IbkrTwsMarketDataTransport(
        config=IbkrTwsMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
        ),
        sink=adapter,
    )
    transport.register_market_data_request(77, broker_symbol="AAPL")
    transport._request_symbols.pop(77)

    assert transport.handle_tick_price(77, tick_type=4, price=101.25) is None


@requires_official_ibapi
def test_ibkr_tws_market_data_transport_resubscribes_active_requests_after_reconnect() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrMarketDataContractSpec,
        IbkrTwsMarketDataTransport,
        IbkrTwsMarketDataTransportConfig,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    first_app = _MarketDataReconnectApp()
    transport = IbkrTwsMarketDataTransport(
        config=IbkrTwsMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            market_data_type=1,
        ),
        sink=adapter,
    )
    transport._app = first_app
    contract = IbkrMarketDataContractSpec.stock("AAPL", primary_exchange="ISLAND")
    req_id = transport.subscribe_market_data(contract, generic_ticks="233")
    transport.disconnect()
    second_app = _MarketDataReconnectApp()
    transport._app = second_app

    transport.resubscribe_market_data()

    assert first_app.cancelled == [req_id]
    assert second_app.market_data_types == [1]
    [(resub_req_id, resub_contract, generic_ticks, snapshot)] = second_app.requests
    assert resub_req_id == req_id
    assert resub_contract.symbol == "AAPL"
    assert generic_ticks == "233"
    assert snapshot is False
    assert transport.handle_tick_price(req_id, tick_type=4, price=101.25) is not None


def test_ibkr_tws_market_data_transport_bounds_blocking_ibapi_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrTwsMarketDataTransport,
        IbkrTwsMarketDataTransportConfig,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    app = _BlockingConnectApp()
    monkeypatch.setattr(
        "qts.data.transports.ibkr_tws_market_data_transport._new_market_data_app", lambda owner: app
    )
    transport = IbkrTwsMarketDataTransport(
        config=IbkrTwsMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            timeout_seconds=0.01,
        ),
        sink=adapter,
    )

    with pytest.raises(TimeoutError, match="timed out connecting"):
        transport.connect()

    assert app.disconnect_called
    assert not transport.connected


@dataclass(slots=True)
class _FakeMarketDataTransport:
    sink: IbkrMarketDataCallbackSink
    connected: bool = False

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def emit_tick(self, payload: IbkrTickPayload) -> Tick:
        return self.sink.on_tick(payload)

    def emit_quote(self, payload: IbkrQuotePayload) -> Quote:
        return self.sink.on_quote(payload)

    def emit_bar(self, payload: IbkrBarPayload) -> Bar:
        return self.sink.on_bar(payload)


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
class _MarketDataReconnectApp:
    requests: list[tuple[int, Any, str, bool]] = field(default_factory=list)
    cancelled: list[int] = field(default_factory=list)
    market_data_types: list[int] = field(default_factory=list)
    disconnected: bool = False

    def isConnected(self) -> bool:
        return not self.disconnected

    def reqMarketDataType(self, market_data_type: int) -> None:
        self.market_data_types.append(market_data_type)

    def reqMktData(
        self,
        req_id: int,
        contract: object,
        generic_ticks: str,
        snapshot: bool,
        regulatory_snapshot: bool,
        options: list[object],
    ) -> None:
        del regulatory_snapshot, options
        self.requests.append((req_id, contract, generic_ticks, snapshot))

    def cancelMktData(self, req_id: int) -> None:
        self.cancelled.append(req_id)

    def disconnect(self) -> None:
        self.disconnected = True
