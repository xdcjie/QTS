"""Adapter protocols for streaming market data feeds."""

from __future__ import annotations

from typing import Protocol

from .capabilities import FeedCapabilities
from .events import FeedSubscription, MarketDataSubscribed


class LiveFeedAdapter(Protocol):
    """Live market data feed adapter boundary."""

    @property
    def capabilities(self) -> FeedCapabilities:
        """Return feed capabilities."""
        ...

    def subscribe(self, subscription: FeedSubscription) -> MarketDataSubscribed:
        """Subscribe to a live feed stream."""
        ...


class MarketDataAdapter(Protocol):
    """Canonical market-data source adapter contract."""

    @property
    def capabilities(self) -> FeedCapabilities:
        """Return feed capabilities."""
        ...

    def subscribe(self, subscription: FeedSubscription) -> MarketDataSubscribed:
        """Subscribe to a source stream."""
        ...


__all__ = [
    "LiveFeedAdapter",
    "MarketDataAdapter",
]
