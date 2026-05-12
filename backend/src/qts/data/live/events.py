"""Live feed subscription and event DTOs."""

from __future__ import annotations

from dataclasses import dataclass

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar, Quote, Tick

LiveFeedPayload = Bar | Quote | Tick


@dataclass(frozen=True, slots=True)
class FeedSubscription:
    """Internal live feed subscription request."""

    subscription_id: str
    instrument_id: InstrumentId
    timeframe: str

    def __post_init__(self) -> None:
        if not self.subscription_id.strip():
            raise ValueError("subscription_id must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")


@dataclass(frozen=True, slots=True)
class MarketDataSubscribed:
    """Successful market-data source subscription acknowledgement."""

    subscription: FeedSubscription
    source_id: str


@dataclass(frozen=True, slots=True)
class LiveFeedEvent:
    """Live feed payload emitted by a subscription."""

    payload: LiveFeedPayload
    source_id: str


@dataclass(frozen=True, slots=True)
class LiveFeedFailure:
    """Live feed failure notification."""

    subscription_id: str
    source_id: str
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("reason must not be empty")


__all__ = [
    "FeedSubscription",
    "MarketDataSubscribed",
    "LiveFeedEvent",
    "LiveFeedFailure",
    "LiveFeedPayload",
]

LiveFeedSubscribed = MarketDataSubscribed
