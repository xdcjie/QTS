"""Deterministic market-data doubles for tests."""

from __future__ import annotations

from qts.data.capabilities import MarketDataFeedCapabilities
from qts.data.events import (
    MarketDataPayload,
    MarketDataSourceEvent,
    MarketDataSourceFailure,
    MarketDataSubscribed,
    MarketDataSubscription,
)
from qts.data.interfaces import StreamingFeedAdapter


class FakeStreamingMarketDataAdapter(StreamingFeedAdapter):
    """Deterministic streaming market-data fake for unit/integration test composition."""

    def __init__(
        self,
        *,
        source_id: str,
        capabilities: MarketDataFeedCapabilities | None = None,
    ) -> None:
        if not source_id.strip():
            raise ValueError("source_id must not be empty")
        if capabilities is not None and capabilities.source_id != source_id:
            raise ValueError("capabilities source_id must match source_id")
        self._source_id = source_id
        self._capabilities = capabilities
        self._subscriptions: dict[str, MarketDataSubscription] = {}

    @property
    def capabilities(self) -> MarketDataFeedCapabilities:
        """Return adapter capabilities."""
        return self._capabilities or MarketDataFeedCapabilities(source_id=self._source_id)

    @property
    def subscription_count(self) -> int:
        """Return the number of active stream subscriptions."""
        return len(self._subscriptions)

    def subscribe(self, subscription: MarketDataSubscription) -> MarketDataSubscribed:
        """Track subscription and acknowledge it."""
        self._subscriptions[subscription.subscription_id] = subscription
        return MarketDataSubscribed(subscription=subscription, source_id=self._source_id)

    def emit(self, payload: MarketDataPayload) -> MarketDataSourceEvent:
        """Emit a deterministic market-data payload."""
        return MarketDataSourceEvent(payload=payload, source_id=self._source_id)

    def fail(
        self,
        subscription_id: str,
        *,
        reason: str,
    ) -> MarketDataSourceFailure:
        """Create a failure event for a tracked subscription."""
        if subscription_id not in self._subscriptions:
            raise KeyError(subscription_id)
        return MarketDataSourceFailure(
            subscription_id=subscription_id,
            source_id=self._source_id,
            reason=reason,
        )


__all__ = [
    "FakeStreamingMarketDataAdapter",
]
