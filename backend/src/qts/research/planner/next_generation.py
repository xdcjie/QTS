"""Evidence-backed next-generation proposal and approval records."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.audit_log import ResearchAuditLog
from qts.research.landscape import FitnessAnalytics


@dataclass(frozen=True, slots=True)
class GenerationMutation:
    """One explicit mutation proposed for the next research generation."""

    mutation_id: str
    target: str
    action: str
    payload: Mapping[str, Any]
    reason: str
    evidence_refs: tuple[str, ...]
    mutation_type: ClassVar[str] = "generation"

    def __post_init__(self) -> None:
        for field_name in ("mutation_id", "target", "action", "reason"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")
        if not self.evidence_refs:
            raise ValueError("mutation evidence_refs must not be empty")
        if any(not str(ref).strip() for ref in self.evidence_refs):
            raise ValueError("mutation evidence_refs must contain non-empty values")
        object.__setattr__(self, "payload", self._json_object(self.payload))
        object.__setattr__(self, "evidence_refs", tuple(str(ref) for ref in self.evidence_refs))

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready mutation payload."""

        return {
            "action": self.action,
            "evidence_refs": list(self.evidence_refs),
            "mutation_id": self.mutation_id,
            "mutation_type": self.mutation_type,
            "payload": dict(self.payload),
            "reason": self.reason,
            "target": self.target,
        }

    @staticmethod
    def _json_object(payload: Mapping[str, Any]) -> dict[str, Any]:
        loaded = json.loads(stable_json_dumps(dict(payload)))
        if not isinstance(loaded, dict):
            raise ValueError("mutation payload must be a JSON object")
        return loaded


@dataclass(frozen=True, slots=True)
class SearchSpaceMutation(GenerationMutation):
    """Explicit mutation to a bounded search-space region."""

    mutation_type: ClassVar[str] = "search_space"


@dataclass(frozen=True, slots=True)
class FamilyBudgetMutation(GenerationMutation):
    """Explicit mutation to family-level research trial budgets."""

    mutation_type: ClassVar[str] = "family_budget"


@dataclass(frozen=True, slots=True)
class HypothesisMutation(GenerationMutation):
    """Explicit mutation to the next research hypothesis set."""

    mutation_type: ClassVar[str] = "hypothesis"


@dataclass(frozen=True, slots=True)
class StrategyVariantMutation(GenerationMutation):
    """Explicit mutation to strategy variant construction."""

    mutation_type: ClassVar[str] = "strategy_variant"


