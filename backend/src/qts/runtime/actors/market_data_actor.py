"""Market data actor MVP."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import tzinfo

from qts.core.ids import InstrumentId
from qts.data.bars.aggregator import BarAggregator
from qts.data.bars.timeframe import Timeframe
from qts.data.live_feed import FeedSubscription, LiveFeedAdapter
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
        feed: LiveFeedAdapter | None = None,
    ) -> None:
        self._subscribers = tuple(subscribers)
        self._target_timeframe = (
            Timeframe.parse(aggregate_timeframe) if aggregate_timeframe is not None else None
        )
        if (self._target_timeframe is not None or feed is not None) and exchange_timezone is None:
            raise ValueError("exchange_timezone is required when aggregate_timeframe is set")
        self._exchange_timezone = exchange_timezone
        self._feed = feed
        self._aggregators: dict[tuple[object, ...], BarAggregator] = {}
        self._logical_subscribers: dict[LogicalSubscriptionKey, dict[str, ActorRef]] = {}
        self._source_timeframe_by_logical: dict[LogicalSubscriptionKey, str] = {}
        self._physical_subscriptions: set[PhysicalSubscriptionKey] = set()

    def handle(self, message: object) -> None:
        if isinstance(message, SubscribeMarketData):
            self._subscribe(message)
            return
        if isinstance(message, MarketDataEvent):
            if self._logical_subscribers:
                self._publish_to_logical_subscribers(message.payload)
                return
            if isinstance(message.payload, Bar) and self._target_timeframe is not None:
                aggregator = self._aggregator_for(message.payload)
                result = aggregator.update(message.payload)
                for completed in result.completed:
                    self._publish(completed)
                return
            self._publish(message.payload)
            return
        raise TypeError(f"unsupported market data message: {type(message).__name__}")

    @property
    def logical_subscription_count(self) -> int:
        return len(self._logical_subscribers)

    @property
    def physical_subscription_count(self) -> int:
        return len(self._physical_subscriptions)

    def _subscribe(self, message: SubscribeMarketData) -> None:
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
            FeedSubscription(
                subscription_id=_subscription_id(physical_key),
                instrument_id=physical_key.instrument_id,
                timeframe=physical_key.source_timeframe,
            )
        )
        self._physical_subscriptions.add(physical_key)

    def _publish_to_logical_subscribers(self, payload: MarketDataPayload) -> None:
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
                _publish_to(subscribers.values(), payload)
                continue
            if source_timeframe != payload.timeframe:
                continue
            aggregator = self._logical_aggregator_for(
                payload,
                source_timeframe=source_timeframe,
                target_timeframe=key.requested_timeframe,
            )
            result = aggregator.update(payload)
            for completed in result.completed:
                _publish_to(subscribers.values(), completed)

    def _aggregator_for(self, bar: Bar) -> BarAggregator:
        if self._target_timeframe is None or self._exchange_timezone is None:
            raise RuntimeError("bar aggregation is not configured")
        key = (bar.instrument_id, str(self._target_timeframe), bar.session_id)
        aggregator = self._aggregators.get(key)
        if aggregator is None:
            aggregator = BarAggregator(
                target_timeframe=self._target_timeframe,
                exchange_timezone=self._exchange_timezone,
            )
            self._aggregators[key] = aggregator
        return aggregator

    def _logical_aggregator_for(
        self,
        bar: Bar,
        *,
        source_timeframe: str,
        target_timeframe: str,
    ) -> BarAggregator:
        if self._exchange_timezone is None:
            raise RuntimeError("bar aggregation is not configured")
        key = (bar.instrument_id, source_timeframe, target_timeframe, bar.session_id)
        aggregator = self._aggregators.get(key)
        if aggregator is None:
            aggregator = BarAggregator(
                target_timeframe=Timeframe.parse(target_timeframe),
                exchange_timezone=self._exchange_timezone,
            )
            self._aggregators[key] = aggregator
        return aggregator

    def _publish(self, payload: MarketDataPayload) -> None:
        for subscriber in self._subscribers:
            subscriber.tell(payload)


def _publish_to(subscribers: Iterable[ActorRef], payload: MarketDataPayload) -> None:
    for subscriber in subscribers:
        subscriber.tell(payload)


def _subscription_id(key: PhysicalSubscriptionKey) -> str:
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
