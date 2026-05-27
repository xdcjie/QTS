"""Deterministic analytics over autonomous research fitness landscapes."""

from __future__ import annotations

import statistics
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.research.landscape.store import FitnessLandscape, FitnessLandscapePoint


@dataclass(frozen=True, slots=True)
class FamilyPerformanceSummary:
    """Risk-adjusted performance summary for a strategy/factor family."""

    strategy_family: str
    factor_family: str
    trial_count: int
    accepted_count: int
    family_success_rate: float
    median_oos_sharpe: float
    tail_drawdown: float
    cost_sensitivity: float
    risk_adjusted_score: float
    evidence_refs: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready family summary."""

        return {
            "accepted_count": self.accepted_count,
            "cost_sensitivity": self.cost_sensitivity,
            "evidence_refs": list(self.evidence_refs),
            "factor_family": self.factor_family,
            "family_success_rate": self.family_success_rate,
            "median_oos_sharpe": self.median_oos_sharpe,
            "risk_adjusted_score": self.risk_adjusted_score,
            "strategy_family": self.strategy_family,
            "tail_drawdown": self.tail_drawdown,
            "trial_count": self.trial_count,
        }


@dataclass(frozen=True, slots=True)
class ParameterRegionSummary:
    """Observed performance for one parameter hash region."""

    parameter_hash: str
    trial_count: int
    accepted_count: int
    median_train_sharpe: float
    median_oos_sharpe: float
    overfit: bool
    evidence_refs: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready parameter-region summary."""

        return {
            "accepted_count": self.accepted_count,
            "evidence_refs": list(self.evidence_refs),
            "median_oos_sharpe": self.median_oos_sharpe,
            "median_train_sharpe": self.median_train_sharpe,
            "overfit": self.overfit,
            "parameter_hash": self.parameter_hash,
            "trial_count": self.trial_count,
        }


@dataclass(frozen=True, slots=True)
class RegimePerformanceSummary:
    """Fitness stability by market regime."""

    regime: str
    trial_count: int
    accepted_count: int
    median_oos_sharpe: float
    tail_drawdown: float
    regime_stability: float
    evidence_refs: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready regime summary."""

        return {
            "accepted_count": self.accepted_count,
            "evidence_refs": list(self.evidence_refs),
            "median_oos_sharpe": self.median_oos_sharpe,
            "regime": self.regime,
            "regime_stability": self.regime_stability,
            "tail_drawdown": self.tail_drawdown,
            "trial_count": self.trial_count,
        }


@dataclass(frozen=True, slots=True)
class RejectionClusterSummary:
    """Aggregated rejection reason cluster."""

    reason: str
    count: int
    trial_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready rejection cluster summary."""

        return {
            "count": self.count,
            "evidence_refs": list(self.evidence_refs),
            "reason": self.reason,
            "trial_ids": list(self.trial_ids),
        }


