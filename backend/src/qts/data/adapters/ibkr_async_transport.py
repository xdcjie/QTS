"""ib_async-backed IBKR market-data transport."""

from __future__ import annotations

import queue
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from math import isfinite
from time import monotonic
from typing import Any

from qts.data.adapters.ibkr_transport import (
    IbkrMarketDataCallbackSink,
    IbkrMarketDataContractSpec,
    IbkrMarketDataErrorPayload,
    IbkrQuotePayload,
    IbkrTickPayload,
)
from qts.domain.market_data import Bar, Quote, Tick

_IBKR_INFO_ERROR_CODES = frozenset(
    {
        1100,
        1101,
        1102,
        1104,
        10167,
        10168,
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


@dataclass(frozen=True, slots=True)
class IbAsyncMarketDataTransportConfig:
    """IB Gateway market-data settings for an ib_async client."""

    host: str
    port: int
    client_id: int
    timeout_seconds: float = 20.0
    market_data_type: int = 3

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if self.client_id <= 0:
            raise ValueError("client_id must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.market_data_type not in {1, 2, 3, 4}:
            raise ValueError("market_data_type must be one of 1, 2, 3, or 4")


class IbAsyncMarketDataTransport:
    """Collect normalized market-data events through ib_async."""

    def __init__(
        self,
        *,
        config: IbAsyncMarketDataTransportConfig,
        sink: IbkrMarketDataCallbackSink,
        ib_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.config = config
        self._sink = sink
        self._ib_factory = ib_factory or _default_ib_factory
        self._ib: Any | None = None
        self._events: queue.Queue[Tick | Quote | Bar] = queue.Queue()
        self._errors: queue.Queue[IbkrMarketDataErrorPayload] = queue.Queue()
        self._seen_errors: list[IbkrMarketDataErrorPayload] = []
        self._tickers_by_request_id: dict[int, Any] = {}
        self._emitted_snapshots_by_request_id: dict[int, tuple[str, ...]] = {}
        self._next_req_id = 1

    @property
    def connected(self) -> bool:
        """Return whether the underlying ib_async client is connected."""

        ib = self._ib
        return bool(ib is not None and ib.isConnected())

    def connect(self) -> None:
        """Connect to IB Gateway."""

        if self.connected:
            return
        ib = self._ib_factory()
        ib.connect(
            self.config.host,
            self.config.port,
            clientId=self.config.client_id,
            timeout=self.config.timeout_seconds,
        )
        ib.errorEvent += self._on_error
        self._ib = ib

    def disconnect(self) -> None:
        """Disconnect from IB Gateway."""

        ib = self._ib
        if ib is not None:
            for ticker in tuple(self._tickers_by_request_id.values()):
                ib.cancelMktData(ticker.contract)
            ib.disconnect()
        self._ib = None
        self._tickers_by_request_id.clear()
        self._emitted_snapshots_by_request_id.clear()
        while not self._events.empty():
            self._events.get_nowait()
        while not self._errors.empty():
            self._errors.get_nowait()

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
            if req_id in self._tickers_by_request_id and self.connected:
                self.unsubscribe_market_data(req_id)

    def subscribe_market_data(
        self,
        contract: IbkrMarketDataContractSpec,
        *,
        generic_ticks: str = "",
        snapshot: bool = False,
    ) -> int:
        """Subscribe to market data and return an internal request id."""

        ib = self._require_connected_ib()
        ib_contract = _to_ib_async_contract(contract)
        ib_contract = ib.qualifyContracts(ib_contract)[0]
        ib.reqMarketDataType(self.config.market_data_type)
        ticker = ib.reqMktData(ib_contract, generic_ticks, snapshot, False, [])
        req_id = self._next_req_id
        self._next_req_id += 1
        self._tickers_by_request_id[req_id] = ticker
        self._emit_ticker_if_ready(req_id, ticker)
        return req_id

    def unsubscribe_market_data(self, req_id: int) -> None:
        """Cancel a market-data subscription."""

        ticker = self._tickers_by_request_id.pop(req_id)
        self._emitted_snapshots_by_request_id.pop(req_id, None)
        self._require_connected_ib().cancelMktData(ticker.contract)

    def wait_for_event(self, *, timeout_seconds: float | None = None) -> Tick | Quote | Bar:
        """Wait for a normalized market-data event."""

        timeout = timeout_seconds or self.config.timeout_seconds
        deadline = monotonic() + timeout
        while True:
            self._raise_fatal_error_if_any()
            try:
                return self._events.get_nowait()
            except queue.Empty:
                pass
            for req_id, ticker in tuple(self._tickers_by_request_id.items()):
                self._emit_ticker_if_ready(req_id, ticker)
            remaining = deadline - monotonic()
            if remaining <= 0:
                details = "; ".join(_format_error(error) for error in self._seen_errors)
                suffix = f" IBKR errors: {details}" if details else ""
                raise TimeoutError(f"timed out waiting for ib_async market data.{suffix}")
            self._require_connected_ib().sleep(min(0.05, remaining))

    def _emit_ticker_if_ready(self, req_id: int, ticker: Any) -> None:
        bid = getattr(ticker, "bid", None)
        ask = getattr(ticker, "ask", None)
        if _has_price(bid) and _has_price(ask):
            snapshot: tuple[str, ...] = (
                "quote",
                str(bid),
                str(ask),
                str(getattr(ticker, "bidSize", 0) or 0),
                str(getattr(ticker, "askSize", 0) or 0),
            )
            if self._emitted_snapshots_by_request_id.get(req_id) == snapshot:
                return
            self._emitted_snapshots_by_request_id[req_id] = snapshot
            self._events.put(
                self._sink.on_quote(
                    IbkrQuotePayload(
                        broker_symbol=ticker.contract.symbol,
                        time=datetime.now(tz=UTC),
                        bid_price=Decimal(str(bid)),
                        ask_price=Decimal(str(ask)),
                        bid_size=Decimal(str(getattr(ticker, "bidSize", 0) or 0)),
                        ask_size=Decimal(str(getattr(ticker, "askSize", 0) or 0)),
                    )
                )
            )
            return
        last = getattr(ticker, "last", None)
        if _has_price(last):
            snapshot = (
                "tick",
                str(last),
                str(getattr(ticker, "lastSize", 0) or 0),
            )
            if self._emitted_snapshots_by_request_id.get(req_id) == snapshot:
                return
            self._emitted_snapshots_by_request_id[req_id] = snapshot
            self._events.put(
                self._sink.on_tick(
                    IbkrTickPayload(
                        broker_symbol=ticker.contract.symbol,
                        time=datetime.now(tz=UTC),
                        price=Decimal(str(last)),
                        size=Decimal(str(getattr(ticker, "lastSize", 0) or 0)),
                    )
                )
            )

    def _on_error(
        self,
        request_id: int,
        code: int,
        message: str,
        contract: object | None = None,
    ) -> None:
        del contract
        if message.strip():
            self._errors.put(
                IbkrMarketDataErrorPayload(request_id=request_id, code=code, message=message)
            )

    def _raise_fatal_error_if_any(self) -> None:
        while True:
            try:
                error = self._errors.get_nowait()
            except queue.Empty:
                return
            self._seen_errors.append(error)
            if error.code not in _IBKR_INFO_ERROR_CODES:
                raise RuntimeError(f"IBKR ib_async market-data error: {_format_error(error)}")

    def _require_connected_ib(self) -> Any:
        ib = self._ib
        if ib is None or not ib.isConnected():
            raise RuntimeError("ib_async market-data transport is not connected")
        return ib


def _to_ib_async_contract(contract: IbkrMarketDataContractSpec) -> Any:
    from ib_async import Contract, Forex, Stock

    if contract.security_type.upper() == "STK":
        return Stock(
            contract.broker_symbol,
            contract.exchange,
            contract.currency,
            primaryExchange=contract.primary_exchange or "",
        )
    if contract.security_type.upper() == "CASH":
        return Forex(
            symbol=contract.broker_symbol,
            currency=contract.currency,
            exchange=contract.exchange,
        )
    return Contract(
        symbol=contract.broker_symbol,
        secType=contract.security_type,
        exchange=contract.exchange,
        currency=contract.currency,
        primaryExchange=contract.primary_exchange or "",
    )


def _has_price(value: object) -> bool:
    if value is None:
        return False
    try:
        price = float(str(value))
    except (TypeError, ValueError):
        return False
    return isfinite(price) and price > 0


def _format_error(error: IbkrMarketDataErrorPayload) -> str:
    return f"request_id={error.request_id} code={error.code} message={error.message}"


def _default_ib_factory() -> Any:
    from ib_async import IB

    return IB()


__all__ = ["IbAsyncMarketDataTransport", "IbAsyncMarketDataTransportConfig"]
