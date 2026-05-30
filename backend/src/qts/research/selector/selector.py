"""Evidence-aware autonomous research candidate selector."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.metrics_schema import ResearchMetricsSchema
from qts.research.selector.multiplicity_adjustment import (
    CandidateStatistics,
    MultiplicityAdjustmentResult,
    ResearchMultiplicityAdjustment,
)


@dataclass(frozen=True, slots=True)
class SelectionPolicy:
    """Thresholds and weights for promotion-grade research candidate selection."""

    max_drawdown: float = 0.25
    min_oos_trade_count: int = 30
    min_profit_factor: float | None = None
    max_selected: int | None = None
    purpose: str = "candidate_selection"
    total_return_metric: str = "performance.total_return"
    oos_sharpe_metric: str = "performance.oos_sharpe"
    max_drawdown_metric: str = "performance.max_drawdown"
    oos_trade_count_metric: str = "trading.oos_trade_count"
    profit_factor_metric: str = "quality.profit_factor"
    cost_sensitivity_metric: str = "costs.cost_sensitivity"
    observed_sharpe_metric: str = "performance.observed_sharpe"
    sample_size_metric: str = "performance.return_observation_count"
    skewness_metric: str = "performance.return_skewness"
    kurtosis_metric: str = "performance.return_kurtosis"
    oos_returns_metric: str = "performance.oos_returns"
    false_discovery_rate: float = 0.10
    composite_weights: Mapping[str, float] = field(
        default_factory=lambda: {
            "total_return": 1.0,
            "oos_sharpe": 1.0,
            "max_drawdown": 1.0,
            "cost_sensitivity": 0.5,
        }
    )

    def __post_init__(self) -> None:
        if self.max_drawdown < 0:
            raise ValueError("max_drawdown must be non-negative")
        if self.min_oos_trade_count < 0:
            raise ValueError("min_oos_trade_count must be non-negative")
        if self.min_profit_factor is not None and self.min_profit_factor <= 0:
            raise ValueError("min_profit_factor must be positive when provided")
        if self.max_selected is not None and self.max_selected < 1:
            raise ValueError("max_selected must be positive when provided")
        if not 0.0 < self.false_discovery_rate <= 1.0:
            raise ValueError("false_discovery_rate must be in (0, 1]")
        if not self.purpose.strip():
            raise ValueError("purpose must not be empty")
        object.__setattr__(
            self,
            "composite_weights",
            {str(name): float(value) for name, value in self.composite_weights.items()},
        )

    def composite_score(self, metrics: Mapping[str, Any]) -> float:
        """Return deterministic risk-adjusted score used for survivor ranking."""

        weights = self.composite_weights
        total_return = self.metric_number(metrics, self.total_return_metric) or 0.0
        oos_sharpe = self.metric_number(metrics, self.oos_sharpe_metric) or 0.0
        drawdown = abs(self.metric_number(metrics, self.max_drawdown_metric) or 0.0)
        cost_sensitivity = self.metric_number(metrics, self.cost_sensitivity_metric) or 0.0
        return (
            weights.get("total_return", 0.0) * total_return
            + weights.get("oos_sharpe", 0.0) * oos_sharpe
            - weights.get("max_drawdown", 0.0) * drawdown
            - weights.get("cost_sensitivity", 0.0) * cost_sensitivity
        )

    def candidate_statistics(
        self,
        candidate_id: str,
        metrics: Mapping[str, Any],
    ) -> CandidateStatistics:
        """Return the statistical inputs the multiplicity adjustment consumes.

        ``observed_sharpe`` falls back to the annualized ``oos_sharpe`` metric when a
        dedicated per-observation Sharpe is not published; ``sample_size`` defaults to
        the OOS trade count. Skewness/kurtosis default to the normal moments
        (``0`` / ``3``) when not published.
        """

        observed_sharpe = self.metric_number(metrics, self.observed_sharpe_metric)
        if observed_sharpe is None:
            observed_sharpe = self.metric_number(metrics, self.oos_sharpe_metric) or 0.0
        sample_size = self.metric_number(metrics, self.sample_size_metric)
        if sample_size is None:
            sample_size = self.metric_number(metrics, self.oos_trade_count_metric) or 0.0
        skewness = self.metric_number(metrics, self.skewness_metric)
        kurtosis = self.metric_number(metrics, self.kurtosis_metric)
        return CandidateStatistics(
            candidate_id=candidate_id,
            raw_score=self.composite_score(metrics),
            observed_sharpe=observed_sharpe,
            sample_size=max(int(sample_size), 0),
            skewness=skewness if skewness is not None else 0.0,
            kurtosis=kurtosis if kurtosis is not None else 3.0,
            oos_returns=self._oos_returns(metrics),
        )

    def _oos_returns(self, metrics: Mapping[str, Any]) -> tuple[float, ...]:
        value = self.metric_value(metrics, self.oos_returns_metric)
        if not isinstance(value, Sequence) or isinstance(value, str):
            return ()
        returns: list[float] = []
        for item in value:
            if isinstance(item, bool) or not isinstance(item, int | float):
                continue
            returns.append(float(item))
        return tuple(returns)

    def metric_number(self, metrics: Mapping[str, Any], path: str) -> float | None:
        """Return a finite numeric metric value from a dotted metrics path."""

        value = self.metric_value(metrics, path)
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, int | float):
            return float(value)
        try:
            return float(str(value))
        except ValueError:
            return None

    @staticmethod
    def metric_value(metrics: Mapping[str, Any], path: str) -> Any:
        """Return a raw value from a dotted mapping path."""

        current: Any = metrics
        for part in path.split("."):
            if not isinstance(current, Mapping):
                return None
            current = current.get(part)
        return current


@dataclass(frozen=True, slots=True)
class SelectedCandidate:
    """One candidate accepted by the selector and ready for gauntlet validation.

    ``composite_score`` is the raw selection objective. ``raw_score`` mirrors it,
    and ``adjusted_score`` is the trial-count / overfitting-corrected objective the
    selector ranks on. ``multiplicity_adjustment`` carries the full per-candidate
    correction payload (deflated/probabilistic Sharpe, PBO, FDR significance).
    """

    candidate_id: str
    selected_rank: int
    composite_score: float
    metrics: Mapping[str, Any]
    evidence: Mapping[str, Any]
    candidate_payload: Mapping[str, Any]
    raw_score: float | None = None
    adjusted_score: float | None = None
    multiplicity_adjustment: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if self.selected_rank < 1:
            raise ValueError("selected_rank must be positive")
        object.__setattr__(self, "metrics", self._json_object(self.metrics, "metrics"))
        object.__setattr__(self, "evidence", self._json_object(self.evidence, "evidence"))
        object.__setattr__(
            self,
            "candidate_payload",
            self._json_object(self.candidate_payload, "candidate_payload"),
        )
        if self.raw_score is None:
            object.__setattr__(self, "raw_score", self.composite_score)
        if self.adjusted_score is None:
            object.__setattr__(self, "adjusted_score", self.raw_score)
        if self.multiplicity_adjustment is not None:
            object.__setattr__(
                self,
                "multiplicity_adjustment",
                self._json_object(self.multiplicity_adjustment, "multiplicity_adjustment"),
            )

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready selected candidate evidence."""

        payload: dict[str, Any] = {
            "adjusted_score": self.adjusted_score,
            "candidate_id": self.candidate_id,
            "candidate_payload": dict(self.candidate_payload),
            "composite_score": self.composite_score,
            "evidence": dict(self.evidence),
            "metrics": dict(self.metrics),
            "raw_score": self.raw_score,
            "selected_rank": self.selected_rank,
        }
        if self.multiplicity_adjustment is not None:
            payload["multiplicity_adjustment"] = dict(self.multiplicity_adjustment)
        return payload

    @staticmethod
    def _json_object(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
        loaded = json.loads(stable_json_dumps(dict(payload)))
        if not isinstance(loaded, dict):
            raise ValueError(f"{field_name} must be a JSON object")
        return loaded


@dataclass(frozen=True, slots=True)
class RejectedCandidate:
    """One selector rejection with durable, operator-readable reasons."""

    candidate_id: str
    reasons: tuple[str, ...]
    metrics: Mapping[str, Any]
    evidence: Mapping[str, Any]
    candidate_payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if not self.reasons:
            raise ValueError("rejected candidates require at least one reason")
        object.__setattr__(self, "reasons", tuple(str(reason) for reason in self.reasons))
        object.__setattr__(
            self,
            "metrics",
            SelectedCandidate._json_object(self.metrics, "metrics"),
        )
        object.__setattr__(
            self,
            "evidence",
            SelectedCandidate._json_object(self.evidence, "evidence"),
        )
        object.__setattr__(
            self,
            "candidate_payload",
            SelectedCandidate._json_object(self.candidate_payload, "candidate_payload"),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready rejection evidence."""

        return {
            "candidate_id": self.candidate_id,
            "candidate_payload": dict(self.candidate_payload),
            "evidence": dict(self.evidence),
            "metrics": dict(self.metrics),
            "reasons": list(self.reasons),
        }


# Scopes over which the multiple-testing correction is applied. ``generation``
# counts every candidate tried in one research generation; ``family`` narrows the
# count to a single idea family; ``campaign`` spans the whole campaign.
_MULTIPLICITY_SCOPES = frozenset({"generation", "family", "campaign"})


@dataclass(frozen=True, slots=True)
class SelectionResult:
    """Complete selector decision artifact.

    ``trial_count`` is the campaign-level number of configurations tried that the
    multiplicity correction was computed against, ``multiplicity_scope`` records the
    boundary that count spans (``generation`` | ``family`` | ``campaign``), and
    ``false_discovery_rate`` is the Benjamini-Hochberg control level ``q`` the
    selector applied. Serializing all three makes the statistical correction in
    ``selection_result.json`` auditable instead of implicit.
    """

    selected_candidates: tuple[SelectedCandidate, ...]
    rejected_candidates: tuple[RejectedCandidate, ...]
    policy: SelectionPolicy
    trial_count: int = 1
    multiplicity_scope: str = "generation"
    false_discovery_rate: float | None = None

    def __post_init__(self) -> None:
        if self.trial_count < 1:
            raise ValueError("trial_count must be positive")
        if self.multiplicity_scope not in _MULTIPLICITY_SCOPES:
            raise ValueError(
                "multiplicity_scope must be one of "
                f"{sorted(_MULTIPLICITY_SCOPES)}; got {self.multiplicity_scope!r}"
            )
        fdr = (
            self.policy.false_discovery_rate
            if self.false_discovery_rate is None
            else self.false_discovery_rate
        )
        if not 0.0 < fdr <= 1.0:
            raise ValueError("false_discovery_rate must be in (0, 1]")
        object.__setattr__(self, "false_discovery_rate", fdr)

    @property
    def selection_hash(self) -> str:
        """Return the deterministic hash of the selector artifact."""

        return stable_json_hash(self._payload_without_hash())

    def to_payload(self) -> dict[str, Any]:
        """Return deterministic JSON-ready selector output."""

        payload = self._payload_without_hash()
        payload["selection_hash"] = self.selection_hash
        return payload

    def write_artifacts(self, output_dir: Path) -> None:
        """Write selection_result.json plus selected/rejected JSONL artifacts."""

        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "selection_result.json").write_text(
            json.dumps(self.to_payload(), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        self._write_jsonl(
            output_dir / "selected_candidates.jsonl",
            (candidate.to_payload() for candidate in self.selected_candidates),
        )
        self._write_jsonl(
            output_dir / "rejected_candidates.jsonl",
            (candidate.to_payload() for candidate in self.rejected_candidates),
        )

    def _payload_without_hash(self) -> dict[str, Any]:
        return {
            "false_discovery_rate": self.false_discovery_rate,
            "multiplicity_scope": self.multiplicity_scope,
            "policy": {
                "composite_weights": dict(self.policy.composite_weights),
                "cost_sensitivity_metric": self.policy.cost_sensitivity_metric,
                "false_discovery_rate": self.policy.false_discovery_rate,
                "kurtosis_metric": self.policy.kurtosis_metric,
                "max_drawdown": self.policy.max_drawdown,
                "max_drawdown_metric": self.policy.max_drawdown_metric,
                "max_selected": self.policy.max_selected,
                "min_oos_trade_count": self.policy.min_oos_trade_count,
                "min_profit_factor": self.policy.min_profit_factor,
                "observed_sharpe_metric": self.policy.observed_sharpe_metric,
                "oos_returns_metric": self.policy.oos_returns_metric,
                "oos_sharpe_metric": self.policy.oos_sharpe_metric,
                "oos_trade_count_metric": self.policy.oos_trade_count_metric,
                "profit_factor_metric": self.policy.profit_factor_metric,
                "purpose": self.policy.purpose,
                "sample_size_metric": self.policy.sample_size_metric,
                "skewness_metric": self.policy.skewness_metric,
                "total_return_metric": self.policy.total_return_metric,
            },
            "rejected_candidates": [
                candidate.to_payload() for candidate in self.rejected_candidates
            ],
            "rejected_count": len(self.rejected_candidates),
            "selected_candidates": [
                candidate.to_payload() for candidate in self.selected_candidates
            ],
            "selected_count": len(self.selected_candidates),
            "trial_count": self.trial_count,
        }

    @staticmethod
    def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")


class CandidateSelector:
    """Applies hard evidence gates and ranks surviving research candidates."""

    def __init__(self, policy: SelectionPolicy) -> None:
        self.policy = policy

    def select(
        self,
        candidate_results: Iterable[Mapping[str, Any]],
        *,
        metrics_schema: ResearchMetricsSchema | None = None,
        trial_count: int = 1,
        multiplicity_scope: str = "generation",
    ) -> SelectionResult:
        """Return selected/rejected candidates for a completed research generation.

        ``trial_count`` is the number of configurations tried in the family
        (threaded from the search budget). It feeds the multiplicity adjustment:
        with more trials the expected-maximum-Sharpe haircut grows, every adjusted
        score drops, and the acceptance threshold rises. With the default of ``1``
        there is no inflation and the adjusted score equals the raw objective.
        ``multiplicity_scope`` (``generation`` | ``family`` | ``campaign``) records
        the boundary that ``trial_count`` spans so the correction is auditable on
        the produced ``SelectionResult``.
        """

        if trial_count < 1:
            raise ValueError("trial_count must be positive")
        if multiplicity_scope not in _MULTIPLICITY_SCOPES:
            raise ValueError(
                "multiplicity_scope must be one of "
                f"{sorted(_MULTIPLICITY_SCOPES)}; got {multiplicity_scope!r}"
            )

        survivors: list[SelectedCandidate] = []
        rejections: list[RejectedCandidate] = []
        for raw_candidate in candidate_results:
            candidate = self._json_candidate(raw_candidate)
            candidate_id = self._candidate_id(candidate)
            metrics = self._metrics(candidate)
            evidence = self._evidence(candidate)
            reasons = self._rejection_reasons(candidate, metrics, metrics_schema)
            if reasons:
                rejections.append(
                    RejectedCandidate(
                        candidate_id=candidate_id,
                        reasons=reasons,
                        metrics=metrics,
                        evidence=evidence,
                        candidate_payload=candidate,
                    )
                )
                continue
            survivors.append(
                SelectedCandidate(
                    candidate_id=candidate_id,
                    selected_rank=1,
                    composite_score=self.policy.composite_score(metrics),
                    metrics=metrics,
                    evidence=evidence,
                    candidate_payload=candidate,
                )
            )

        adjustments = self._adjustments(survivors, trial_count)
        survivors = [self._with_adjustment(survivor, adjustments) for survivor in survivors]
        ranked = sorted(
            survivors,
            key=lambda survivor: (-(survivor.adjusted_score or 0.0), survivor.candidate_id),
        )
        selected: list[SelectedCandidate] = []
        max_selected = self.policy.max_selected or len(ranked)
        for rank, survivor in enumerate(ranked, start=1):
            if rank <= max_selected:
                selected.append(
                    SelectedCandidate(
                        candidate_id=survivor.candidate_id,
                        selected_rank=rank,
                        composite_score=survivor.composite_score,
                        metrics=survivor.metrics,
                        evidence=survivor.evidence,
                        candidate_payload=survivor.candidate_payload,
                        raw_score=survivor.raw_score,
                        adjusted_score=survivor.adjusted_score,
                        multiplicity_adjustment=survivor.multiplicity_adjustment,
                    )
                )
            else:
                rejections.append(
                    RejectedCandidate(
                        candidate_id=survivor.candidate_id,
                        reasons=(f"selection_budget: rank {rank} exceeds {max_selected}",),
                        metrics=survivor.metrics,
                        evidence=survivor.evidence,
                        candidate_payload=survivor.candidate_payload,
                    )
                )

        return SelectionResult(
            selected_candidates=tuple(selected),
            rejected_candidates=tuple(
                sorted(rejections, key=lambda candidate: candidate.candidate_id)
            ),
            policy=self.policy,
            trial_count=trial_count,
            multiplicity_scope=multiplicity_scope,
            false_discovery_rate=self.policy.false_discovery_rate,
        )

    def _adjustments(
        self,
        survivors: Sequence[SelectedCandidate],
        trial_count: int,
    ) -> dict[str, MultiplicityAdjustmentResult]:
        if not survivors:
            return {}
        statistics = [
            self.policy.candidate_statistics(survivor.candidate_id, survivor.metrics)
            for survivor in survivors
        ]
        adjustment = ResearchMultiplicityAdjustment(
            trial_count=trial_count,
            false_discovery_rate=self.policy.false_discovery_rate,
            objective_sharpe_key="oos_sharpe",
            composite_weights=self.policy.composite_weights,
        )
        return {result.candidate_id: result for result in adjustment.adjust(statistics)}

    @staticmethod
    def _with_adjustment(
        survivor: SelectedCandidate,
        adjustments: Mapping[str, MultiplicityAdjustmentResult],
    ) -> SelectedCandidate:
        result = adjustments.get(survivor.candidate_id)
        if result is None:
            return survivor
        return SelectedCandidate(
            candidate_id=survivor.candidate_id,
            selected_rank=survivor.selected_rank,
            composite_score=survivor.composite_score,
            metrics=survivor.metrics,
            evidence=survivor.evidence,
            candidate_payload={
                **dict(survivor.candidate_payload),
                "multiplicity_adjustment": result.to_payload(),
            },
            raw_score=result.raw_score,
            adjusted_score=result.adjusted_score,
            multiplicity_adjustment=result.to_payload(),
        )

    def _rejection_reasons(
        self,
        candidate: Mapping[str, Any],
        metrics: Mapping[str, Any],
        metrics_schema: ResearchMetricsSchema | None,
    ) -> tuple[str, ...]:
        schema_reasons = self._metrics_schema_reasons(metrics, metrics_schema)
        if schema_reasons:
            return schema_reasons

        reasons: list[str] = []
        drawdown = self.policy.metric_number(metrics, self.policy.max_drawdown_metric)
        if drawdown is None:
            reasons.append(f"{self.policy.max_drawdown_metric}: metric is required")
        elif abs(drawdown) > self.policy.max_drawdown:
            reasons.append(
                f"max_drawdown: {self._metric_text(abs(drawdown))} "
                f"exceeds {self._metric_text(self.policy.max_drawdown)}"
            )

        trade_count = self.policy.metric_number(metrics, self.policy.oos_trade_count_metric)
        if trade_count is None:
            reasons.append(f"{self.policy.oos_trade_count_metric}: metric is required")
        elif int(trade_count) < self.policy.min_oos_trade_count:
            reasons.append(
                f"oos_trade_count: {int(trade_count)} below {self.policy.min_oos_trade_count}"
            )

        if self.policy.min_profit_factor is not None:
            profit_factor = self.policy.metric_number(metrics, self.policy.profit_factor_metric)
            if profit_factor is None:
                reasons.append(f"{self.policy.profit_factor_metric}: metric is required")
            elif profit_factor < self.policy.min_profit_factor:
                reasons.append(
                    f"profit_factor: {self._metric_text(profit_factor)} "
                    f"below {self._metric_text(self.policy.min_profit_factor)}"
                )

        reasons.extend(self._data_quality_reasons(candidate.get("data_quality")))
        reasons.extend(self._reproducibility_reasons(candidate.get("reproducibility")))
        return tuple(reasons)

    def _metrics_schema_reasons(
        self,
        metrics: Mapping[str, Any],
        metrics_schema: ResearchMetricsSchema | None,
    ) -> tuple[str, ...]:
        if metrics_schema is None:
            return ()
        validation = metrics_schema.validate(metrics, purpose=self.policy.purpose)
        return tuple(f"metrics_schema: {reason}" for reason in validation.reasons)

    @staticmethod
    def _data_quality_reasons(data_quality: Any) -> tuple[str, ...]:
        if data_quality is None:
            return ("data_quality: artifact missing",)
        accepted = bool(getattr(data_quality, "accepted", False))
        blockers: Sequence[Any] = ()
        if isinstance(data_quality, Mapping):
            accepted = bool(data_quality.get("accepted", False))
            raw_blockers = data_quality.get("blockers", ())
            if isinstance(raw_blockers, Sequence) and not isinstance(raw_blockers, str):
                blockers = raw_blockers
        elif hasattr(data_quality, "blockers"):
            blockers = data_quality.blockers()
        if not accepted:
            return ("data_quality: artifact rejected",)
        return tuple(
            f"data_quality: {blocker.get('code', 'blocker')}"
            for blocker in blockers
            if isinstance(blocker, Mapping)
        )

    @staticmethod
    def _reproducibility_reasons(reproducibility: Any) -> tuple[str, ...]:
        if reproducibility is None:
            return ("reproducibility: snapshot missing",)
        blockers: tuple[str, ...] = ()
        if hasattr(reproducibility, "promotion_blockers"):
            blockers = tuple(str(reason) for reason in reproducibility.promotion_blockers())
        elif isinstance(reproducibility, Mapping):
            blockers = tuple(str(reason) for reason in reproducibility.get("blockers", ()))
            if bool(reproducibility.get("git_dirty")):
                blockers = (*blockers, "git working tree is dirty")
        return tuple(f"reproducibility: {reason}" for reason in blockers)

    @staticmethod
    def _json_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
        loaded = json.loads(stable_json_dumps(dict(candidate)))
        if not isinstance(loaded, dict):
            raise ValueError("candidate must be a JSON object")
        return loaded

    @staticmethod
    def _candidate_id(candidate: Mapping[str, Any]) -> str:
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("candidate_id is required")
        return candidate_id.strip()

    @staticmethod
    def _metrics(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        metrics = candidate.get("metrics")
        if not isinstance(metrics, Mapping):
            raise ValueError("candidate metrics must be a JSON object")
        return metrics

    @staticmethod
    def _evidence(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        evidence = candidate.get("evidence", {})
        if not isinstance(evidence, Mapping):
            raise ValueError("candidate evidence must be a JSON object")
        return evidence

    @staticmethod
    def _metric_text(value: float) -> str:
        return f"{value:g}"


__all__ = [
    "CandidateSelector",
    "CandidateStatistics",
    "MultiplicityAdjustmentResult",
    "RejectedCandidate",
    "SelectedCandidate",
    "SelectionPolicy",
    "SelectionResult",
]
