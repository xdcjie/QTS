"""IBKR market-data transport boundary contracts."""

from __future__ import annotations

import queue
import threading
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import IntEnum
from importlib import import_module
from time import monotonic
from typing import Any, Protocol

from qts.core.time import Clock, SystemClock
from qts.domain.market_data import Bar, Quote, Tick

_BID_PRICE_TICK_TYPES = frozenset({1, 66})
_ASK_PRICE_TICK_TYPES = frozenset({2, 67})
_LAST_PRICE_TICK_TYPES = frozenset({4, 68})
_BID_SIZE_TICK_TYPES = frozenset({0, 69})
_ASK_SIZE_TICK_TYPES = frozenset({3, 70})
_LAST_SIZE_TICK_TYPES = frozenset({5, 71})
_IBKR_INFO_ERROR_CODES = frozenset(
    {
        1100,
        1101,
        1102,
        1104,
        2103,
        2104,
        2105,
        2106,
        2107,
        2108,
        2110,
        2119,
        2157,
        2158,
    }
)
_IBKR_PERMISSION_ERROR_CODES = frozenset({354, 10167, 10168})
_IBKR_PACING_ERROR_CODES = frozenset({100, 420})
_DEFAULT_REALTIME_BAR_SECONDS = 5


class IbkrProviderMarketDataType(IntEnum):
    """IBKR provider market data type codes."""

    LIVE = 1
    FROZEN = 2
    DELAYED = 3
    DELAYED_FROZEN = 4


@dataclass(frozen=True, slots=True)
class IbkrMarketDataContractSpec:
    """IBKR contract fields required for market-data requests."""

    broker_symbol: str
    security_type: str
    exchange: str
    currency: str
    primary_exchange: str | None = None

    def __post_init__(self) -> None:
        if not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")
        if not self.security_type.strip():
            raise ValueError("security_type must not be empty")
        if not self.exchange.strip():
            raise ValueError("exchange must not be empty")
        if not self.currency.strip():
            raise ValueError("currency must not be empty")
        if self.primary_exchange is not None and not self.primary_exchange.strip():
            raise ValueError("primary_exchange must not be empty when provided")

    @classmethod
    def stock(
        cls,
        broker_symbol: str,
        *,
        exchange: str = "SMART",
        currency: str = "USD",
        primary_exchange: str | None = None,
    ) -> IbkrMarketDataContractSpec:
        """Create a stock contract spec for an IBKR broker symbol."""

        return cls(
            broker_symbol=broker_symbol,
            security_type="STK",
            exchange=exchange,
            currency=currency,
            primary_exchange=primary_exchange,
        )

    def to_ibapi_contract(self) -> Any:
        """Return an official ibapi Contract object for this spec."""

        contract_class = _ibapi_attr("ibapi.contract", "Contract")
        contract = contract_class()
        contract.symbol = self.broker_symbol
        contract.secType = self.security_type
        contract.exchange = self.exchange
        contract.currency = self.currency
        if self.primary_exchange is not None:
            contract.primaryExchange = self.primary_exchange
        return contract


