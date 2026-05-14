"""Signal aggregation actor boundary."""

from __future__ import annotations

from dataclasses import dataclass

from qts.core.ids import StrategyId
from qts.domain.market_data import Bar
from qts.runtime.actor import Actor
from qts.runtime.actor_ref import ActorRef
from qts.runtime.signal_policy import (
    SignalAggregationPolicy,
    SignalContribution,
    SignalPolicyEngine,
)
from qts.strategy_sdk import TargetIntent


@dataclass(frozen=True, slots=True)
class StrategySignalEvent:
    """Strategy intents emitted for one completed bar."""

    bar: Bar
    intents: tuple[TargetIntent, ...]
    strategy_id: StrategyId | None = None


@dataclass(frozen=True, slots=True)
class AggregatedSignalBatch:
    """Aggregated intents ready for portfolio/risk/order flow."""

    bar: Bar
    intents: tuple[TargetIntent, ...]
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    rejected_strategy_ids: tuple[StrategyId, ...] = ()
    conflict_reason: str = ""
    aggregation_policy: SignalAggregationPolicy = SignalAggregationPolicy.SUM_TARGETS


class SignalAggregatorActor(Actor):
    """Boundary for combining strategy signals before order flow."""

    def __init__(
        self,
        *,
        result_ref: ActorRef,
        policy: SignalAggregationPolicy = SignalAggregationPolicy.SUM_TARGETS,
    ) -> None:
        """Perform __init__."""
        self._result_ref = result_ref
        self._policy_engine = SignalPolicyEngine(policy=policy)

    def handle(self, message: object) -> None:
        """Perform handle."""
        if isinstance(message, StrategySignalEvent):
            if message.strategy_id is not None:
                decision = self._policy_engine.aggregate(
                    tuple(
                        SignalContribution(strategy_id=message.strategy_id, intent=intent)
                        for intent in message.intents
                    )
                )
                self._result_ref.tell(
                    AggregatedSignalBatch(
                        bar=message.bar,
                        intents=decision.intents,
                        contributing_strategy_ids=decision.contributing_strategy_ids,
                        rejected_strategy_ids=decision.rejected_strategy_ids,
                        conflict_reason=decision.conflict_reason,
                        aggregation_policy=decision.policy,
                    )
                )
                return
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
