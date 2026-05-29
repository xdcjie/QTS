"""Market data actor MVP."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import tzinfo

from qts.core.ids import InstrumentId
from qts.data.bars.pipeline import BarAggregationPipeline
from qts.data.bars.timeframe import Timeframe
from qts.data.events import MarketDataSubscription
from qts.data.interfaces import MarketDataAdapter
from qts.data.sessions import RegularSessionWindow
from qts.data.subscriptions import (
    LogicalSubscription,
    LogicalSubscriptionKey,
    PhysicalSubscriptionKey,
    SourceStreamType,
    logical_key,
    plan_physical_subscription,
)
from qts.domain.market_data import Bar, Quote, Tick
from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorUnhandledMessageError
from qts.runtime.actor_ref import ActorRef

MarketDataPayload = Bar | Quote | Tick


@dataclass(frozen=True, slots=True)
class MarketDataEvent:
    """Normalized market data payload accepted by MarketDataActor."""

    payload: MarketDataPayload


@dataclass(frozen=True, slots=True)
class SubscribeMarketData:
    """Message requesting strategy market data fan-out."""

    subscriber_id: str
    subscriber_ref: ActorRef
    instrument_id: InstrumentId
    timeframe: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.subscriber_id.strip():
            raise ValueError("subscriber_id must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")


class MarketDataActor(Actor):
    """Actor boundary for normalized market data events."""

    def __init__(
        self,
        subscribers: Iterable[ActorRef] = (),
        *,
        aggregate_timeframe: str | None = None,
        exchange_timezone: str | tzinfo | None = None,
        session_window: RegularSessionWindow | None = None,
        feed: MarketDataAdapter | None = None,
    ) -> None:
        """Perform __init__."""
        self._subscribers = tuple(subscribers)
        self._target_timeframe = (
            Timeframe.parse(aggregate_timeframe) if aggregate_timeframe is not None else None
        )
        if (self._target_timeframe is not None or feed is not None) and exchange_timezone is None:
            raise ValueError("exchange_timezone is required when aggregate_timeframe is set")
        self._exchange_timezone = exchange_timezone
        self._feed = feed
        self._aggregation_pipeline = (
            BarAggregationPipeline(exchange_timezone, session_window=session_window)
            if exchange_timezone is not None
            else None
        )
        self._logical_subscribers: dict[LogicalSubscriptionKey, dict[str, ActorRef]] = {}
        self._source_timeframe_by_logical: dict[LogicalSubscriptionKey, str] = {}
        self._physical_subscriptions: set[PhysicalSubscriptionKey] = set()

    def handle(self, message: object) -> None:
        """Perform handle."""
        if isinstance(message, SubscribeMarketData):
            self._subscribe(message)
            return
        if isinstance(message, MarketDataEvent):
            if self._logical_subscribers:
                self._publish_to_logical_subscribers(message.payload)
                return
            if isinstance(message.payload, Bar) and self._target_timeframe is not None:
                if self._aggregation_pipeline is None:
                    raise RuntimeError("bar aggregation is not configured")
                result = self._aggregation_pipeline.aggregate(
                    message.payload, self._target_timeframe
                )
                for completed in result:
                    self._publish(completed)
                return
            self._publish(message.payload)
            return
        raise ActorUnhandledMessageError(
            f"unsupported market data message: {type(message).__name__}"
        )

    @property
    def logical_subscription_count(self) -> int:
        """Perform logical_subscription_count."""
        return len(self._logical_subscribers)

    @property
    def physical_subscription_count(self) -> int:
        """Perform physical_subscription_count."""
        return len(self._physical_subscriptions)

    def _subscribe(self, message: SubscribeMarketData) -> None:
        """Perform _subscribe."""
        subscription = LogicalSubscription(
            subscriber_id=message.subscriber_id,
            instrument_id=message.instrument_id,
            requested_timeframe=message.timeframe,
        )
        key = logical_key(subscription)
        subscribers = self._logical_subscribers.setdefault(key, {})
        subscribers[subscription.subscriber_id] = message.subscriber_ref

        if self._feed is None:
            self._source_timeframe_by_logical.setdefault(key, subscription.requested_timeframe)
            return

        physical_key = plan_physical_subscription(
            subscription,
            capabilities=self._feed.capabilities,
        )
        self._source_timeframe_by_logical[key] = physical_key.source_timeframe
        if physical_key in self._physical_subscriptions:
            return
        self._feed.subscribe(
            MarketDataSubscription(
                subscription_id=self._subscription_id(physical_key),
                instrument_id=physical_key.instrument_id,
                timeframe=physical_key.source_timeframe,
            )
        )
        self._physical_subscriptions.add(physical_key)

    def _publish_to_logical_subscribers(self, payload: MarketDataPayload) -> None:
        """Perform _publish_to_logical_subscribers."""
        if not isinstance(payload, Bar):
            self._publish(payload)
            return

        for key, subscribers in self._logical_subscribers.items():
            if key.stream_type is not SourceStreamType.BAR:
                continue
            if key.instrument_id != payload.instrument_id:
                continue
            source_timeframe = self._source_timeframe_by_logical[key]
            if key.requested_timeframe == payload.timeframe:
                self._publish_to(subscribers.values(), payload)
                continue
            if source_timeframe != payload.timeframe:
                continue
            if self._aggregation_pipeline is None:
                raise RuntimeError("bar aggregation is not configured")
            result = self._aggregation_pipeline.aggregate_logical(
                payload,
                source_timeframe=source_timeframe,
                target_timeframe=key.requested_timeframe,
            )
            for completed in result:
                self._publish_to(subscribers.values(), completed)

    def _publish(self, payload: MarketDataPayload) -> None:
        """Perform _publish."""
        for subscriber in self._subscribers:
            subscriber.tell(payload)

    @staticmethod
    def _publish_to(subscribers: Iterable[ActorRef], payload: MarketDataPayload) -> None:
        """Perform _publish_to."""
        for subscriber in subscribers:
            subscriber.tell(payload)

    @staticmethod
    def _subscription_id(key: PhysicalSubscriptionKey) -> str:
        """Perform _subscription_id."""
        return ":".join(
            (
                key.source_id,
                key.instrument_id.value,
                key.stream_type.value,
                key.source_timeframe,
            )
        )


__all__ = [
    "MarketDataActor",
    "MarketDataEvent",
    "MarketDataPayload",
    "SubscribeMarketData",
]
