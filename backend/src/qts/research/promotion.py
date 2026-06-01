"""Research-to-promotion review packet schemas.

These schemas make promotion review machine-readable. They do not create
paper/live runtime configuration and do not approve strategy code by themselves.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.research.metrics import metric_value
from qts.research.metrics_schema import ResearchMetricsSchema

_DEFAULT_METRICS_SCHEMA_PATH = Path("configs/research/metrics/schema_v2.yaml")
_PROMOTION_THRESHOLD_GATE_SPECS = (
    ("min", "minimum_oos_months", "trading", "oos_months"),
    ("min", "minimum_oos_trade_count", "trading", "oos_trade_count"),
    ("min", "oos_sharpe", "quality", "sharpe"),
    ("min", "profit_factor", "quality", "profit_factor"),
    ("max", "max_drawdown", "risk", "max_drawdown"),
    ("max", "cost_impact", "execution", "cost_impact"),
    ("max", "slippage_stress", "execution", "slippage_sensitivity"),
    ("min", "parameter_neighborhood_stability", "stability", "parameter_sensitivity"),
    ("min", "walk_forward_consistency", "stability", "walk_forward_consistency"),
    ("max", "correlation_to_active_strategies", "portfolio", "correlation_to_active"),
)
_PROMOTION_BOOL_GATE_SPECS = (
    ("deterministic_replay", "research", "deterministic_replay_passed"),
    ("no_lookahead", "research", "no_lookahead_passed"),
)


@dataclass(frozen=True, slots=True)
class PromotionGateResult:
    """One machine-readable research promotion gate result."""

    name: str
    status: str
    observed: Any
    threshold: Any
    reason: str
    metric_path: str | None = None
    unit: str | None = None
    direction: str | None = None
    source_artifact_id: str | None = None
    period_role: str | None = None

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready gate result."""

        payload = {
            "name": self.name,
            "observed": self.observed,
            "reason": self.reason,
            "status": self.status,
            "threshold": self.threshold,
        }
        if self.metric_path is not None:
            payload["metric_path"] = self.metric_path
        if self.unit is not None:
            payload["unit"] = self.unit
        if self.direction is not None:
            payload["direction"] = self.direction
        if self.source_artifact_id is not None:
            payload["source_artifact_id"] = self.source_artifact_id
        if self.period_role is not None:
            payload["period_role"] = self.period_role
        return payload


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
    metrics_schema_id: str = "schema_v2"
    metrics_schema_path: Path | str = _DEFAULT_METRICS_SCHEMA_PATH

    @classmethod
    def from_yaml(cls, path: Path) -> ResearchPromotionPolicy:
        """Load a promotion policy YAML file."""

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("promotion config must be a YAML mapping")
        gates = payload.get("research_gates", payload)
        if not isinstance(gates, dict):
            raise ValueError("research_gates must be a mapping")
        raw_schema_id = payload.get("metrics_schema_id", gates.get("metrics_schema_id"))
        if not isinstance(raw_schema_id, str) or not raw_schema_id.strip():
            raise ValueError("metrics_schema_id is required")
        raw_schema_path = payload.get("metrics_schema_path", gates.get("metrics_schema_path"))
        metrics_schema_path: Path | str
        if raw_schema_path is None:
            raise ValueError("metrics_schema_path is required")
        else:
            configured_path = Path(str(raw_schema_path))
            metrics_schema_path = (
                configured_path if configured_path.is_absolute() else path.parent / configured_path
            )
        metrics_schema = ResearchMetricsSchema.from_yaml(Path(metrics_schema_path))
        metrics_schema_id = raw_schema_id.strip()
        if metrics_schema.schema_id != metrics_schema_id:
            raise ValueError(
                f"metrics_schema_id mismatch: {metrics_schema_id} != {metrics_schema.schema_id}"
            )
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
            metrics_schema_id=metrics_schema_id,
            metrics_schema_path=metrics_schema_path,
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

        warnings: tuple[str, ...] = ()
        if reproducibility.get("git_dirty") is True:
            warnings = ("git worktree was dirty during research run",)

        metrics_schema = ResearchMetricsSchema.from_yaml(Path(self.metrics_schema_path))
        schema_id_reason = _metrics_schema_id_mismatch_reason(metrics, self.metrics_schema_id)
        if schema_id_reason is None and metrics_schema.schema_id != self.metrics_schema_id:
            schema_id_reason = (
                "metrics schema id mismatch: "
                f"{self.metrics_schema_id} != {metrics_schema.schema_id}"
            )
        if schema_id_reason is not None:
            return ResearchPromotionDecision(
                run_id=run_id,
                strategy_id=strategy_id,
                status="rejected",
                gates=(
                    PromotionGateResult(
                        "metrics_schema",
                        "failed",
                        self.metrics_schema_id,
                        metrics_schema.schema_id,
                        schema_id_reason,
                    ),
                ),
                warnings=warnings,
            )
        schema_result = metrics_schema.validate(metrics, purpose="promotion")
        if not schema_result.accepted:
            schema_status = (
                "missing"
                if schema_result.reasons
                and all(" missing for " in reason for reason in schema_result.reasons)
                else "failed"
            )
            return ResearchPromotionDecision(
                run_id=run_id,
                strategy_id=strategy_id,
                status="rejected",
                gates=(
                    PromotionGateResult(
                        "metrics_schema",
                        schema_status,
                        schema_result.to_payload(),
                        True,
                        "metrics schema validation failed: " + "; ".join(schema_result.reasons),
                    ),
                ),
                warnings=warnings,
            )

        gate_results: list[PromotionGateResult] = []
        for (gate_kind, name, group, field_name), threshold in zip(
            _PROMOTION_THRESHOLD_GATE_SPECS,
            _promotion_thresholds(self),
            strict=True,
        ):
            gate_fn = self._min_gate if gate_kind == "min" else self._max_gate
            gate_results.append(
                gate_fn(
                    metrics,
                    metrics_schema,
                    name,
                    group,
                    field_name,
                    threshold,
                )
            )
        for name, group, field_name in _PROMOTION_BOOL_GATE_SPECS:
            gate_results.append(self._bool_gate(metrics, metrics_schema, name, group, field_name))
        if metric_value(metrics, "research", "promotion_eligible") is not None:
            gate_results.append(
                self._bool_gate(
                    metrics,
                    metrics_schema,
                    "promotion_eligible",
                    "research",
                    "promotion_eligible",
                )
            )
        gates = tuple(gate_results)
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
        metrics_schema: ResearchMetricsSchema,
        name: str,
        group: str,
        field_name: str,
        threshold: float,
    ) -> PromotionGateResult:
        metric_path = f"{group}.{field_name}"
        unit, direction = _metric_schema_metadata(metrics_schema, metric_path)
        source_artifact_id, period_role = _metric_source_metadata(metrics, metric_path)
        observed = _optional_float(metric_value(metrics, group, field_name))
        if observed is None:
            return PromotionGateResult(
                name,
                "missing",
                None,
                threshold,
                f"{group}.{field_name} missing",
                metric_path=metric_path,
                unit=unit,
                direction=direction,
                source_artifact_id=source_artifact_id,
                period_role=period_role,
            )
        passed = observed >= threshold
        return PromotionGateResult(
            name,
            "passed" if passed else "failed",
            observed,
            threshold,
            f"{group}.{field_name} must be >= {threshold}",
            metric_path=metric_path,
            unit=unit,
            direction=direction,
            source_artifact_id=source_artifact_id,
            period_role=period_role,
        )

    def _max_gate(
        self,
        metrics: Mapping[str, Any],
        metrics_schema: ResearchMetricsSchema,
        name: str,
        group: str,
        field_name: str,
        threshold: float,
    ) -> PromotionGateResult:
        metric_path = f"{group}.{field_name}"
        unit, direction = _metric_schema_metadata(metrics_schema, metric_path)
        source_artifact_id, period_role = _metric_source_metadata(metrics, metric_path)
        observed = _optional_float(metric_value(metrics, group, field_name))
        if observed is None:
            return PromotionGateResult(
                name,
                "missing",
                None,
                threshold,
                f"{group}.{field_name} missing",
                metric_path=metric_path,
                unit=unit,
                direction=direction,
                source_artifact_id=source_artifact_id,
                period_role=period_role,
            )
        passed = observed <= threshold
        return PromotionGateResult(
            name,
            "passed" if passed else "failed",
            observed,
            threshold,
            f"{group}.{field_name} must be <= {threshold}",
            metric_path=metric_path,
            unit=unit,
            direction=direction,
            source_artifact_id=source_artifact_id,
            period_role=period_role,
        )

    @staticmethod
    def _bool_gate(
        metrics: Mapping[str, Any],
        metrics_schema: ResearchMetricsSchema,
        name: str,
        group: str,
        field_name: str,
    ) -> PromotionGateResult:
        metric_path = f"{group}.{field_name}"
        unit, direction = _metric_schema_metadata(metrics_schema, metric_path)
        source_artifact_id, period_role = _metric_source_metadata(metrics, metric_path)
        observed = metric_value(metrics, group, field_name)
        if observed is None:
            return PromotionGateResult(
                name,
                "missing",
                None,
                True,
                f"{group}.{field_name} missing",
                metric_path=metric_path,
                unit=unit,
                direction=direction,
                source_artifact_id=source_artifact_id,
                period_role=period_role,
            )
        passed = observed is True
        return PromotionGateResult(
            name,
            "passed" if passed else "failed",
            observed,
            True,
            f"{group}.{field_name} must be true",
            metric_path=metric_path,
            unit=unit,
            direction=direction,
            source_artifact_id=source_artifact_id,
            period_role=period_role,
        )


