"""Signal aggregation actor boundary."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import InstrumentId, StrategyId
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
    intents: tuple[TargetIntent, ...] = ()
    strategy_id: StrategyId | None = None
    contributions: tuple[SignalContribution, ...] = ()
    conflict_group: str = "default"
    signal_weight: Decimal = Decimal("1")
    signal_priority: int = 0
    signal_aggregation_policy: SignalAggregationPolicy = SignalAggregationPolicy.SUM_TARGETS


@dataclass(frozen=True, slots=True)
class AggregatedSignalBatch:
    """Aggregated intents ready for portfolio/risk/order flow."""

    bar: Bar
    intents: tuple[TargetIntent, ...]
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    rejected_strategy_ids: tuple[StrategyId, ...] = ()
    conflict_reason: str = ""
    aggregation_policy: SignalAggregationPolicy = SignalAggregationPolicy.SUM_TARGETS
    conflict_group: str = "default"
    target_before_risk: Decimal | None = None
    target_after_aggregation: Decimal | None = None


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
        if not isinstance(message, StrategySignalEvent):
            raise TypeError(f"unsupported signal aggregation message: {type(message).__name__}")

        if message.strategy_id is None and not message.contributions:
            self._result_ref.tell(
                AggregatedSignalBatch(
                    bar=message.bar,
                    intents=message.intents,
                    conflict_group=message.conflict_group,
                    aggregation_policy=message.signal_aggregation_policy,
                )
            )
            return

        contributions = self._contributions(message)
        if not contributions:
            self._result_ref.tell(
                AggregatedSignalBatch(
                    bar=message.bar,
                    intents=(),
                )
            )
            return

        grouped = self._group_contributions(contributions)
        for (_instrument_id, conflict_group, policy), grouped_contributions in grouped.items():
            decision = SignalPolicyEngine(policy=policy).aggregate(grouped_contributions)
            self._result_ref.tell(
                AggregatedSignalBatch(
                    bar=message.bar,
                    intents=decision.intents,
                    contributing_strategy_ids=decision.contributing_strategy_ids,
                    rejected_strategy_ids=decision.rejected_strategy_ids,
                    conflict_reason=decision.conflict_reason,
                    aggregation_policy=decision.policy,
                    conflict_group=conflict_group,
                    target_before_risk=decision.target_before_risk,
                    target_after_aggregation=decision.target_after_aggregation,
                )
            )

    def _contributions(self, message: StrategySignalEvent) -> tuple[SignalContribution, ...]:
        if message.contributions:
            return message.contributions
        return tuple(
            SignalContribution(
                strategy_id=message.strategy_id,
                intent=intent,
                aggregation_policy=message.signal_aggregation_policy,
                priority=message.signal_priority,
                weight=message.signal_weight,
                conflict_group=message.conflict_group,
            )
            for intent in message.intents
            if message.strategy_id is not None
        )

    @staticmethod
    def _group_contributions(
        contributions: tuple[SignalContribution, ...],
    ) -> dict[
        tuple[InstrumentId, str, SignalAggregationPolicy],
        tuple[SignalContribution, ...],
    ]:
        grouped: dict[
            tuple[InstrumentId, str, SignalAggregationPolicy],
            list[SignalContribution],
        ] = {}
        for contribution in contributions:
            key = (
                contribution.intent.asset.instrument_id,
                contribution.conflict_group,
                contribution.aggregation_policy,
            )
            grouped.setdefault(key, []).append(contribution)
        return {key: tuple(values) for key, values in grouped.items()}


__all__ = [
    "AggregatedSignalBatch",
    "SignalContribution",
    "SignalAggregatorActor",
    "StrategySignalEvent",
]
