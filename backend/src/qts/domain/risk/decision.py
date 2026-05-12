"""Explicit risk decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


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

    @classmethod
    def approve(
        cls,
        *,
        rule_id: str | None = None,
        checked_at: datetime | None = None,
    ) -> RiskDecision:
        """Perform approve."""
        return cls(status=RiskDecisionStatus.APPROVED, rule_id=rule_id, checked_at=checked_at)

    @classmethod
    def rejected(
        cls,
        reason_code: str,
        reason: str,
        *,
        rule_id: str | None = None,
        checked_at: datetime | None = None,
    ) -> RiskDecision:
        """Perform rejected."""
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
        )

    @property
    def approved(self) -> bool:
        """Perform approved."""
        return self.status is RiskDecisionStatus.APPROVED

    @property
    def reason_text(self) -> str | None:
        """Perform reason_text."""
        return self.reason


__all__ = ["RiskDecision", "RiskDecisionStatus"]