def _float(payload: Mapping[str, Any], field_name: str) -> float:
    value = payload.get(field_name)
    if value is None:
        raise ValueError(f"{field_name} is required")
    return float(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _promotion_thresholds(policy: ResearchPromotionPolicy) -> tuple[float, ...]:
    return (
        float(policy.min_oos_months),
        float(policy.min_oos_trade_count),
        float(policy.min_oos_sharpe),
        float(policy.min_profit_factor),
        float(policy.max_drawdown),
        float(policy.max_cost_impact),
        float(policy.max_slippage_sensitivity),
        float(policy.min_parameter_stability),
        float(policy.min_walk_forward_consistency),
        float(policy.max_correlation_to_active),
    )


def _metric_schema_metadata(
    metrics_schema: ResearchMetricsSchema, metric_path: str
) -> tuple[str | None, str | None]:
    definition = metrics_schema.definition_for(metric_path)
    if definition is None:
        return None, None
    return definition.unit, definition.direction


def _metric_source_metadata(
    metrics: Mapping[str, Any], metric_path: str
) -> tuple[str | None, str | None]:
    metadata = metrics.get("_metadata")
    if not isinstance(metadata, Mapping):
        return None, None
    metric_sources = metadata.get("metric_sources")
    if not isinstance(metric_sources, Mapping):
        return None, None
    source = metric_sources.get(metric_path)
    if not isinstance(source, Mapping):
        return None, None
    source_artifact_id = source.get("source_artifact_id")
    period_role = source.get("period_role")
    return (
        source_artifact_id if isinstance(source_artifact_id, str) else None,
        period_role if isinstance(period_role, str) else None,
    )


def _metrics_schema_id_mismatch_reason(
    metrics: Mapping[str, Any],
    expected_schema_id: str,
) -> str | None:
    observed = metrics.get("metrics_schema_id")
    if observed is None:
        metadata = metrics.get("_metadata")
        if isinstance(metadata, Mapping):
            observed = metadata.get("metrics_schema_id")
    if observed is None:
        return None
    if observed != expected_schema_id:
        return f"metrics schema id mismatch: {observed} != {expected_schema_id}"
    return None


__all__ = [
    "PromotionGateResult",
    "ResearchPromotionDecision",
    "ResearchPromotionPolicy",
]
