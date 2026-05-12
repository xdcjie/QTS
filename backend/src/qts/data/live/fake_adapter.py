"""Test-oriented fake live feed adapter."""

from __future__ import annotations

from .adapter import LiveFeedAdapter
from .capabilities import FeedCapabilities
from .events import (
    FeedSubscription,
    LiveFeedEvent,
    LiveFeedFailure,
    LiveFeedPayload,
    LiveFeedSubscribed,
)


class FakeLiveFeedAdapter(LiveFeedAdapter):
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
        """Return adapter capabilities."""
        return self._capabilities or FeedCapabilities(source_id=self._source_id)

    @property
    def subscription_count(self) -> int:
        """Return current active subscription count."""
        return len(self._subscriptions)

    def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed:
        """Accept a new subscription and acknowledge it."""
        self._subscriptions[subscription.subscription_id] = subscription
        return LiveFeedSubscribed(subscription=subscription, source_id=self._source_id)

    def emit(self, payload: LiveFeedPayload) -> LiveFeedEvent:
        """Emit a typed live feed event."""
        return LiveFeedEvent(payload=payload, source_id=self._source_id)

    def fail(self, subscription_id: str, *, reason: str) -> LiveFeedFailure:
        """Create a failure event for a tracked subscription."""
        if subscription_id not in self._subscriptions:
            raise KeyError(subscription_id)
        return LiveFeedFailure(
            subscription_id=subscription_id,
            source_id=self._source_id,
            reason=reason,
        )


class FakeMarketDataAdapter(FakeLiveFeedAdapter):
    """Canonical fake adapter name used for market-data source tests."""


__all__ = ["FakeLiveFeedAdapter", "FakeMarketDataAdapter"]
