"""Explicit risk decisions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from qts.core.ids import StrategyId


class RiskDecisionStatus(StrEnum):
    """Risk check outcome."""

    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


@dataclass(frozen=True, slots=True)
class RiskDecision:
    """Explicit result of a risk check."""

    status: RiskDecisionStatus
    reason_code: str | None = None
    reason: str | None = None
    rule_id: str | None = None
    checked_at: datetime | None = None
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    aggregation_decision_id: str | None = None
    conflict_reason: str | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def approve(
        cls,
        *,
        rule_id: str | None = None,
        checked_at: datetime | None = None,
        contributing_strategy_ids: tuple[StrategyId, ...] | None = None,
        aggregation_decision_id: str | None = None,
        conflict_reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> RiskDecision:
        """Build an APPROVED RiskDecision with optional rule and aggregation metadata."""
        return cls(
            status=RiskDecisionStatus.APPROVED,
            rule_id=rule_id,
            checked_at=checked_at,
            contributing_strategy_ids=contributing_strategy_ids
            if contributing_strategy_ids is not None
            else (),
            aggregation_decision_id=aggregation_decision_id,
            conflict_reason=conflict_reason,
            evidence={} if evidence is None else dict(evidence),
        )

    @classmethod
    def rejected(
        cls,
        reason_code: str,
        reason: str,
        *,
        rule_id: str | None = None,
        checked_at: datetime | None = None,
        contributing_strategy_ids: tuple[StrategyId, ...] | None = None,
        aggregation_decision_id: str | None = None,
        conflict_reason: str | None = None,
        evidence: Mapping[str, object] | None = None,
    ) -> RiskDecision:
        """Build a REJECTED RiskDecision, requiring non-empty reason code and reason."""
        if not reason_code.strip():
            raise ValueError("reason_code must not be empty")
        if not reason.strip():
            raise ValueError("reason must not be empty")
        return cls(
            status=RiskDecisionStatus.REJECTED,
            reason_code=reason_code,
            reason=reason,
            rule_id=rule_id,
            checked_at=checked_at,
            contributing_strategy_ids=contributing_strategy_ids
            if contributing_strategy_ids is not None
            else (),
            aggregation_decision_id=aggregation_decision_id,
            conflict_reason=conflict_reason,
            evidence={} if evidence is None else dict(evidence),
        )

    @property
    def approved(self) -> bool:
        """Return whether this decision's status is APPROVED."""
        return self.status is RiskDecisionStatus.APPROVED

    @property
    def reason_text(self) -> str | None:
        """Return the human-readable rejection reason, if any."""
        return self.reason


__all__ = ["RiskDecision", "RiskDecisionStatus"]