@dataclass(frozen=True, slots=True)
class NextGenerationProposal:
    """Human-reviewable proposal for the next autonomous research generation."""

    proposal_id: str
    campaign_id: str
    previous_generation_id: str
    next_generation_id: str
    previous_data_window: Mapping[str, Any]
    proposed_data_window: Mapping[str, Any]
    trial_budget: int
    max_trial_budget: int
    mutations: tuple[GenerationMutation, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "proposal_id",
            "campaign_id",
            "previous_generation_id",
            "next_generation_id",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")
        if self.trial_budget < 0:
            raise ValueError("trial_budget must be non-negative")
        if self.max_trial_budget < 0:
            raise ValueError("max_trial_budget must be non-negative")
        if self.trial_budget > self.max_trial_budget:
            raise ValueError(
                f"proposal trial budget exceeds maximum: "
                f"{self.trial_budget} > {self.max_trial_budget}"
            )
        object.__setattr__(
            self,
            "previous_data_window",
            GenerationMutation._json_object(self.previous_data_window),
        )
        object.__setattr__(
            self,
            "proposed_data_window",
            GenerationMutation._json_object(self.proposed_data_window),
        )
        mutation_ids = [mutation.mutation_id for mutation in self.mutations]
        if len(set(mutation_ids)) != len(mutation_ids):
            raise ValueError("mutation_id values must be unique")
        if (
            self.previous_data_window != self.proposed_data_window
            and not self._has_data_window_mutation()
        ):
            raise ValueError("data window change requires explicit mutation evidence")

    @classmethod
    def from_analytics(
        cls,
        *,
        campaign_id: str,
        previous_generation_id: str,
        next_generation_id: str,
        analytics: FitnessAnalytics,
        previous_campaign_config: Mapping[str, Any],
        trial_budget_state: Mapping[str, Any],
        human_constraints: Mapping[str, Any],
    ) -> NextGenerationProposal:
        """Generate a deterministic evidence-backed next-generation proposal."""

        requested_budget = cls._int_value(trial_budget_state, "requested_trials")
        remaining_budget = cls._int_value(trial_budget_state, "remaining_trials")
        max_per_generation = cls._int_value(human_constraints, "max_trials_per_generation")
        max_trial_budget = min(remaining_budget, max_per_generation)
        if requested_budget > max_trial_budget:
            raise ValueError(
                f"proposal trial budget exceeds maximum: {requested_budget} > {max_trial_budget}"
            )
        data_window = previous_campaign_config.get("data_window")
        if not isinstance(data_window, Mapping):
            raise ValueError("previous_campaign_config.data_window is required")
        analytics_payload = analytics.to_payload()
        mutations = cls._mutations_from_analytics(analytics, analytics_payload)
        return cls(
            proposal_id=f"{campaign_id}:{next_generation_id}",
            campaign_id=campaign_id,
            previous_generation_id=previous_generation_id,
            next_generation_id=next_generation_id,
            previous_data_window=data_window,
            proposed_data_window=data_window,
            trial_budget=requested_budget,
            max_trial_budget=max_trial_budget,
            mutations=mutations,
        )

    @property
    def proposal_hash(self) -> str:
        """Return the deterministic proposal artifact hash."""

        return stable_json_hash(self._payload_without_hash())

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready proposal artifact."""

        payload = self._payload_without_hash()
        payload["proposal_hash"] = self.proposal_hash
        return payload

    def write_artifact(self, path: Path) -> None:
        """Write the proposal artifact as deterministic JSON."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_payload(), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    def _payload_without_hash(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "max_trial_budget": self.max_trial_budget,
            "mutations": [mutation.to_payload() for mutation in self.mutations],
            "next_generation_id": self.next_generation_id,
            "previous_data_window": dict(self.previous_data_window),
            "previous_generation_id": self.previous_generation_id,
            "proposal_id": self.proposal_id,
            "proposed_data_window": dict(self.proposed_data_window),
            "trial_budget": self.trial_budget,
        }

    def _has_data_window_mutation(self) -> bool:
        return any(
            mutation.target == "data_window" and mutation.evidence_refs
            for mutation in self.mutations
        )

    @classmethod
    def _mutations_from_analytics(
        cls,
        analytics: FitnessAnalytics,
        analytics_payload: Mapping[str, Any],
    ) -> tuple[GenerationMutation, ...]:
        evidence_ref = str(analytics_payload["analytics_hash"])
        mutations: list[GenerationMutation] = []
        best_family = analytics_payload.get("best_family")
        if isinstance(best_family, Mapping):
            mutations.append(
                SearchSpaceMutation(
                    mutation_id="search-space-001",
                    target=f"{best_family['strategy_family']}.parameter_region",
                    action="focus_best_family",
                    payload={
                        "factor_family": best_family["factor_family"],
                        "strategy_family": best_family["strategy_family"],
                    },
                    reason="best family by risk-adjusted fitness",
                    evidence_refs=(evidence_ref, *tuple(best_family.get("evidence_refs", ()))),
                )
            )

        for index, summary in enumerate(analytics_payload["family_summaries"], start=1):
            if not isinstance(summary, Mapping):
                continue
            if float(summary["family_success_rate"]) >= 0.5:
                continue
            mutations.append(
                FamilyBudgetMutation(
                    mutation_id=f"family-budget-{index:03d}",
                    target=str(summary["strategy_family"]),
                    action="reduce_family_budget",
                    payload={
                        "accepted_count": summary["accepted_count"],
                        "family_success_rate": summary["family_success_rate"],
                        "trial_count": summary["trial_count"],
                    },
                    reason="family success rate below planner threshold",
                    evidence_refs=(evidence_ref, *tuple(summary.get("evidence_refs", ()))),
                )
            )

        for index, cluster in enumerate(analytics_payload["rejection_clusters"], start=1):
            if not isinstance(cluster, Mapping):
                continue
            reason = str(cluster["reason"]).lower()
            if "drawdown" in reason:
                mutations.append(
                    StrategyVariantMutation(
                        mutation_id=f"strategy-variant-{index:03d}",
                        target="risk_controls",
                        action="add_stop_or_vol_target",
                        payload={"rejection_reason": cluster["reason"]},
                        reason="drawdown rejection cluster requires explicit risk control",
                        evidence_refs=(evidence_ref, *tuple(cluster.get("evidence_refs", ()))),
                    )
                )
            elif "cost" in reason or "slippage" in reason:
                mutations.append(
                    StrategyVariantMutation(
                        mutation_id=f"strategy-variant-{index:03d}",
                        target="holding_period",
                        action="increase_min_hold_bars",
                        payload={"rejection_reason": cluster["reason"]},
                        reason="cost rejection cluster requires lower turnover variant",
                        evidence_refs=(evidence_ref, *tuple(cluster.get("evidence_refs", ()))),
                    )
                )
        if not mutations:
            mutations.append(
                HypothesisMutation(
                    mutation_id="hypothesis-001",
                    target="research_hypothesis",
                    action="continue_evidence_backed_search",
                    payload={"trial_count": analytics_payload["trial_count"]},
                    reason="no rejection cluster requires a structural mutation",
                    evidence_refs=(evidence_ref,),
                )
            )
        return tuple(sorted(mutations, key=lambda mutation: mutation.mutation_id))

    @staticmethod
    def _int_value(payload: Mapping[str, Any], field_name: str) -> int:
        value = payload.get(field_name)
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be an integer")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip():
            return int(value)
        raise ValueError(f"{field_name} is required")


