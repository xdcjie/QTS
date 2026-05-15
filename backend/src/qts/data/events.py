"""Shared market-data events and subscription DTOs."""

from __future__ import annotations

from dataclasses import dataclass

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar, Quote, Tick

MarketDataPayload = Bar | Quote | Tick


@dataclass(frozen=True, slots=True)
class MarketDataSubscription:
    """Request to subscribe one logical market-data stream."""

    subscription_id: str
    instrument_id: InstrumentId
    timeframe: str

    def __post_init__(self) -> None:
        if not self.subscription_id.strip():
            raise ValueError("subscription_id must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")


@dataclass(frozen=True, slots=True)
class MarketDataSourceEvent:
    """Market-data payload emitted by a source subscription."""

    payload: MarketDataPayload
    source_id: str


@dataclass(frozen=True, slots=True)
class MarketDataSourceFailure:
    """Market-data failure notification."""

    subscription_id: str
    source_id: str
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("reason must not be empty")


@dataclass(frozen=True, slots=True)
class MarketDataSubscribed:
    """Acknowledgement of a live source subscription."""

    subscription: MarketDataSubscription
    source_id: str


__all__ = [
    "MarketDataPayload",
    "MarketDataSubscription",
    "MarketDataSourceEvent",
    "MarketDataSourceFailure",
    "MarketDataSubscribed",
]
