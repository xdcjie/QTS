"""Signal aggregation actor boundary."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256

from qts.core.ids import AccountId, CorrelationId, InstrumentId, StrategyId
from qts.domain.market_data import Bar
from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorUnhandledMessageError
from qts.runtime.actor_ref import ActorRef
from qts.runtime.signal_policy import (
    SignalAggregationPolicy,
    SignalConflict,
    SignalContribution,
    SignalPolicyEngine,
)
from qts.strategy_sdk import TargetIntent


@dataclass(frozen=True, slots=True)
class StrategySignalEvent:
    """Strategy intents emitted for one completed bar."""

    bar: Bar
    intents: tuple[TargetIntent, ...] = ()
    account_id: AccountId | None = None
    correlation_id: CorrelationId | None = None
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
    aggregation_decision_id: str | None = None
    account_id: AccountId | None = None
    instrument_id: InstrumentId | None = None
    correlation_id: CorrelationId | None = None
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    rejected_strategy_ids: tuple[StrategyId, ...] = ()
    conflicts: tuple[SignalConflict, ...] = ()
    conflict_reason: str = ""
    aggregation_policy: SignalAggregationPolicy = SignalAggregationPolicy.SUM_TARGETS
    conflict_group: str = "default"
    target_before_risk: Decimal | None = None
    target_after_aggregation: Decimal | None = None

    def __post_init__(self) -> None:
        """Normalize derived audit identity defaults."""
        if self.instrument_id is None:
            object.__setattr__(self, "instrument_id", self.bar.instrument_id)


class SignalAggregatorActor(Actor):
    """Boundary for combining strategy signals before order flow."""

    def __init__(
        self,
        *,
        result_ref: ActorRef,
        policy: SignalAggregationPolicy = SignalAggregationPolicy.SUM_TARGETS,
    ) -> None:
        """Initialize the aggregator with its result actor ref and policy engine."""
        self._result_ref = result_ref
        self._policy_engine = SignalPolicyEngine(policy=policy)

    def handle(self, message: object) -> None:
        """Aggregate a StrategySignalEvent into per-group batches and emit them downstream."""
        if not isinstance(message, StrategySignalEvent):
            raise ActorUnhandledMessageError(
                f"unsupported signal aggregation message: {type(message).__name__}"
            )

        if message.strategy_id is None and not message.contributions:
            self._result_ref.tell(
                AggregatedSignalBatch(
                    bar=message.bar,
                    intents=message.intents,
                    account_id=message.account_id,
                    instrument_id=message.bar.instrument_id,
                    correlation_id=message.correlation_id,
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
                    account_id=message.account_id,
                    instrument_id=message.bar.instrument_id,
                    correlation_id=message.correlation_id,
                )
            )
            return

        grouped = self._group_contributions(contributions)
        for (instrument_id, conflict_group, policy), grouped_contributions in grouped.items():
            decision = SignalPolicyEngine(policy=policy).aggregate(grouped_contributions)
            self._result_ref.tell(
                AggregatedSignalBatch(
                    bar=message.bar,
                    intents=decision.intents,
                    aggregation_decision_id=self._aggregation_decision_id(
                        bar=message.bar,
                        account_id=message.account_id,
                        correlation_id=message.correlation_id,
                        instrument_id=instrument_id,
                        conflict_group=conflict_group,
                        policy=decision.policy,
                        contributions=grouped_contributions,
                    ),
                    account_id=message.account_id,
                    instrument_id=instrument_id,
                    correlation_id=message.correlation_id,
                    contributing_strategy_ids=decision.contributing_strategy_ids,
                    rejected_strategy_ids=decision.rejected_strategy_ids,
                    conflicts=decision.conflicts,
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

    @staticmethod
    def _aggregation_decision_id(
        *,
        bar: Bar,
        account_id: AccountId | None,
        correlation_id: CorrelationId | None,
        instrument_id: InstrumentId,
        conflict_group: str,
        policy: SignalAggregationPolicy,
        contributions: tuple[SignalContribution, ...],
    ) -> str:
        payload = "|".join(
            (
                account_id.value if account_id is not None else "",
                correlation_id.value if correlation_id is not None else "",
                instrument_id.value,
                bar.start_time.isoformat(),
                bar.end_time.isoformat(),
                conflict_group,
                policy.value,
                ";".join(
                    f"{item.strategy_id.value}:{item.intent.intent_type.value}:{item.intent.value}"
                    for item in contributions
                ),
            )
        )
        return f"sigagg-{sha256(payload.encode('utf-8')).hexdigest()[:16]}"


__all__ = [
    "AggregatedSignalBatch",
    "SignalContribution",
    "SignalAggregatorActor",
    "StrategySignalEvent",
]
