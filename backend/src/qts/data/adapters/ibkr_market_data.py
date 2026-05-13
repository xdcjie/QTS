"""IBKR market data adapter skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.data.adapters.ibkr_transport import IbkrBarPayload, IbkrQuotePayload, IbkrTickPayload
from qts.domain.market_data import Bar, Quote, Tick
from qts.registry.broker_symbol_mapping import BrokerSymbolMapping


@dataclass(frozen=True, slots=True)
class IbkrMarketDataConnection:
    """IBKR market data connection settings."""

    host: str
    port: int
    client_id: int
    source_id: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if self.client_id <= 0:
            raise ValueError("client_id must be positive")
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrMarketDataSubscription:
    """IBKR market data subscription request at the adapter boundary."""

    instrument_id: InstrumentId
    broker_symbol: str
    source_id: str


class IbkrMarketDataAdapter:
    """Normalizes IBKR market data without owning order execution."""

    def __init__(
        self,
        *,
        connection: IbkrMarketDataConnection,
        symbol_mapping: BrokerSymbolMapping,
    ) -> None:
        """Perform __init__."""
        self.connection = connection
        self._symbol_mapping = symbol_mapping

    def subscription_for(self, instrument_id: InstrumentId) -> IbkrMarketDataSubscription:
        """Perform subscription_for."""
        return IbkrMarketDataSubscription(
            instrument_id=instrument_id,
            broker_symbol=self._symbol_mapping.to_broker_symbol(instrument_id),
            source_id=self.connection.source_id,
        )

    def normalize_tick(
        self,
        *,
        broker_symbol: str,
        time: datetime,
        price: Decimal,
        size: Decimal = Decimal("0"),
    ) -> Tick:
        """Perform normalize_tick."""
        return Tick(
            instrument_id=self._symbol_mapping.to_instrument_id(broker_symbol),
            time=time,
            price=price,
            size=size,
        )

    def on_tick(self, payload: IbkrTickPayload) -> Tick:
        """Normalize a raw IBKR tick transport callback."""

        return self.normalize_tick(
            broker_symbol=payload.broker_symbol,
            time=payload.time,
            price=payload.price,
            size=payload.size,
        )

    def normalize_quote(
        self,
        *,
        broker_symbol: str,
        time: datetime,
        bid_price: Decimal,
        ask_price: Decimal,
        bid_size: Decimal = Decimal("0"),
        ask_size: Decimal = Decimal("0"),
    ) -> Quote:
        """Perform normalize_quote."""
        return Quote(
            instrument_id=self._symbol_mapping.to_instrument_id(broker_symbol),
            time=time,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=bid_size,
            ask_size=ask_size,
        )

    def on_quote(self, payload: IbkrQuotePayload) -> Quote:
        """Normalize a raw IBKR quote transport callback."""

        return self.normalize_quote(
            broker_symbol=payload.broker_symbol,
            time=payload.time,
            bid_price=payload.bid_price,
            ask_price=payload.ask_price,
            bid_size=payload.bid_size,
            ask_size=payload.ask_size,
        )

    def normalize_bar(
        self,
        *,
        broker_symbol: str,
        start_time: datetime,
        end_time: datetime,
        timeframe: str,
        session_id: str,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal = Decimal("0"),
        vwap: Decimal | None = None,
        open_interest: Decimal | None = None,
        trade_count: int | None = None,
        is_complete: bool = False,
        is_partial: bool = False,
    ) -> Bar:
        """Perform normalize_bar."""
        return Bar(
            instrument_id=self._symbol_mapping.to_instrument_id(broker_symbol),
            start_time=start_time,
            end_time=end_time,
            timeframe=timeframe,
            session_id=session_id,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            vwap=vwap,
            open_interest=open_interest,
            trade_count=trade_count,
            is_complete=is_complete,
            is_partial=is_partial,
        )

    def on_bar(self, payload: IbkrBarPayload) -> Bar:
        """Normalize a raw IBKR bar transport callback."""

        return self.normalize_bar(
            broker_symbol=payload.broker_symbol,
            start_time=payload.start_time,
            end_time=payload.end_time,
            timeframe=payload.timeframe,
            session_id=payload.session_id,
            open=payload.open,
            high=payload.high,
            low=payload.low,
            close=payload.close,
            volume=payload.volume,
            vwap=payload.vwap,
            open_interest=payload.open_interest,
            trade_count=payload.trade_count,
            is_complete=payload.is_complete,
            is_partial=payload.is_partial,
        )


# Canonicalized names used by higher-level documentation and mode-independent paths.
LiveMarketDataAdapter = IbkrMarketDataAdapter
LiveMarketDataConnection = IbkrMarketDataConnection
LiveMarketDataSubscription = IbkrMarketDataSubscription


__all__ = [
    "IbkrMarketDataAdapter",
    "IbkrMarketDataConnection",
    "IbkrMarketDataSubscription",
    "LiveMarketDataAdapter",
    "LiveMarketDataConnection",
    "LiveMarketDataSubscription",
]