@dataclass(frozen=True, slots=True)
class IbkrTwsMarketDataTransportConfig:
    """IBKR TWS/Gateway market-data transport settings."""

    host: str
    port: int
    client_id: int
    timeout_seconds: float = 20.0
    market_data_type: int = 3
    pacing_backoff_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if self.client_id <= 0:
            raise ValueError("client_id must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.pacing_backoff_seconds <= 0:
            raise ValueError("pacing_backoff_seconds must be positive")
        if self.market_data_type not in {1, 2, 3, 4}:
            raise ValueError("market_data_type must be one of 1, 2, 3, or 4")


@dataclass(frozen=True, slots=True)
class IbkrTickPayload:
    """Raw IBKR tick callback payload at the market-data boundary."""

    broker_symbol: str
    time: datetime
    price: Decimal
    size: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrQuotePayload:
    """Raw IBKR top-of-book callback payload at the market-data boundary."""

    broker_symbol: str
    time: datetime
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal = Decimal("0")
    ask_size: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrBarPayload:
    """Raw IBKR bar callback payload at the market-data boundary."""

    broker_symbol: str
    start_time: datetime
    end_time: datetime
    timeframe: str
    session_id: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")
    vwap: Decimal | None = None
    open_interest: Decimal | None = None
    trade_count: int | None = None
    is_complete: bool = False
    is_partial: bool = False

    def __post_init__(self) -> None:
        if not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if not self.session_id.strip():
            raise ValueError("session_id must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrMarketDataErrorPayload:
    """Raw IBKR market-data error callback payload."""

    request_id: int
    code: int
    message: str

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("message must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrMarketDataTypePayload:
    """Raw IBKR marketDataType callback payload."""

    request_id: int
    market_data_type: int

    def __post_init__(self) -> None:
        if self.market_data_type not in set(IbkrProviderMarketDataType):
            raise ValueError("market_data_type must be one of 1, 2, 3, or 4")


class IbkrMarketDataCallbackSink(Protocol):
    """IBKR market-data callback sink owned by the market-data adapter."""

    def on_tick(self, payload: IbkrTickPayload) -> Tick:
        """Normalize a raw IBKR tick callback."""
        ...

    def on_quote(self, payload: IbkrQuotePayload) -> Quote:
        """Normalize a raw IBKR quote callback."""
        ...

    def on_bar(self, payload: IbkrBarPayload) -> Bar:
        """Normalize a raw IBKR bar callback."""
        ...

    def on_market_data_type(self, payload: IbkrMarketDataTypePayload) -> object:
        """Normalize a raw marketDataType callback."""
        ...


class IbkrMarketDataTransport(Protocol):
    """Transport interface for IBKR market-data connectivity."""

    @property
    def connected(self) -> bool:
        """Return whether the transport is connected."""
        ...

    def connect(self) -> None:
        """Connect the market-data transport."""
        ...

    def disconnect(self) -> None:
        """Disconnect the market-data transport."""
        ...

    def emit_tick(self, payload: IbkrTickPayload) -> Tick:
        """Dispatch a raw tick callback to the adapter sink."""
        ...

    def emit_quote(self, payload: IbkrQuotePayload) -> Quote:
        """Dispatch a raw quote callback to the adapter sink."""
        ...

    def emit_bar(self, payload: IbkrBarPayload) -> Bar:
        """Dispatch a raw bar callback to the adapter sink."""
        ...


@dataclass(slots=True)
class _IbkrQuoteState:
    bid_price: Decimal | None = None
    ask_price: Decimal | None = None
    bid_size: Decimal = Decimal("0")
    ask_size: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class _IbkrMarketDataActiveRequest:
    contract: IbkrMarketDataContractSpec
    generic_ticks: str
    snapshot: bool


class IbkrTwsMarketDataTransport:
    """Official IBKR TWS API transport for paper/live market data."""

    def __init__(
        self,
        *,
        config: IbkrTwsMarketDataTransportConfig,
        sink: IbkrMarketDataCallbackSink,
        clock: Clock | None = None,
    ) -> None:
        self.config = config
        self._sink = sink
        self._clock = clock if clock is not None else SystemClock()
        self._app: Any | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._events: queue.Queue[Tick | Quote | Bar] = queue.Queue()
        self._errors: queue.Queue[IbkrMarketDataErrorPayload] = queue.Queue()
        self._seen_errors: list[IbkrMarketDataErrorPayload] = []
        self._request_symbols: dict[int, str] = {}
        self._active_requests: dict[int, _IbkrMarketDataActiveRequest] = {}
        self._quote_state: dict[int, _IbkrQuoteState] = {}
        self._last_sizes: dict[int, Decimal] = {}
        self._next_req_id = 1
        self._pacing_backoff_deadline: float | None = None

    @property
    def connected(self) -> bool:
        """Return whether the IBKR client is connected."""

        app = self._app
        return bool(app is not None and app.isConnected())

    def connect(self) -> None:
        """Connect to TWS/Gateway and wait until the API session is ready."""

        if self.connected:
            return
        self._ready.clear()
        app = _new_market_data_app(self)
        self._app = app
        try:
            _connect_ibapi_app(
                app,
                host=self.config.host,
                port=self.config.port,
                client_id=self.config.client_id,
                timeout_seconds=self.config.timeout_seconds,
            )
            self._thread = threading.Thread(
                target=app.run,
                name=f"qts-ibkr-md-{self.config.client_id}",
                daemon=True,
            )
            self._thread.start()
            if self._ready.wait(self.config.timeout_seconds):
                return
        except Exception:
            self.disconnect()
            raise
        self.disconnect()
        raise TimeoutError("timed out waiting for IBKR market-data API readiness")

    def disconnect(self) -> None:
        """Disconnect from TWS/Gateway."""

        app = self._app
        if app is not None:
            for req_id in tuple(self._request_symbols):
                with suppress(Exception):
                    app.cancelMktData(req_id)
            app.disconnect()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)
        self._app = None
        self._thread = None
        self._ready.clear()
        self._request_symbols.clear()
        self._quote_state.clear()
        self._last_sizes.clear()

    def subscribe_market_data(
        self,
        contract: IbkrMarketDataContractSpec,
        *,
        generic_ticks: str = "",
        snapshot: bool = False,
    ) -> int:
        """Subscribe to streaming market data and return the IBKR request id."""

        self._raise_if_pacing_backoff_active()
        self._raise_fatal_error_if_any()
        app = self._require_connected_app()
        req_id = self._next_req_id
        self._next_req_id += 1
        self.register_market_data_request(req_id, broker_symbol=contract.broker_symbol)
        app.reqMarketDataType(self.config.market_data_type)
        app.reqMktData(req_id, contract.to_ibapi_contract(), generic_ticks, snapshot, False, [])
        self._active_requests[req_id] = _IbkrMarketDataActiveRequest(
            contract=contract,
            generic_ticks=generic_ticks,
            snapshot=snapshot,
        )
        return req_id

    def unsubscribe_market_data(self, req_id: int) -> None:
        """Cancel a streaming market-data subscription."""

        app = self._require_connected_app()
        app.cancelMktData(req_id)
        self._active_requests.pop(req_id, None)
        self._request_symbols.pop(req_id, None)
        self._quote_state.pop(req_id, None)
        self._last_sizes.pop(req_id, None)

    def resubscribe_market_data(self) -> None:
        """Restore active market-data subscriptions after reconnect."""

        app = self._require_connected_app()
        for req_id, request in sorted(self._active_requests.items()):
            self.register_market_data_request(
                req_id,
                broker_symbol=request.contract.broker_symbol,
            )
            app.reqMarketDataType(self.config.market_data_type)
            app.reqMktData(
                req_id,
                request.contract.to_ibapi_contract(),
                request.generic_ticks,
                request.snapshot,
                False,
                [],
            )

    def collect_first_event(
        self,
        contract: IbkrMarketDataContractSpec,
        *,
        timeout_seconds: float | None = None,
    ) -> Tick | Quote | Bar:
        """Subscribe and return the first normalized market-data event."""

        req_id = self.subscribe_market_data(contract)
        try:
            return self.wait_for_event(timeout_seconds=timeout_seconds)
        finally:
            if self.connected and req_id in self._request_symbols:
                self.unsubscribe_market_data(req_id)

    def wait_for_event(self, *, timeout_seconds: float | None = None) -> Tick | Quote | Bar:
        """Wait for the next normalized market-data event."""

        timeout = timeout_seconds or self.config.timeout_seconds
        deadline = monotonic() + timeout
        while True:
            self._raise_fatal_error_if_any()
            remaining = deadline - monotonic()
            if remaining <= 0:
                details = "; ".join(_format_error(error) for error in self._seen_errors)
                suffix = f" IBKR errors: {details}" if details else ""
                raise TimeoutError(f"timed out waiting for IBKR market data.{suffix}")
            try:
                return self._events.get(timeout=min(0.25, remaining))
            except queue.Empty:
                continue

    def register_market_data_request(self, req_id: int, *, broker_symbol: str) -> None:
        """Register the broker symbol for an IBKR request id."""

        if req_id <= 0:
            raise ValueError("req_id must be positive")
        if not broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")
        self._request_symbols[req_id] = broker_symbol
        self._quote_state.setdefault(req_id, _IbkrQuoteState())

    def handle_tick_price(
        self, req_id: int, *, tick_type: int, price: float
    ) -> Tick | Quote | None:
        """Handle an IBKR tickPrice callback."""

        if price <= 0 or req_id not in self._request_symbols:
            return None
        value = _to_decimal(price)
        if tick_type in _LAST_PRICE_TICK_TYPES:
            return self.emit_tick(
                IbkrTickPayload(
                    broker_symbol=self._broker_symbol_for(req_id),
                    time=self._clock.now(),
                    price=value,
                    size=self._last_sizes.get(req_id, Decimal("0")),
                )
            )
        if tick_type in _BID_PRICE_TICK_TYPES:
            state = self._quote_state.setdefault(req_id, _IbkrQuoteState())
            state.bid_price = value
            return self._maybe_emit_quote(req_id, state)
        if tick_type in _ASK_PRICE_TICK_TYPES:
            state = self._quote_state.setdefault(req_id, _IbkrQuoteState())
            state.ask_price = value
            return self._maybe_emit_quote(req_id, state)
        return None

    def handle_tick_size(self, req_id: int, *, tick_type: int, size: Decimal) -> Quote | None:
        """Handle an IBKR tickSize callback."""

        if size < Decimal("0") or req_id not in self._request_symbols:
            return None
        if tick_type in _LAST_SIZE_TICK_TYPES:
            self._last_sizes[req_id] = size
            return None
        state = self._quote_state.setdefault(req_id, _IbkrQuoteState())
        if tick_type in _BID_SIZE_TICK_TYPES:
            state.bid_size = size
        elif tick_type in _ASK_SIZE_TICK_TYPES:
            state.ask_size = size
        else:
            return None
        return self._maybe_emit_quote(req_id, state)

    def handle_realtime_bar(
        self,
        req_id: int,
        *,
        epoch_seconds: int,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: Decimal,
        wap: Decimal,
        count: int,
    ) -> Bar:
        """Handle an IBKR realtimeBar callback."""

        start_time = datetime.fromtimestamp(epoch_seconds, tz=UTC)
        return self.emit_bar(
            IbkrBarPayload(
                broker_symbol=self._broker_symbol_for(req_id),
                start_time=start_time,
                end_time=start_time + timedelta(seconds=_DEFAULT_REALTIME_BAR_SECONDS),
                timeframe="5s",
                session_id=start_time.date().isoformat(),
                open=_to_decimal(open_price),
                high=_to_decimal(high_price),
                low=_to_decimal(low_price),
                close=_to_decimal(close_price),
                volume=volume,
                vwap=wap,
                trade_count=count,
                is_complete=True,
            )
        )

    def handle_error(
        self,
        *,
        request_id: int,
        code: int,
        message: str,
    ) -> None:
        """Record an IBKR transport error callback."""

        if message.strip():
            if code in _IBKR_PACING_ERROR_CODES:
                self._enter_pacing_backoff()
            self._errors.put(
                IbkrMarketDataErrorPayload(request_id=request_id, code=code, message=message)
            )

    def handle_market_data_type(self, *, request_id: int, market_data_type: int) -> object:
        """Handle an IBKR marketDataType callback."""

        return self._sink.on_market_data_type(
            IbkrMarketDataTypePayload(
                request_id=request_id,
                market_data_type=market_data_type,
            )
        )

    def mark_ready(self) -> None:
        """Mark the API client as ready after nextValidId."""

        self._ready.set()

    def emit_tick(self, payload: IbkrTickPayload) -> Tick:
        """Dispatch a raw tick callback to the adapter sink."""

        tick = self._sink.on_tick(payload)
        self._events.put(tick)
        return tick

    def emit_quote(self, payload: IbkrQuotePayload) -> Quote:
        """Dispatch a raw quote callback to the adapter sink."""

        quote = self._sink.on_quote(payload)
        self._events.put(quote)
        return quote

    def emit_bar(self, payload: IbkrBarPayload) -> Bar:
        """Dispatch a raw bar callback to the adapter sink."""

        bar = self._sink.on_bar(payload)
        self._events.put(bar)
        return bar

    def _require_connected_app(self) -> Any:
        app = self._app
        if app is None or not app.isConnected():
            raise RuntimeError("IBKR market-data transport is not connected")
        return app

    def _broker_symbol_for(self, req_id: int) -> str:
        try:
            return self._request_symbols[req_id]
        except KeyError as exc:
            raise KeyError(f"unknown IBKR market-data request id: {req_id}") from exc

    def _maybe_emit_quote(self, req_id: int, state: _IbkrQuoteState) -> Quote | None:
        if state.bid_price is None or state.ask_price is None:
            return None
        return self.emit_quote(
            IbkrQuotePayload(
                broker_symbol=self._broker_symbol_for(req_id),
                time=self._clock.now(),
                bid_price=state.bid_price,
                ask_price=state.ask_price,
                bid_size=state.bid_size,
                ask_size=state.ask_size,
            )
        )

    def _raise_fatal_error_if_any(self) -> None:
        while True:
            try:
                error = self._errors.get_nowait()
            except queue.Empty:
                return
            self._seen_errors.append(error)
            if error.code in _IBKR_PERMISSION_ERROR_CODES:
                raise RuntimeError(f"IBKR market-data permission error: {_format_error(error)}")
            if error.code in _IBKR_PACING_ERROR_CODES:
                self._enter_pacing_backoff()
                raise RuntimeError(f"IBKR market-data pacing violation: {_format_error(error)}")
            if error.code not in _IBKR_INFO_ERROR_CODES:
                raise RuntimeError(f"IBKR market-data error: {_format_error(error)}")

    def _enter_pacing_backoff(self) -> None:
        self._pacing_backoff_deadline = monotonic() + self.config.pacing_backoff_seconds

    def _raise_if_pacing_backoff_active(self) -> None:
        deadline = self._pacing_backoff_deadline
        if deadline is None:
            return
        remaining = deadline - monotonic()
        if remaining > 0:
            raise RuntimeError(f"IBKR market-data pacing backoff is active for {remaining:.3f}s")
        self._pacing_backoff_deadline = None


__all__ = [
    "IbkrBarPayload",
    "IbkrMarketDataCallbackSink",
    "IbkrMarketDataContractSpec",
    "IbkrMarketDataErrorPayload",
    "IbkrMarketDataTransport",
    "IbkrMarketDataTypePayload",
    "IbkrProviderMarketDataType",
    "IbkrQuotePayload",
    "IbkrTickPayload",
    "IbkrTwsMarketDataTransport",
    "IbkrTwsMarketDataTransportConfig",
]


def _new_market_data_app(owner: IbkrTwsMarketDataTransport) -> Any:
    wrapper_class = _ibapi_attr("ibapi.wrapper", "EWrapper")
    client_class = _ibapi_attr("ibapi.client", "EClient")

    def __init__(self: Any) -> None:
        wrapper_class.__init__(self)
        client_class.__init__(self, self)

    def connect_ack(self: Any) -> None:
        pass

    def next_valid_id(self: Any, order_id: int) -> None:
        del order_id
        owner.mark_ready()

    def tick_price(self: Any, req_id: int, tick_type: int, price: float, attrib: Any) -> None:
        del attrib
        owner.handle_tick_price(req_id, tick_type=tick_type, price=price)

    def tick_size(self: Any, req_id: int, tick_type: int, size: Decimal) -> None:
        owner.handle_tick_size(req_id, tick_type=tick_type, size=size)

    def realtime_bar(
        self: Any,
        req_id: int,
        epoch_seconds: int,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: Decimal,
        wap: Decimal,
        count: int,
    ) -> None:
        owner.handle_realtime_bar(
            req_id,
            epoch_seconds=epoch_seconds,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            wap=wap,
            count=count,
        )

    def market_data_type(self: Any, req_id: int, market_data_type: int) -> None:
        owner.handle_market_data_type(request_id=req_id, market_data_type=market_data_type)

    def error(
        self: Any,
        req_id: int,
        error_time: int,
        error_code: int,
        error_string: str,
        advanced_order_reject_json: str = "",
    ) -> None:
        del error_time, advanced_order_reject_json
        owner.handle_error(request_id=req_id, code=error_code, message=error_string)

    app_class = type(
        "_QtsIbkrMarketDataApp",
        (wrapper_class, client_class),
        {
            "__init__": __init__,
            "connectAck": connect_ack,
            "nextValidId": next_valid_id,
            "tickPrice": tick_price,
            "tickSize": tick_size,
            "realtimeBar": realtime_bar,
            "marketDataType": market_data_type,
            "error": error,
        },
    )
    return app_class()


def _ibapi_attr(module_name: str, attribute_name: str) -> Any:
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "official IBKR TWS Python API package is required; install ibapi from "
            "the Interactive Brokers TWS API download"
        ) from exc
    return getattr(module, attribute_name)


def _connect_ibapi_app(
    app: Any,
    *,
    host: str,
    port: int,
    client_id: int,
    timeout_seconds: float,
) -> None:
    errors: list[BaseException] = []

    def connect() -> None:
        try:
            app.connect(host, port, client_id)
        except BaseException as exc:  # pragma: no cover - re-raised on caller thread
            errors.append(exc)

    thread = threading.Thread(
        target=connect,
        name=f"qts-ibkr-connect-{client_id}",
        daemon=True,
    )
    thread.start()
    thread.join(timeout_seconds)
    if thread.is_alive():
        with suppress(Exception):
            app.disconnect()
        thread.join(timeout=1)
        raise TimeoutError("timed out connecting to IBKR API")
    if errors:
        raise errors[0]


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _format_error(error: IbkrMarketDataErrorPayload) -> str:
    return f"request_id={error.request_id} code={error.code} message={error.message}"
