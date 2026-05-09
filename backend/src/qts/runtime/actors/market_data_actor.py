"""Market data actor MVP."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import tzinfo

from qts.data.bars.aggregator import BarAggregator
from qts.data.bars.timeframe import Timeframe
from qts.domain.market_data import Bar, Quote, Tick
from qts.runtime.actor import Actor
from qts.runtime.actor_ref import ActorRef

MarketDataPayload = Bar | Quote | Tick


@dataclass(frozen=True, slots=True)
class MarketDataEvent:
    """Normalized market data payload accepted by MarketDataActor."""

    payload: MarketDataPayload


class MarketDataActor(Actor):
    """Actor boundary for normalized market data events."""

    def __init__(
        self,
        subscribers: Iterable[ActorRef] = (),
        *,
        aggregate_timeframe: str | None = None,
        exchange_timezone: str | tzinfo | None = None,
    ) -> None:
        self._subscribers = tuple(subscribers)
        self._target_timeframe = (
            Timeframe.parse(aggregate_timeframe) if aggregate_timeframe is not None else None
        )
        if self._target_timeframe is not None and exchange_timezone is None:
            raise ValueError("exchange_timezone is required when aggregate_timeframe is set")
        self._exchange_timezone = exchange_timezone
        self._aggregators: dict[tuple[object, str, str], BarAggregator] = {}

    def handle(self, message: object) -> None:
        if isinstance(message, MarketDataEvent):
            if isinstance(message.payload, Bar) and self._target_timeframe is not None:
                aggregator = self._aggregator_for(message.payload)
                result = aggregator.update(message.payload)
                for completed in result.completed:
                    self._publish(completed)
                return
            self._publish(message.payload)
            return
        raise TypeError(f"unsupported market data message: {type(message).__name__}")

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

    def _publish(self, payload: MarketDataPayload) -> None:
        for subscriber in self._subscribers:
            subscriber.tell(payload)


__all__ = ["MarketDataActor", "MarketDataEvent", "MarketDataPayload"]
