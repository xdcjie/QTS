"""Signal aggregation actor boundary."""

from __future__ import annotations

from dataclasses import dataclass

from qts.domain.market_data import Bar
from qts.runtime.actor import Actor
from qts.runtime.actor_ref import ActorRef
from qts.strategy_sdk import TargetIntent


@dataclass(frozen=True, slots=True)
class StrategySignalEvent:
    """Strategy intents emitted for one completed bar."""

    bar: Bar
    intents: tuple[TargetIntent, ...]


@dataclass(frozen=True, slots=True)
class AggregatedSignalBatch:
    """Aggregated intents ready for portfolio/risk/order flow."""

    bar: Bar
    intents: tuple[TargetIntent, ...]


class SignalAggregatorActor(Actor):
    """Boundary for combining strategy signals before order flow."""

    def __init__(self, *, result_ref: ActorRef) -> None:
        self._result_ref = result_ref

    def handle(self, message: object) -> None:
        if isinstance(message, StrategySignalEvent):
            self._result_ref.tell(
                AggregatedSignalBatch(
                    bar=message.bar,
                    intents=message.intents,
                )
            )
            return
        raise TypeError(f"unsupported signal aggregation message: {type(message).__name__}")


__all__ = [
    "AggregatedSignalBatch",
    "SignalAggregatorActor",
    "StrategySignalEvent",
]
