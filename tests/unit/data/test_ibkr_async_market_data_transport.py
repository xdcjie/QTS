from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


def test_ib_async_market_data_transport_collects_normalized_quote() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ib_async_market_data_transport import (
        IbAsyncMarketDataTransport,
        IbAsyncMarketDataTransportConfig,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import IbkrMarketDataContractSpec
    from qts.domain.market_data import Quote
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
    fake_ib = _FakeIb()
    transport = IbAsyncMarketDataTransport(
        config=IbAsyncMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            timeout_seconds=1,
            market_data_type=3,
        ),
        sink=adapter,
        ib_factory=lambda: fake_ib,
    )

    transport.connect()
    event = transport.collect_first_event(
        IbkrMarketDataContractSpec.stock("AAPL", primary_exchange="ISLAND"),
        timeout_seconds=1,
    )
    transport.disconnect()

    assert isinstance(event, Quote)
    assert event.instrument_id == instrument_id
    assert event.bid_price == Decimal("101.20")
    assert event.ask_price == Decimal("101.30")
    assert fake_ib.market_data_type == 3
    assert fake_ib.qualified_contracts == ["AAPL"]
    assert fake_ib.cancelled_contracts == ["AAPL"]
    assert not transport.connected


def test_ib_async_market_data_transport_ignores_nan_initial_ticker_values() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ib_async_market_data_transport import (
        IbAsyncMarketDataTransport,
        IbAsyncMarketDataTransportConfig,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import IbkrMarketDataContractSpec
    from qts.domain.market_data import Quote
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
    ticker = _FakeTicker(contract=_FakeContract("AAPL"), bid=float("nan"), ask=float("nan"))
    fake_ib = _FakeIb(tickers=[ticker], sleep_update=ticker)
    transport = IbAsyncMarketDataTransport(
        config=IbAsyncMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            timeout_seconds=1,
            market_data_type=3,
        ),
        sink=adapter,
        ib_factory=lambda: fake_ib,
    )

    transport.connect()
    event = transport.collect_first_event(
        IbkrMarketDataContractSpec.stock("AAPL", primary_exchange="ISLAND"),
        timeout_seconds=1,
    )
    transport.disconnect()

    assert isinstance(event, Quote)
    assert event.instrument_id == instrument_id
    assert event.bid_price == Decimal("101.2")
    assert event.ask_price == Decimal("101.3")


def test_ib_async_market_data_transport_does_not_reemit_unchanged_ticker_snapshot() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ib_async_market_data_transport import (
        IbAsyncMarketDataTransport,
        IbAsyncMarketDataTransportConfig,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import IbkrMarketDataContractSpec
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
    ticker = _FakeTicker(contract=_FakeContract("AAPL"))
    fake_ib = _FakeIb(tickers=[ticker])
    transport = IbAsyncMarketDataTransport(
        config=IbAsyncMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            timeout_seconds=1,
        ),
        sink=adapter,
        ib_factory=lambda: fake_ib,
    )

    transport.connect()
    req_id = transport.subscribe_market_data(
        IbkrMarketDataContractSpec.stock("AAPL", primary_exchange="ISLAND")
    )
    first = transport.wait_for_event(timeout_seconds=1)

    import pytest

    with pytest.raises(TimeoutError, match="timed out waiting for ib_async market data"):
        transport.wait_for_event(timeout_seconds=0.01)

    transport.unsubscribe_market_data(req_id)
    transport.disconnect()

    assert first.instrument_id == instrument_id


def test_ib_async_market_data_transport_stamps_events_with_injected_clock() -> None:
    from datetime import UTC

    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ib_async_market_data_transport import (
        IbAsyncMarketDataTransport,
        IbAsyncMarketDataTransportConfig,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import IbkrMarketDataContractSpec
    from qts.domain.market_data import Quote
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
    fake_ib = _FakeIb()
    fixed = datetime(2026, 5, 30, 14, 30, tzinfo=UTC)
    transport = IbAsyncMarketDataTransport(
        config=IbAsyncMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            timeout_seconds=1,
            market_data_type=3,
        ),
        sink=adapter,
        ib_factory=lambda: fake_ib,
        clock=_FixedClock(fixed),
    )

    transport.connect()
    event = transport.collect_first_event(
        IbkrMarketDataContractSpec.stock("AAPL", primary_exchange="ISLAND"),
        timeout_seconds=1,
    )
    transport.disconnect()

    assert isinstance(event, Quote)
    assert event.time == fixed