@dataclass(frozen=True, slots=True)
class FitnessAnalytics:
    """Deterministic, proposal-ready analytics from a fitness landscape."""

    points: tuple[FitnessLandscapePoint, ...]
    family_summaries: tuple[FamilyPerformanceSummary, ...]
    parameter_regions: tuple[ParameterRegionSummary, ...]
    regime_summaries: tuple[RegimePerformanceSummary, ...]
    rejection_clusters: tuple[RejectionClusterSummary, ...]

    @classmethod
    def from_landscape(cls, landscape: FitnessLandscape) -> FitnessAnalytics:
        """Summarize a fitness landscape deterministically."""

        points = tuple(sorted(landscape.points, key=lambda point: point.sort_key))
        return cls(
            points=points,
            family_summaries=cls._family_summaries(points),
            parameter_regions=cls._parameter_regions(points),
            regime_summaries=cls._regime_summaries(points),
            rejection_clusters=cls._rejection_clusters(points),
        )

    @property
    def analytics_hash(self) -> str:
        """Return the deterministic hash of the analytics artifact."""

        return stable_json_hash(self._payload_without_hash())

    @property
    def best_family(self) -> FamilyPerformanceSummary | None:
        """Return the highest risk-adjusted family summary."""

        if not self.family_summaries:
            return None
        return sorted(
            self.family_summaries,
            key=lambda summary: (
                -summary.risk_adjusted_score,
                summary.strategy_family,
                summary.factor_family,
            ),
        )[0]

    def to_payload(self) -> dict[str, Any]:
        """Return deterministic JSON-ready analytics output."""

        payload = self._payload_without_hash()
        payload["analytics_hash"] = self.analytics_hash
        return payload

    def _payload_without_hash(self) -> dict[str, Any]:
        best_family = self.best_family
        return {
            "best_family": None if best_family is None else best_family.to_payload(),
            "family_summaries": [summary.to_payload() for summary in self.family_summaries],
            "parameter_regions": [summary.to_payload() for summary in self.parameter_regions],
            "regime_summaries": [summary.to_payload() for summary in self.regime_summaries],
            "rejection_clusters": [summary.to_payload() for summary in self.rejection_clusters],
            "trial_count": len(self.points),
        }

    @classmethod
    def _family_summaries(
        cls,
        points: tuple[FitnessLandscapePoint, ...],
    ) -> tuple[FamilyPerformanceSummary, ...]:
        groups = cls._group_points(
            points,
            key=lambda point: (point.strategy_family, point.factor_family),
        )
        summaries: list[FamilyPerformanceSummary] = []
        for (strategy_family, factor_family), family_points in groups.items():
            accepted_count = sum(1 for point in family_points if point.accepted)
            trial_count = len(family_points)
            success_rate = accepted_count / trial_count
            median_oos_sharpe = cls._median_metric(family_points, "performance.oos_sharpe")
            tail_drawdown = max(
                abs(point.metric("performance.max_drawdown")) for point in family_points
            )
            cost_sensitivity = cls._median_metric(family_points, "costs.cost_sensitivity")
            risk_adjusted_score = (
                success_rate * median_oos_sharpe - tail_drawdown - 0.25 * cost_sensitivity
            )
            summaries.append(
                FamilyPerformanceSummary(
                    strategy_family=strategy_family,
                    factor_family=factor_family,
                    trial_count=trial_count,
                    accepted_count=accepted_count,
                    family_success_rate=success_rate,
                    median_oos_sharpe=median_oos_sharpe,
                    tail_drawdown=tail_drawdown,
                    cost_sensitivity=cost_sensitivity,
                    risk_adjusted_score=risk_adjusted_score,
                    evidence_refs=tuple(point.point_hash for point in family_points),
                )
            )
        return tuple(
            sorted(
                summaries,
                key=lambda summary: (
                    -summary.risk_adjusted_score,
                    summary.strategy_family,
                    summary.factor_family,
                ),
            )
        )

    @classmethod
    def _parameter_regions(
        cls,
        points: tuple[FitnessLandscapePoint, ...],
    ) -> tuple[ParameterRegionSummary, ...]:
        groups = cls._group_points(points, key=lambda point: point.parameter_hash)
        summaries: list[ParameterRegionSummary] = []
        for parameter_hash, region_points in groups.items():
            accepted_count = sum(1 for point in region_points if point.accepted)
            median_train = cls._median_metric(region_points, "performance.train_sharpe")
            median_oos = cls._median_metric(region_points, "performance.oos_sharpe")
            reasons = {
                reason.lower() for point in region_points for reason in point.rejected_reasons
            }
            overfit = median_train - median_oos > 1.0 or any(
                "overfit" in reason or "walk_forward" in reason for reason in reasons
            )
            summaries.append(
                ParameterRegionSummary(
                    parameter_hash=parameter_hash,
                    trial_count=len(region_points),
                    accepted_count=accepted_count,
                    median_train_sharpe=median_train,
                    median_oos_sharpe=median_oos,
                    overfit=overfit,
                    evidence_refs=tuple(point.point_hash for point in region_points),
                )
            )
        return tuple(sorted(summaries, key=lambda summary: summary.parameter_hash))

    @classmethod
    def _regime_summaries(
        cls,
        points: tuple[FitnessLandscapePoint, ...],
    ) -> tuple[RegimePerformanceSummary, ...]:
        groups = cls._group_points(points, key=lambda point: point.regime)
        summaries: list[RegimePerformanceSummary] = []
        for regime, regime_points in groups.items():
            accepted_count = sum(1 for point in regime_points if point.accepted)
            success_rate = accepted_count / len(regime_points)
            median_oos = cls._median_metric(regime_points, "performance.oos_sharpe")
            tail_drawdown = max(
                abs(point.metric("performance.max_drawdown")) for point in regime_points
            )
            regime_stability = success_rate + max(0.0, median_oos) / (1.0 + tail_drawdown)
            summaries.append(
                RegimePerformanceSummary(
                    regime=regime,
                    trial_count=len(regime_points),
                    accepted_count=accepted_count,
                    median_oos_sharpe=median_oos,
                    tail_drawdown=tail_drawdown,
                    regime_stability=regime_stability,
                    evidence_refs=tuple(point.point_hash for point in regime_points),
                )
            )
        return tuple(
            sorted(
                summaries,
                key=lambda summary: (-summary.regime_stability, summary.regime),
            )
        )

    @staticmethod
    def _rejection_clusters(
        points: tuple[FitnessLandscapePoint, ...],
    ) -> tuple[RejectionClusterSummary, ...]:
        groups: dict[str, list[FitnessLandscapePoint]] = {}
        for point in points:
            for reason in point.rejected_reasons:
                groups.setdefault(reason, []).append(point)
        summaries = tuple(
            RejectionClusterSummary(
                reason=reason,
                count=len(cluster_points),
                trial_ids=tuple(point.trial_id for point in cluster_points),
                evidence_refs=tuple(point.point_hash for point in cluster_points),
            )
            for reason, cluster_points in groups.items()
        )
        return tuple(sorted(summaries, key=lambda summary: (-summary.count, summary.reason)))

    @staticmethod
    def _median_metric(points: Iterable[FitnessLandscapePoint], path: str) -> float:
        values = [point.metric(path) for point in points]
        if not values:
            return 0.0
        return float(statistics.median(values))

    @staticmethod
    def _group_points(
        points: Iterable[FitnessLandscapePoint],
        *,
        key: Any,
    ) -> dict[Any, tuple[FitnessLandscapePoint, ...]]:
        grouped: dict[Any, list[FitnessLandscapePoint]] = {}
        for point in points:
            grouped.setdefault(key(point), []).append(point)
        return {
            group_key: tuple(sorted(group_points, key=lambda point: point.sort_key))
            for group_key, group_points in sorted(grouped.items(), key=lambda item: item[0])
        }


__all__ = [
    "FamilyPerformanceSummary",
    "FitnessAnalytics",
    "ParameterRegionSummary",
    "RegimePerformanceSummary",
    "RejectionClusterSummary",
]
