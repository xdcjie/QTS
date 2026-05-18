"""Post-run optimizer validation constraints."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, ClassVar, Protocol

from qts.research.optimizer.result import OptimizationResult


@dataclass(frozen=True, slots=True)
class ConstraintDecision:
    """Result of applying one validation constraint to one optimizer result."""

    accepted: bool
    reason: str


class OptimizationConstraint(Protocol):
    """Contract for constraints that mark optimizer results accepted or rejected."""

    def evaluate(self, result: OptimizationResult) -> ConstraintDecision:
        """Return the validation decision for one optimization result."""


@dataclass(frozen=True, slots=True)
class MetricConstraint:
    """Validate a Decimal metric from the run manifest against a threshold."""

    metric_name: str
    operator: str
    threshold: Decimal

    _OPERATORS: ClassVar[dict[str, Callable[[Decimal, Decimal], bool]]] = {
        ">": lambda left, right: left > right,
        ">=": lambda left, right: left >= right,
        "<": lambda left, right: left < right,
        "<=": lambda left, right: left <= right,
        "==": lambda left, right: left == right,
    }
    _MISSING: ClassVar[object] = object()

    def __post_init__(self) -> None:
        if not self.metric_name.strip():
            raise ValueError("metric_name must not be empty")
        if self.operator not in self._OPERATORS:
            raise ValueError(f"unsupported constraint operator: {self.operator!r}")
        threshold = Decimal(str(self.threshold))
        if not threshold.is_finite():
            raise ValueError("constraint threshold must be finite")
        object.__setattr__(self, "threshold", threshold)

    def evaluate(self, result: OptimizationResult) -> ConstraintDecision:
        """Evaluate this constraint against metrics in the result manifest."""
        raw_metric = self._read_manifest_metric_value(result.manifest_path)
        if raw_metric is self._MISSING:
            return ConstraintDecision(
                accepted=False,
                reason=(
                    f"metric {self.metric_name!r} missing from manifest {result.manifest_path}"
                ),
            )
        try:
            metric = Decimal(str(raw_metric))
        except (InvalidOperation, ValueError):
            return ConstraintDecision(
                accepted=False,
                reason=(f"{self.metric_name} value {str(raw_metric)!r} is not Decimal-parseable"),
            )
        if not metric.is_finite():
            return ConstraintDecision(
                accepted=False,
                reason=f"{self.metric_name} value {str(raw_metric)!r} is not finite",
            )
        accepted = self._OPERATORS[self.operator](metric, self.threshold)
        comparison = f"{self.operator} {self.threshold}"
        if accepted:
            return ConstraintDecision(
                accepted=True,
                reason=f"{self.metric_name}={metric} satisfied {comparison}",
            )
        return ConstraintDecision(
            accepted=False,
            reason=f"{self.metric_name}={metric} failed {comparison}",
        )

    def _read_manifest_metric_value(self, manifest_path: Path) -> Any:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        for section in ("statistics", "metrics"):
            block = payload.get(section)
            if not isinstance(block, dict) or self.metric_name not in block:
                continue
            return block[self.metric_name]
        return self._MISSING


__all__ = ["ConstraintDecision", "MetricConstraint", "OptimizationConstraint"]
