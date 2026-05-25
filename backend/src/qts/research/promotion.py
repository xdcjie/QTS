"""Research-to-promotion review packet schemas.

These schemas make promotion review machine-readable. They do not create
paper/live runtime configuration and do not approve strategy code by themselves.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PaperReadinessChecklist:
    """Required evidence before a candidate can be labelled paper-ready."""

    evidence_bundle_verified: bool = False
    trade_diagnostics_available: bool = False
    validation_scorecard_available: bool = False
    cost_stress_available: bool = False
    no_research_import_in_production: bool = False
    no_examples_direct_promotion: bool = False

    def missing_items(self) -> tuple[str, ...]:
        """Return checklist field names that are not satisfied."""

        return tuple(
            field_name
            for field_name in (
                "evidence_bundle_verified",
                "trade_diagnostics_available",
                "validation_scorecard_available",
                "cost_stress_available",
                "no_research_import_in_production",
                "no_examples_direct_promotion",
            )
            if not bool(getattr(self, field_name))
        )

    def to_payload(self) -> dict[str, bool]:
        """Return a JSON-ready checklist payload."""

        return {
            "cost_stress_available": self.cost_stress_available,
            "evidence_bundle_verified": self.evidence_bundle_verified,
            "no_examples_direct_promotion": self.no_examples_direct_promotion,
            "no_research_import_in_production": self.no_research_import_in_production,
            "trade_diagnostics_available": self.trade_diagnostics_available,
            "validation_scorecard_available": self.validation_scorecard_available,
        }


@dataclass(frozen=True, slots=True)
class PromotionCandidateSpec:
    """Machine-readable packet for human promotion review."""

    promotion_candidate_id: str
    strategy_id: str
    source_module: str
    target_module: str
    evidence_bundle_id: str
    status: str = "review_required"
    paper_readiness: PaperReadinessChecklist = field(default_factory=PaperReadinessChecklist)
    production_params: Mapping[str, Any] | None = None
    examples_migration_reviewed: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "promotion_candidate_id",
            "strategy_id",
            "source_module",
            "target_module",
            "evidence_bundle_id",
        ):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} is required")
        if self.status not in _PROMOTION_STATUSES:
            raise ValueError(f"unsupported promotion candidate status: {self.status}")
        if self.source_module == self.target_module:
            raise ValueError("source_module and target_module must be separate review boundaries")
        if self.source_module.startswith("examples.") and not self.examples_migration_reviewed:
            raise ValueError("examples strategy requires migration review")
        _reject_research_only_params(self.production_params or {})
        if self.status == "paper_candidate":
            missing_items = self.paper_readiness.missing_items()
            if missing_items:
                raise ValueError(f"paper_candidate missing readiness item: {missing_items[0]}")

    def to_payload(self) -> dict[str, Any]:
        """Return deterministic JSON-ready promotion review payload."""

        return {
            "evidence_bundle_id": self.evidence_bundle_id,
            "paper_readiness": self.paper_readiness.to_payload(),
            "production_params": dict(self.production_params or {}),
            "promotion_boundary": "human_review_required",
            "promotion_candidate_id": self.promotion_candidate_id,
            "source_module": self.source_module,
            "status": self.status,
            "strategy_id": self.strategy_id,
            "target_module": self.target_module,
        }


def _reject_research_only_params(params: Mapping[str, Any]) -> None:
    for key in params:
        if str(key) in _RESEARCH_ONLY_PARAMS:
            raise ValueError(f"research-only parameter is not allowed in promotion spec: {key}")


_PROMOTION_STATUSES = frozenset(
    {"review_required", "paper_candidate", "small_live_candidate", "rejected", "retired"}
)
_RESEARCH_ONLY_PARAMS = frozenset(
    {
        "ablation_id",
        "candidate_tags",
        "factor_filters",
        "idea_id",
        "trial_budget",
        "trial_count",
    }
)


__all__ = ["PaperReadinessChecklist", "PromotionCandidateSpec"]
