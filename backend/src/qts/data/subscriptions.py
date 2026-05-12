"""Market data subscription planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from qts.core.ids import InstrumentId
from qts.data.live_feed import FeedCapabilities


class SourceStreamType(StrEnum):
    """Physical market data stream type."""

    BAR = "bar"
    TICK = "tick"
    QUOTE = "quote"


@dataclass(frozen=True, slots=True)
class LogicalSubscription:
    """Strategy-requested market data stream."""

    subscriber_id: str
    instrument_id: InstrumentId
    requested_timeframe: str
    stream_type: SourceStreamType = SourceStreamType.BAR

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.subscriber_id.strip():
            raise ValueError("subscriber_id must not be empty")
        if not self.requested_timeframe.strip():
            raise ValueError("requested_timeframe must not be empty")


@dataclass(frozen=True, slots=True)
class LogicalSubscriptionKey:
    """Deduplication key for strategy-facing subscribers."""

    instrument_id: InstrumentId
    requested_timeframe: str
    stream_type: SourceStreamType = SourceStreamType.BAR


@dataclass(frozen=True, slots=True)
class PhysicalSubscriptionKey:
    """Deduplication key for provider-facing subscriptions."""

    source_id: str
    instrument_id: InstrumentId
    stream_type: SourceStreamType
    source_timeframe: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.source_timeframe.strip():
            raise ValueError("source_timeframe must not be empty")


def logical_key(subscription: LogicalSubscription) -> LogicalSubscriptionKey:
    """Return the logical fan-out key for a subscription."""

    return LogicalSubscriptionKey(
        instrument_id=subscription.instrument_id,
        requested_timeframe=subscription.requested_timeframe,
        stream_type=subscription.stream_type,
    )


def plan_physical_subscription(
    subscription: LogicalSubscription,
    *,
    capabilities: FeedCapabilities,
) -> PhysicalSubscriptionKey:
    """Map one logical subscription to its provider source subscription."""

    if subscription.stream_type is not SourceStreamType.BAR:
        raise ValueError("only bar subscriptions are supported")
    return PhysicalSubscriptionKey(
        source_id=capabilities.source_id,
        instrument_id=subscription.instrument_id,
        stream_type=subscription.stream_type,
        source_timeframe=capabilities.source_timeframe_for(subscription.requested_timeframe),
    )


__all__ = [
    "LogicalSubscription",
    "LogicalSubscriptionKey",
    "PhysicalSubscriptionKey",
    "SourceStreamType",
    "logical_key",
    "plan_physical_subscription",
]
