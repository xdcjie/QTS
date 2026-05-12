"""Adapter protocols for live and replay market data feeds."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from .capabilities import FeedCapabilities
from .events import FeedSubscription, LiveFeedEvent, LiveFeedSubscribed


class LiveFeedAdapter(Protocol):
    """Live market data feed adapter boundary."""

    @property
    def capabilities(self) -> FeedCapabilities:
        """Return feed capabilities."""
        ...

    def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed:
        """Subscribe to a live feed stream."""
        ...


class MarketDataAdapter(Protocol):
    """Canonical market-data source adapter contract shared by live and replay feeds."""

    @property
    def capabilities(self) -> FeedCapabilities:
        """Return feed capabilities."""
        ...

    def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed:
        """Subscribe to a source stream."""
        ...


class ReplayMarketDataAdapter(Protocol):
    """Canonical replay market-data adapter contract for historical sources."""

    @property
    def capabilities(self) -> FeedCapabilities:
        """Return feed capabilities."""
        ...

    def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed:
        """Subscribe to a replay stream."""
        ...

    def events(self, subscription_id: str) -> Iterator[LiveFeedEvent]:
        """Iterate replay events for a subscription."""
        ...


__all__ = [
    "LiveFeedAdapter",
    "MarketDataAdapter",
    "ReplayMarketDataAdapter",
]
