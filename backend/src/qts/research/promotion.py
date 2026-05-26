"""Research-to-promotion review packet schemas.

These schemas make promotion review machine-readable. They do not create
paper/live runtime configuration and do not approve strategy code by themselves.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.research.metrics import metric_value


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
        if not self.target_module.startswith(_APPROVED_PROMOTION_TARGET_PREFIXES):
            raise ValueError("target_module must be production-owned")
        if self.source_module.startswith("examples.") and not self.examples_migration_reviewed:
            raise ValueError("examples strategy requires migration review")
        _reject_research_only_params(self.production_params or {})
        if self.status in _READINESS_REQUIRED_STATUSES:
            missing_items = self.paper_readiness.missing_items()
            if missing_items:
                raise ValueError(f"{self.status} missing readiness item: {missing_items[0]}")

    def missing_items(self) -> tuple[str, ...]:
        """Return readiness items still missing for promotion review."""

        return self.paper_readiness.missing_items()

    def to_payload(self) -> dict[str, Any]:
        """Return deterministic JSON-ready promotion review payload."""

        return {
            "evidence_bundle_id": self.evidence_bundle_id,
            "missing_items": list(self.missing_items()),
            "paper_readiness": self.paper_readiness.to_payload(),
            "production_params": dict(self.production_params or {}),
            "promotion_boundary": "human_review_required",
            "promotion_candidate_id": self.promotion_candidate_id,
            "source_module": self.source_module,
            "status": self.status,
            "strategy_id": self.strategy_id,
            "target_module": self.target_module,
        }


@dataclass(frozen=True, slots=True)
class PromotionGateResult:
    """One machine-readable research promotion gate result."""

    name: str
    status: str
    observed: Any
    threshold: Any
    reason: str

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready gate result."""

        return {
            "name": self.name,
            "observed": self.observed,
            "reason": self.reason,
            "status": self.status,
            "threshold": self.threshold,
        }


