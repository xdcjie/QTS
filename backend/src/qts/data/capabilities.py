"""Shared market-data capability contracts.

Shared contracts are defined here so provider-specific packages (including
`qts.data.live`) do not become protocol owners.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from qts.data.bars.timeframe import AlignmentMode, Timeframe

LiveFeedTimeframeSet = frozenset[str]


@dataclass(frozen=True, slots=True)
class MarketDataFeedCapabilities:
    """Capabilities exposed by a market-data source adapter/transport."""

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
        """Whether the source directly supports the requested timeframe."""
        requested = timeframe.strip()
        if not requested:
            raise ValueError("timeframe must not be empty")
        return not self.supported_timeframes or requested in self.supported_timeframes

    def source_timeframe_for(self, requested_timeframe: str) -> str:
        """Resolve a source timeframe for a requested canonical timeframe."""
        requested = requested_timeframe.strip()
        if not requested:
            raise ValueError("requested_timeframe must not be empty")
        if not self.supports_bars:
            raise ValueError(f"source {self.source_id} does not support bars")
        if self.supports_timeframe(requested):
            return requested
        requested_timeframe_model = Timeframe.parse(requested)
        compatible = sorted(
            (
                source
                for source in self.supported_timeframes
                if self._can_derive(
                    source_timeframe=Timeframe.parse(source),
                    requested_timeframe=requested_timeframe_model,
                )
            ),
            key=self._source_priority,
        )
        if compatible:
            return compatible[0]
        raise ValueError(
            f"requested timeframe {requested} cannot be derived from source {self.source_id}"
        )

    @staticmethod
    def _can_derive(*, source_timeframe: Timeframe, requested_timeframe: Timeframe) -> bool:
        if source_timeframe.alignment is not AlignmentMode.CLOCK:
            return False
        if source_timeframe.duration is None:
            return False
        if requested_timeframe.alignment is AlignmentMode.SESSION:
            return True
        if requested_timeframe.duration is None:
            return False
        return (
            requested_timeframe.duration > source_timeframe.duration
            and requested_timeframe.duration % source_timeframe.duration == timedelta(0)
        )

    @staticmethod
    def _source_priority(source_timeframe: str) -> timedelta:
        parsed = Timeframe.parse(source_timeframe)
        return parsed.duration or timedelta.max


__all__ = ["MarketDataFeedCapabilities", "LiveFeedTimeframeSet"]
