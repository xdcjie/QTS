"""Live feed capability model."""

from __future__ import annotations

from dataclasses import dataclass

LiveFeedTimeframeSet = frozenset[str]


@dataclass(frozen=True, slots=True)
class FeedCapabilities:
    """Feed-supported live market data capabilities."""

    source_id: str
    supports_ticks: bool = True
    supports_quotes: bool = True
    supports_bars: bool = True
    max_subscriptions: int | None = None
    supported_timeframes: LiveFeedTimeframeSet = frozenset()

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if self.max_subscriptions is not None and self.max_subscriptions <= 0:
            raise ValueError("max_subscriptions must be positive")
        if any(not item.strip() for item in self.supported_timeframes):
            raise ValueError("supported_timeframes must not contain empty values")

    def supports_timeframe(self, timeframe: str) -> bool:
        """Return whether the requested timeframe is directly supported."""
        if not timeframe.strip():
            raise ValueError("timeframe must not be empty")
        return not self.supported_timeframes or timeframe in self.supported_timeframes

    def source_timeframe_for(self, requested_timeframe: str) -> str:
        """Return provider timeframe used to fulfill a requested timeframe."""
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


__all__ = ["FeedCapabilities", "LiveFeedTimeframeSet"]
