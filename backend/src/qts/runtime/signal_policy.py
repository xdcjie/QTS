"""Signal aggregation policies for multi-strategy runtime flows."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum

from qts.core.ids import StrategyId
from qts.strategy_sdk import TargetIntent


class SignalAggregationPolicy(StrEnum):
    """Supported signal aggregation policies."""

    SUM_TARGETS = "sum_targets"
    PRIORITY_WINS = "priority_wins"
    WEIGHTED_NET = "weighted_net"
    REJECT_CONFLICT = "reject_conflict"


@dataclass(frozen=True, slots=True)
class SignalContribution:
    """One strategy's contribution to a target signal batch."""

    strategy_id: StrategyId
    intent: TargetIntent
    priority: int = 0
    weight: Decimal = Decimal("1")
    conflict_group: str = "default"

    def __post_init__(self) -> None:
        """Validate contribution metadata."""
        object.__setattr__(self, "weight", Decimal(str(self.weight)))
        if self.weight < Decimal("0"):
            raise ValueError("signal weight must be non-negative")


@dataclass(frozen=True, slots=True)
class SignalConflict:
    """Detected conflict between strategy target directions."""

    instrument_key: str
    strategy_ids: tuple[StrategyId, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class SignalAggregationDecision:
    """Auditable result of applying a signal aggregation policy."""

    policy: SignalAggregationPolicy
    intents: tuple[TargetIntent, ...]
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    rejected_strategy_ids: tuple[StrategyId, ...] = ()
    conflicts: tuple[SignalConflict, ...] = ()
    conflict_reason: str = ""
    target_before_risk: Decimal | None = None
    target_after_aggregation: Decimal | None = None


class SignalPolicyEngine:
    """Apply deterministic signal aggregation to strategy target intents."""

    def __init__(self, *, policy: SignalAggregationPolicy = SignalAggregationPolicy.SUM_TARGETS):
        """Create a signal policy engine."""
        self._policy = SignalAggregationPolicy(policy)

    def aggregate(
        self,
        contributions: tuple[SignalContribution, ...],
    ) -> SignalAggregationDecision:
        """Aggregate one conflict group of target contributions."""
        if not contributions:
            return SignalAggregationDecision(policy=self._policy, intents=())
        if self._policy is SignalAggregationPolicy.PRIORITY_WINS:
            return self._priority_wins(contributions)
        if self._policy is SignalAggregationPolicy.REJECT_CONFLICT and self._has_direction_conflict(
            contributions
        ):
            strategy_ids = tuple(item.strategy_id for item in contributions)
            conflict = SignalConflict(
                instrument_key=self._instrument_key(contributions[0].intent),
                strategy_ids=strategy_ids,
                reason="opposite directions for target quantity",
            )
            return SignalAggregationDecision(
                policy=self._policy,
                intents=(),
                rejected_strategy_ids=strategy_ids,
                conflicts=(conflict,),
                conflict_reason="opposite directions for target quantity",
            )
        return self._net_targets(
            contributions, weighted=self._policy is SignalAggregationPolicy.WEIGHTED_NET
        )

    def _priority_wins(
        self,
        contributions: tuple[SignalContribution, ...],
    ) -> SignalAggregationDecision:
        winner = max(contributions, key=lambda item: item.priority)
        rejected = tuple(item.strategy_id for item in contributions if item is not winner)
        return SignalAggregationDecision(
            policy=self._policy,
            intents=(winner.intent,),
            contributing_strategy_ids=(winner.strategy_id,),
            rejected_strategy_ids=rejected,
            target_before_risk=winner.intent.value,
            target_after_aggregation=winner.intent.value,
        )

    def _net_targets(
        self,
        contributions: tuple[SignalContribution, ...],
        *,
        weighted: bool,
    ) -> SignalAggregationDecision:
        first = contributions[0]
        total = Decimal("0")
        for contribution in contributions:
            value = contribution.intent.value or Decimal("0")
            total += value * contribution.weight if weighted else value
        return SignalAggregationDecision(
            policy=self._policy,
            intents=(replace(first.intent, value=total),),
            contributing_strategy_ids=tuple(item.strategy_id for item in contributions),
            conflicts=(self._conflict(contributions),)
            if self._has_direction_conflict(contributions)
            else (),
            conflict_reason=(
                "opposite directions netted" if self._has_direction_conflict(contributions) else ""
            ),
            target_before_risk=total,
            target_after_aggregation=total,
        )

    def _has_direction_conflict(self, contributions: tuple[SignalContribution, ...]) -> bool:
        signs = {
            self._sign(contribution.intent.value)
            for contribution in contributions
            if contribution.intent.value is not None and contribution.intent.value != Decimal("0")
        }
        return Decimal("-1") in signs and Decimal("1") in signs

    def _conflict(self, contributions: tuple[SignalContribution, ...]) -> SignalConflict:
        return SignalConflict(
            instrument_key=self._instrument_key(contributions[0].intent),
            strategy_ids=tuple(item.strategy_id for item in contributions),
            reason="opposite directions for target quantity",
        )

    @staticmethod
    def _instrument_key(intent: TargetIntent) -> str:
        return intent.asset.instrument_id.value

    @staticmethod
    def _sign(value: Decimal | None) -> Decimal:
        if value is None or value == Decimal("0"):
            return Decimal("0")
        return Decimal("1") if value > Decimal("0") else Decimal("-1")


__all__ = [
    "SignalAggregationDecision",
    "SignalAggregationPolicy",
    "SignalConflict",
    "SignalContribution",
    "SignalPolicyEngine",
]
