"""Live market data feed boundary contracts and fake adapter."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Protocol

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar, Quote, Tick

LiveFeedPayload = Bar | Quote | Tick


@dataclass(frozen=True, slots=True)
class FeedCapabilities:
    """Feed-supported live market data features."""

    source_id: str
    supports_ticks: bool = True
    supports_quotes: bool = True
    supports_bars: bool = True
    max_subscriptions: int | None = None
    supported_timeframes: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if self.max_subscriptions is not None and self.max_subscriptions <= 0:
            raise ValueError("max_subscriptions must be positive")
        if any(not item.strip() for item in self.supported_timeframes):
            raise ValueError("supported_timeframes must not contain empty values")

    def supports_timeframe(self, timeframe: str) -> bool:
        """Perform supports_timeframe."""
        if not timeframe.strip():
            raise ValueError("timeframe must not be empty")
        return not self.supported_timeframes or timeframe in self.supported_timeframes

    def source_timeframe_for(self, requested_timeframe: str) -> str:
        """Return the provider timeframe needed to satisfy a requested bar stream."""

        requested = requested_timeframe.strip()
        if not requested:
            raise ValueError("requested_timeframe must not be empty")
        if not self.supports_bars:
            raise ValueError(f"source {self.source_id} does not support bars")
        if self.supports_timeframe(requested):
            return requested
        if "5s" in self.supported_timeframes and requested in {
            "1m",
            "5m",
            "15m",
            "30m",
            "1h",
            "4h",
        }:
            return "5s"
        if "1m" in self.supported_timeframes and requested in {
            "5m",
            "15m",
            "30m",
            "1h",
            "4h",
        }:
            return "1m"
        raise ValueError(
            f"requested timeframe {requested} cannot be derived from source {self.source_id}"
        )


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
class LiveFeedSubscribed:
    """Successful live feed subscription acknowledgement."""

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


@dataclass(frozen=True, slots=True)
class ReconnectPolicy:
    """Deterministic reconnect backoff policy."""

    initial_delay: timedelta
    multiplier: Decimal
    max_delay: timedelta
    max_attempts: int

    def __post_init__(self) -> None:
        if self.initial_delay <= timedelta(0):
            raise ValueError("initial_delay must be positive")
        if self.multiplier < Decimal("1"):
            raise ValueError("multiplier must be at least 1")
        if self.max_delay < self.initial_delay:
            raise ValueError("max_delay must be >= initial_delay")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")

    def delay_for_attempt(self, attempt: int) -> timedelta | None:
        """Perform delay_for_attempt."""
        if attempt <= 0:
            raise ValueError("attempt must be positive")
        if attempt > self.max_attempts:
            return None
        seconds = self.initial_delay.total_seconds() * float(self.multiplier ** (attempt - 1))
        return min(timedelta(seconds=seconds), self.max_delay)


class LiveFeedAdapter(Protocol):
    """Live market data feed adapter boundary."""

    @property
    def capabilities(self) -> FeedCapabilities:
        """Return feed capabilities."""
        ...

    def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed:
        """Subscribe to a live feed stream."""
        ...


MarketDataSourceCapabilities = FeedCapabilities
MarketDataSourceSubscription = FeedSubscription
MarketDataSourceSubscribed = LiveFeedSubscribed
MarketDataSourceEvent = LiveFeedEvent
MarketDataSourceFailure = LiveFeedFailure


class MarketDataSourceAdapter(Protocol):
    """Canonical market-data source adapter contract shared by live and replay feeds."""

    @property
    def capabilities(self) -> MarketDataSourceCapabilities:
        """Return feed capabilities."""
        ...

    def subscribe(
        self,
        subscription: MarketDataSourceSubscription,
    ) -> MarketDataSourceSubscribed:
        """Subscribe to a source stream."""
        ...


class ReplayMarketDataAdapter(Protocol):
    """Canonical replay market-data adapter contract for historical sources."""

    @property
    def capabilities(self) -> MarketDataSourceCapabilities:
        """Return feed capabilities."""
        ...

    def subscribe(
        self,
        subscription: MarketDataSourceSubscription,
    ) -> MarketDataSourceSubscribed:
        """Subscribe to a replay stream."""
        ...

    def events(self, subscription_id: str) -> Iterator[MarketDataSourceEvent]:
        """Iterate replay events for a subscription."""
        ...


class MarketDataAdapter(MarketDataSourceAdapter, LiveFeedAdapter):
    """Canonical adapter name for live and replay source implementations."""


class FakeLiveFeedAdapter:
    """Deterministic fake live market data feed."""

    def __init__(
        self,
        *,
        source_id: str,
        capabilities: FeedCapabilities | None = None,
    ) -> None:
        if not source_id.strip():
            raise ValueError("source_id must not be empty")
        if capabilities is not None and capabilities.source_id != source_id:
            raise ValueError("capabilities source_id must match adapter source_id")
        self._source_id = source_id
        self._capabilities = capabilities
        self._subscriptions: dict[str, FeedSubscription] = {}

    @property
    def capabilities(self) -> FeedCapabilities:
        """Perform capabilities."""
        return self._capabilities or FeedCapabilities(source_id=self._source_id)

    @property
    def subscription_count(self) -> int:
        """Perform subscription_count."""
        return len(self._subscriptions)

    def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed:
        """Perform subscribe."""
        self._subscriptions[subscription.subscription_id] = subscription
        return LiveFeedSubscribed(subscription=subscription, source_id=self._source_id)

    def emit(self, payload: LiveFeedPayload) -> LiveFeedEvent:
        """Perform emit."""
        return LiveFeedEvent(payload=payload, source_id=self._source_id)

    def fail(self, subscription_id: str, *, reason: str) -> LiveFeedFailure:
        """Perform fail."""
        if subscription_id not in self._subscriptions:
            raise KeyError(subscription_id)
        return LiveFeedFailure(
            subscription_id=subscription_id,
            source_id=self._source_id,
            reason=reason,
        )


class FakeMarketDataAdapter(FakeLiveFeedAdapter):
    """Canonical fake adapter name used for market-data source tests."""


__all__ = [
    "FakeMarketDataAdapter",
    "MarketDataAdapter",
    "MarketDataSourceAdapter",
    "MarketDataSourceCapabilities",
    "MarketDataSourceEvent",
    "MarketDataSourceFailure",
    "MarketDataSourceSubscribed",
    "MarketDataSourceSubscription",
    "ReplayMarketDataAdapter",
    "FakeLiveFeedAdapter",
    "FeedCapabilities",
    "FeedSubscription",
    "LiveFeedAdapter",
    "LiveFeedEvent",
    "LiveFeedFailure",
    "LiveFeedPayload",
    "LiveFeedSubscribed",
    "ReconnectPolicy",
]