@dataclass(frozen=True, slots=True)
class ResearchPromotionDecision:
    """Research-system promotion decision for one run."""

    run_id: str
    strategy_id: str
    status: str
    gates: tuple[PromotionGateResult, ...]
    warnings: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready promotion decision."""

        return {
            "gates": [gate.to_payload() for gate in self.gates],
            "promotion_boundary": "research_evidence_only",
            "run_id": self.run_id,
            "status": self.status,
            "strategy_id": self.strategy_id,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class ResearchPromotionPolicy:
    """Evaluate anti-overfit controls for research promotion evidence."""

    min_oos_months: float
    min_oos_trade_count: float
    min_oos_sharpe: float
    min_profit_factor: float
    max_drawdown: float
    max_cost_impact: float
    max_slippage_sensitivity: float
    min_parameter_stability: float
    min_walk_forward_consistency: float
    max_correlation_to_active: float

    @classmethod
    def from_yaml(cls, path: Path) -> ResearchPromotionPolicy:
        """Load a promotion policy YAML file."""

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("promotion config must be a YAML mapping")
        gates = payload.get("research_gates", payload)
        if not isinstance(gates, dict):
            raise ValueError("research_gates must be a mapping")
        return cls(
            min_oos_months=_float(gates, "min_oos_months"),
            min_oos_trade_count=_float(gates, "min_oos_trade_count"),
            min_oos_sharpe=_float(gates, "min_oos_sharpe"),
            min_profit_factor=_float(gates, "min_profit_factor"),
            max_drawdown=_float(gates, "max_drawdown"),
            max_cost_impact=_float(gates, "max_cost_impact"),
            max_slippage_sensitivity=_float(gates, "max_slippage_sensitivity"),
            min_parameter_stability=_float(gates, "min_parameter_stability"),
            min_walk_forward_consistency=_float(gates, "min_walk_forward_consistency"),
            max_correlation_to_active=_float(gates, "max_correlation_to_active"),
        )

    def evaluate(
        self,
        *,
        run_id: str,
        strategy_id: str,
        metrics: Mapping[str, Any],
        reproducibility: Mapping[str, Any],
    ) -> ResearchPromotionDecision:
        """Evaluate research metrics without creating paper/live approval."""

        gates = (
            self._min_gate(
                metrics,
                "minimum_oos_months",
                "trading",
                "oos_months",
                self.min_oos_months,
            ),
            self._min_gate(
                metrics,
                "minimum_oos_trade_count",
                "trading",
                "oos_trade_count",
                self.min_oos_trade_count,
            ),
            self._min_gate(metrics, "oos_sharpe", "quality", "sharpe", self.min_oos_sharpe),
            self._min_gate(
                metrics,
                "profit_factor",
                "quality",
                "profit_factor",
                self.min_profit_factor,
            ),
            self._max_gate(metrics, "max_drawdown", "risk", "max_drawdown", self.max_drawdown),
            self._max_gate(
                metrics,
                "cost_impact",
                "execution",
                "cost_impact",
                self.max_cost_impact,
            ),
            self._max_gate(
                metrics,
                "slippage_stress",
                "execution",
                "slippage_sensitivity",
                self.max_slippage_sensitivity,
            ),
            self._min_gate(
                metrics,
                "parameter_neighborhood_stability",
                "stability",
                "parameter_sensitivity",
                self.min_parameter_stability,
            ),
            self._min_gate(
                metrics,
                "walk_forward_consistency",
                "stability",
                "walk_forward_consistency",
                self.min_walk_forward_consistency,
            ),
            self._max_gate(
                metrics,
                "correlation_to_active_strategies",
                "portfolio",
                "correlation_to_active",
                self.max_correlation_to_active,
            ),
            self._bool_gate(
                metrics,
                "deterministic_replay",
                "research",
                "deterministic_replay_passed",
            ),
            self._bool_gate(metrics, "no_lookahead", "research", "no_lookahead_passed"),
        )
        warnings: tuple[str, ...] = ()
        if reproducibility.get("git_dirty") is True:
            warnings = ("git worktree was dirty during research run",)
        status = "research_passed"
        failed = [gate for gate in gates if gate.status != "passed"]
        if failed:
            status = (
                "quarantined"
                if any(
                    gate.name == "deterministic_replay" and gate.status == "failed"
                    for gate in failed
                )
                else "rejected"
            )
        return ResearchPromotionDecision(
            run_id=run_id,
            strategy_id=strategy_id,
            status=status,
            gates=gates,
            warnings=warnings,
        )

    def _min_gate(
        self,
        metrics: Mapping[str, Any],
        name: str,
        group: str,
        field_name: str,
        threshold: float,
    ) -> PromotionGateResult:
        observed = _optional_float(metric_value(metrics, group, field_name))
        if observed is None:
            return PromotionGateResult(
                name,
                "missing",
                None,
                threshold,
                f"{group}.{field_name} missing",
            )
        passed = observed >= threshold
        return PromotionGateResult(
            name,
            "passed" if passed else "failed",
            observed,
            threshold,
            f"{group}.{field_name} must be >= {threshold}",
        )

    def _max_gate(
        self,
        metrics: Mapping[str, Any],
        name: str,
        group: str,
        field_name: str,
        threshold: float,
    ) -> PromotionGateResult:
        observed = _optional_float(metric_value(metrics, group, field_name))
        if observed is None:
            return PromotionGateResult(
                name,
                "missing",
                None,
                threshold,
                f"{group}.{field_name} missing",
            )
        passed = observed <= threshold
        return PromotionGateResult(
            name,
            "passed" if passed else "failed",
            observed,
            threshold,
            f"{group}.{field_name} must be <= {threshold}",
        )

    @staticmethod
    def _bool_gate(
        metrics: Mapping[str, Any],
        name: str,
        group: str,
        field_name: str,
    ) -> PromotionGateResult:
        observed = metric_value(metrics, group, field_name)
        if observed is None:
            return PromotionGateResult(name, "missing", None, True, f"{group}.{field_name} missing")
        passed = observed is True
        return PromotionGateResult(
            name,
            "passed" if passed else "failed",
            observed,
            True,
            f"{group}.{field_name} must be true",
        )


def _reject_research_only_params(params: Mapping[str, Any]) -> None:
    for key in params:
        if str(key) in _RESEARCH_ONLY_PARAMS:
            raise ValueError(f"research-only parameter is not allowed in promotion spec: {key}")


def _float(payload: Mapping[str, Any], field_name: str) -> float:
    value = payload.get(field_name)
    if value is None:
        raise ValueError(f"{field_name} is required")
    return float(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


_PROMOTION_STATUSES = frozenset(
    {
        "candidate",
        "live_approved",
        "live_candidate",
        "paper_candidate",
        "paper_passed",
        "quarantined",
        "rejected",
        "research_passed",
        "retired",
        "review_required",
        "small_live_candidate",
    }
)
_READINESS_REQUIRED_STATUSES = frozenset(
    {"live_approved", "live_candidate", "paper_candidate", "paper_passed", "small_live_candidate"}
)
_APPROVED_PROMOTION_TARGET_PREFIXES = ("strategies.production.",)
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


__all__ = [
    "PaperReadinessChecklist",
    "PromotionCandidateSpec",
    "PromotionGateResult",
    "ResearchPromotionDecision",
    "ResearchPromotionPolicy",
]
