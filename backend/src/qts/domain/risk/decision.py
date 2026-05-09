"""Explicit risk decisions."""

from __future__ import annotations

from dataclasses import dataclass
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

    @classmethod
    def approve(cls) -> RiskDecision:
        return cls(status=RiskDecisionStatus.APPROVED)

    @classmethod
    def rejected(cls, reason_code: str, reason: str) -> RiskDecision:
        if not reason_code.strip():
            raise ValueError("reason_code must not be empty")
        if not reason.strip():
            raise ValueError("reason must not be empty")
        return cls(
            status=RiskDecisionStatus.REJECTED,
            reason_code=reason_code,
            reason=reason,
        )

    @property
    def approved(self) -> bool:
        return self.status is RiskDecisionStatus.APPROVED


__all__ = ["RiskDecision", "RiskDecisionStatus"]