@dataclass(frozen=True, slots=True)
class GenerationApprovalRecord:
    """Human decision record for a next-generation proposal artifact."""

    proposal_id: str
    proposal_hash: str
    decision: str
    reviewer: str
    decided_at: datetime
    reason: str
    evidence_refs: tuple[str, ...]
    audit_record_id: str | None = None

    def __post_init__(self) -> None:
        if self.decision not in {"approved", "rejected"}:
            raise ValueError("decision must be approved or rejected")
        for field_name in ("proposal_id", "proposal_hash", "reviewer", "reason"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")
        if (
            self.decided_at.tzinfo is None
            or self.decided_at.tzinfo.utcoffset(self.decided_at) is None
        ):
            raise ValueError("decided_at must be timezone-aware")
        if not self.evidence_refs:
            raise ValueError("approval evidence_refs must not be empty")
        object.__setattr__(self, "evidence_refs", tuple(str(ref) for ref in self.evidence_refs))

    @property
    def approval_hash(self) -> str:
        """Return deterministic hash of the approval/rejection record."""

        return stable_json_hash(self._payload_without_hash())

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready approval payload."""

        payload = self._payload_without_hash()
        payload["approval_hash"] = self.approval_hash
        return payload

    def _payload_without_hash(self) -> dict[str, Any]:
        return {
            "audit_record_id": self.audit_record_id,
            "decided_at": self.decided_at.isoformat(),
            "decision": self.decision,
            "evidence_refs": list(self.evidence_refs),
            "proposal_hash": self.proposal_hash,
            "proposal_id": self.proposal_id,
            "reason": self.reason,
            "reviewer": self.reviewer,
        }


class GenerationApprovalPolicy:
    """Human approval gate before a next-generation proposal can execute."""

    def approve(
        self,
        proposal: NextGenerationProposal,
        *,
        reviewer: str,
        decided_at: datetime,
        reason: str,
        evidence_refs: tuple[str, ...],
        audit_log: ResearchAuditLog | None = None,
    ) -> GenerationApprovalRecord:
        """Approve a proposal and optionally append a ResearchAuditLog record."""

        return self._decide(
            proposal,
            decision="approved",
            reviewer=reviewer,
            decided_at=decided_at,
            reason=reason,
            evidence_refs=evidence_refs,
            audit_log=audit_log,
        )

    def reject(
        self,
        proposal: NextGenerationProposal,
        *,
        reviewer: str,
        decided_at: datetime,
        reason: str,
        evidence_refs: tuple[str, ...],
        audit_log: ResearchAuditLog | None = None,
    ) -> GenerationApprovalRecord:
        """Reject a proposal and optionally append a ResearchAuditLog record."""

        return self._decide(
            proposal,
            decision="rejected",
            reviewer=reviewer,
            decided_at=decided_at,
            reason=reason,
            evidence_refs=evidence_refs,
            audit_log=audit_log,
        )

    def can_execute(
        self,
        proposal: NextGenerationProposal,
        approval: GenerationApprovalRecord | None,
    ) -> bool:
        """Return whether the exact proposal artifact is approved for execution."""

        return bool(self.execution_payload(proposal, approval)["accepted"])

    def execution_payload(
        self,
        proposal: NextGenerationProposal,
        approval: GenerationApprovalRecord | None,
    ) -> dict[str, Any]:
        """Return audit-ready execution gate status."""

        if approval is None:
            return {
                "accepted": False,
                "proposal_hash": proposal.proposal_hash,
                "proposal_id": proposal.proposal_id,
                "reasons": ("proposal approval is required",),
            }
        if approval.proposal_hash != proposal.proposal_hash:
            return {
                "accepted": False,
                "approval_hash": approval.approval_hash,
                "proposal_hash": proposal.proposal_hash,
                "proposal_id": proposal.proposal_id,
                "reasons": ("approval proposal_hash does not match proposal artifact",),
            }
        if approval.decision != "approved":
            return {
                "accepted": False,
                "approval_hash": approval.approval_hash,
                "proposal_hash": proposal.proposal_hash,
                "proposal_id": proposal.proposal_id,
                "reasons": (f"proposal approval decision is {approval.decision}",),
            }
        return {
            "accepted": True,
            "approval_hash": approval.approval_hash,
            "proposal_hash": proposal.proposal_hash,
            "proposal_id": proposal.proposal_id,
            "reasons": (),
        }

    def _decide(
        self,
        proposal: NextGenerationProposal,
        *,
        decision: str,
        reviewer: str,
        decided_at: datetime,
        reason: str,
        evidence_refs: tuple[str, ...],
        audit_log: ResearchAuditLog | None,
    ) -> GenerationApprovalRecord:
        record = GenerationApprovalRecord(
            proposal_id=proposal.proposal_id,
            proposal_hash=proposal.proposal_hash,
            decision=decision,
            reviewer=reviewer,
            decided_at=decided_at,
            reason=reason,
            evidence_refs=evidence_refs,
        )
        if audit_log is None:
            return record
        audit_record = audit_log.append(
            "human_review_decided",
            record.to_payload(),
            created_at=decided_at,
        )
        return replace(record, audit_record_id=audit_record.record_id)


__all__ = [
    "FamilyBudgetMutation",
    "GenerationApprovalPolicy",
    "GenerationApprovalRecord",
    "GenerationMutation",
    "HypothesisMutation",
    "NextGenerationProposal",
    "SearchSpaceMutation",
    "StrategyVariantMutation",
]