def test_ib_async_market_data_transport_raises_broker_error() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ib_async_market_data_transport import (
        IbAsyncMarketDataTransport,
        IbAsyncMarketDataTransportConfig,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import IbkrMarketDataContractSpec
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
    ticker = _FakeTicker(
        contract=_FakeContract("AAPL"),
        bid=float("nan"),
        ask=float("nan"),
    )
    fake_ib = _FakeIb(
        tickers=[ticker],
        error_on_sleep=(354, "Requested market data is not subscribed"),
    )
    transport = IbAsyncMarketDataTransport(
        config=IbAsyncMarketDataTransportConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            timeout_seconds=1,
        ),
        sink=adapter,
        ib_factory=lambda: fake_ib,
    )

    transport.connect()
    transport.subscribe_market_data(
        IbkrMarketDataContractSpec.stock("AAPL", primary_exchange="ISLAND")
    )

    import pytest

    with pytest.raises(RuntimeError, match="code=354.*Requested market data is not subscribed"):
        transport.wait_for_event(timeout_seconds=1)


@dataclass(slots=True)
class _FixedClock:
    instant: datetime

    def now(self) -> datetime:
        return self.instant


@dataclass(slots=True)
class _FakeContract:
    symbol: str


@dataclass(slots=True)
class _FakeTicker:
    contract: _FakeContract
    bid: float = 101.20
    ask: float = 101.30
    bidSize: float = 20
    askSize: float = 30
    last: float = -1
    lastSize: float = 0


@dataclass(slots=True)
class _FakeIb:
    connected: bool = False
    market_data_type: int | None = None
    qualified_contracts: list[str] = field(default_factory=list)
    cancelled_contracts: list[str] = field(default_factory=list)
    tickers: list[_FakeTicker] = field(default_factory=list)
    sleep_update: _FakeTicker | None = None
    error_on_sleep: tuple[int, str] | None = None
    errorEvent: _FakeEvent = field(default_factory=lambda: _FakeEvent())

    def connect(self, host: str, port: int, clientId: int, timeout: float) -> None:
        del host, port, clientId, timeout
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def isConnected(self) -> bool:
        return self.connected

    def reqMarketDataType(self, market_data_type: int) -> None:
        self.market_data_type = market_data_type

    def qualifyContracts(self, contract: _FakeContract) -> list[_FakeContract]:
        self.qualified_contracts.append(contract.symbol)
        return [contract]

    def reqMktData(
        self,
        contract: _FakeContract,
        genericTickList: str = "",
        snapshot: bool = False,
        regulatorySnapshot: bool = False,
        mktDataOptions: list[Any] | None = None,
    ) -> _FakeTicker:
        del genericTickList, snapshot, regulatorySnapshot, mktDataOptions
        if self.tickers:
            return self.tickers.pop(0)
        return _FakeTicker(contract=contract)

    def cancelMktData(self, contract: _FakeContract) -> None:
        self.cancelled_contracts.append(contract.symbol)

    def sleep(self, seconds: float) -> None:
        del seconds
        if self.error_on_sleep is not None:
            code, message = self.error_on_sleep
            self.error_on_sleep = None
            self.errorEvent.emit(-1, code, message, None)
        if self.sleep_update is not None:
            self.sleep_update.bid = 101.20
            self.sleep_update.ask = 101.30
            self.sleep_update = None


@dataclass(slots=True)
class _FakeEvent:
    handlers: list[Callable[..., None]] = field(default_factory=list)

    def __iadd__(self, handler: Callable[..., None]) -> _FakeEvent:
        self.handlers.append(handler)
        return self

    def emit(self, *args: object) -> None:
        for handler in self.handlers:
            handler(*args)
