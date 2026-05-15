"""Shared market-data source adapter interfaces."""

from __future__ import annotations

from typing import Protocol

from qts.data.capabilities import MarketDataFeedCapabilities
from qts.data.events import MarketDataSubscribed, MarketDataSubscription


class StreamingFeedAdapter(Protocol):
    """Protocol for stream-oriented market-data providers."""

    @property
    def capabilities(self) -> MarketDataFeedCapabilities:
        """Return source capabilities."""
        ...

    def subscribe(self, subscription: MarketDataSubscription) -> MarketDataSubscribed:
        """Subscribe one source stream."""
        ...


class MarketDataAdapter(Protocol):
    """Canonical market-data source adapter contract for shared data boundaries."""

    @property
    def capabilities(self) -> MarketDataFeedCapabilities:
        """Return source capabilities."""
        ...

    def subscribe(self, subscription: MarketDataSubscription) -> MarketDataSubscribed:
        """Subscribe one source stream."""
        ...


__all__ = ["StreamingFeedAdapter", "MarketDataAdapter"]
