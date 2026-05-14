"""Historical market data source adapter."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from qts.data.historical.csv_dataset import iter_historical_bars
from qts.data.live import (
    FeedCapabilities,
    FeedSubscription,
    LiveFeedEvent,
    MarketDataSubscribed,
)
from qts.registry.symbol_resolution import SourceSymbolResolver


@dataclass(slots=True)
class HistoricalMarketDataAdapter:
    """Deterministic historical market data adapter with feed-like contracts."""

    source_id: str
    csv_path: Path
    symbol_resolver: SourceSymbolResolver
    source_timeframe: str
    start: datetime | None = None
    end: datetime | None = None
    _subscriptions: dict[str, FeedSubscription] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.source_timeframe.strip():
            raise ValueError("source_timeframe must not be empty")

    @property
    def capabilities(self) -> FeedCapabilities:
        """Perform capabilities."""
        return FeedCapabilities(
            source_id=self.source_id,
            supports_ticks=False,
            supports_quotes=False,
            supports_bars=True,
            supported_timeframes=frozenset({self.source_timeframe}),
        )

    def subscribe(self, subscription: FeedSubscription) -> MarketDataSubscribed:
        """Perform subscribe."""
        self.capabilities.source_timeframe_for(subscription.timeframe)
        self._subscriptions[subscription.subscription_id] = subscription
        return MarketDataSubscribed(subscription=subscription, source_id=self.source_id)

    def events(self, subscription_id: str) -> Iterator[LiveFeedEvent]:
        """Perform events."""
        if not subscription_id.strip():
            raise ValueError("subscription_id must not be empty")
        try:
            subscription = self._subscriptions[subscription_id]
        except KeyError as exc:
            raise KeyError(subscription_id) from exc
        stream = iter_historical_bars(
            self.csv_path,
            self.symbol_resolver,
            timeframe=self.source_timeframe,
            start=self.start,
            end=self.end,
        )
        for bar in stream:
            if bar.instrument_id == subscription.instrument_id:
                yield LiveFeedEvent(payload=bar, source_id=self.source_id)


__all__ = ["HistoricalMarketDataAdapter"]
