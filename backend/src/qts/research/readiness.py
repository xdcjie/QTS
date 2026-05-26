"""Paper/live readiness gate decision evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps
from qts.research.strategy_registry import LifecycleStatus


@dataclass(frozen=True, slots=True)
class PaperLiveReadinessEvidence:
    """Evidence required before a strategy can pass paper/live readiness gates."""

    paper_trading_days: int
    reconciliation_evidence_ref: str
    risk_limits_ref: str
    kill_switch_ref: str
    runbook_ref: str
    alerting_checks_ref: str
    monitoring_checks_ref: str
    minimum_paper_trading_days: int = 20

    def __post_init__(self) -> None:
        if self.paper_trading_days < self.minimum_paper_trading_days:
            raise ValueError(
                f"paper_trading_days must be at least {self.minimum_paper_trading_days}"
            )

    def missing_items(self) -> tuple[str, ...]:
        """Return required evidence fields that are not populated."""

        missing: list[str] = []
        for field_name in (
            "reconciliation_evidence_ref",
            "risk_limits_ref",
            "kill_switch_ref",
            "runbook_ref",
            "alerting_checks_ref",
            "monitoring_checks_ref",
        ):
            if not str(getattr(self, field_name)).strip():
                missing.append(field_name)
        return tuple(missing)

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready readiness evidence payload."""

        return {
            "alerting_checks_ref": self.alerting_checks_ref,
            "kill_switch_ref": self.kill_switch_ref,
            "minimum_paper_trading_days": self.minimum_paper_trading_days,
            "monitoring_checks_ref": self.monitoring_checks_ref,
            "paper_trading_days": self.paper_trading_days,
            "reconciliation_evidence_ref": self.reconciliation_evidence_ref,
            "risk_limits_ref": self.risk_limits_ref,
            "runbook_ref": self.runbook_ref,
        }


@dataclass(frozen=True, slots=True)
class HumanApprovalRecord:
    """Human signoff required for paper/live readiness decisions."""

    approved_by: str
    approved_at: str
    approval_ref: str

    def __post_init__(self) -> None:
        for field_name in ("approved_by", "approved_at", "approval_ref"):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} is required")

    def to_payload(self) -> dict[str, str]:
        """Return a JSON-ready approval payload."""

        return {
            "approval_ref": self.approval_ref,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
        }


@dataclass(frozen=True, slots=True)
class PaperLiveReadinessDecision:
    """Paper/live readiness gate decision artifact."""

    strategy_id: str
    decision_date: str
    target_status: str
    evidence: PaperLiveReadinessEvidence
    approval: HumanApprovalRecord

    def __post_init__(self) -> None:
        for field_name in ("strategy_id", "decision_date", "target_status"):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} is required")
        try:
            lifecycle_status = LifecycleStatus(self.target_status)
        except ValueError as exc:
            raise ValueError(
                f"target_status must be one of: {_READINESS_TARGET_STATUS_TEXT}"
            ) from exc
        if lifecycle_status not in _READINESS_TARGET_STATUSES:
            raise ValueError(f"target_status must be one of: {_READINESS_TARGET_STATUS_TEXT}")
        missing_items = self.evidence.missing_items()
        if missing_items:
            raise ValueError(f"{missing_items[0]} is required")

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready readiness decision artifact payload."""

        return {
            "approval": self.approval.to_payload(),
            "artifact": (
                f"artifacts/readiness/{self.strategy_id}/{self.decision_date}/"
                "paper_live_gate_decision.json"
            ),
            "decision_date": self.decision_date,
            "evidence": self.evidence.to_payload(),
            "paper_live_readiness_gate": "approved",
            "strategy_id": self.strategy_id,
            "target_status": self.target_status,
        }

    def write(self, root: Path = Path("artifacts/readiness")) -> Path:
        """Write the readiness decision under the standard evidence tree."""

        path = root / self.strategy_id / self.decision_date / "paper_live_gate_decision.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stable_json_dumps(self.to_payload()) + "\n", encoding="utf-8")
        return path


_READINESS_TARGET_STATUSES = frozenset(
    {
        LifecycleStatus.PAPER_CANDIDATE,
        LifecycleStatus.LIVE_CANDIDATE,
        LifecycleStatus.LIVE_APPROVED,
    }
)
_READINESS_TARGET_STATUS_TEXT = ", ".join(
    sorted(status.value for status in _READINESS_TARGET_STATUSES)
)


__all__ = [
    "HumanApprovalRecord",
    "PaperLiveReadinessDecision",
    "PaperLiveReadinessEvidence",
]
