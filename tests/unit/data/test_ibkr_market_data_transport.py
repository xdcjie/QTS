from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from threading import Event
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from qts.data.adapters.ibkr_transport import (
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
    from qts.data.adapters.ibkr_transport import (
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


def test_ibkr_tws_market_data_transport_builds_stock_contract_and_normalizes_tick() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.adapters.ibkr_transport import (
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
    from qts.data.adapters.ibkr_transport import (
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


def test_ibkr_tws_market_data_transport_ignores_late_ticks_after_unsubscribe() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.adapters.ibkr_transport import (
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


def test_ibkr_tws_market_data_transport_bounds_blocking_ibapi_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.adapters.ibkr_transport import (
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
    monkeypatch.setattr("qts.data.adapters.ibkr_transport._new_market_data_app", lambda owner: app)
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
