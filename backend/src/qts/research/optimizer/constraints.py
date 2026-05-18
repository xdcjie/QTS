"""Post-run optimizer validation constraints."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import ClassVar, Protocol

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

    def __post_init__(self) -> None:
        if not self.metric_name.strip():
            raise ValueError("metric_name must not be empty")
        if self.operator not in self._OPERATORS:
            raise ValueError(f"unsupported constraint operator: {self.operator!r}")
        object.__setattr__(self, "threshold", Decimal(str(self.threshold)))

    def evaluate(self, result: OptimizationResult) -> ConstraintDecision:
        """Evaluate this constraint against metrics in the result manifest."""
        metric = self._read_manifest_metric(result.manifest_path)
        if metric is None:
            return ConstraintDecision(
                accepted=False,
                reason=(
                    f"metric {self.metric_name!r} missing from manifest {result.manifest_path}"
                ),
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

    def _read_manifest_metric(self, manifest_path: Path) -> Decimal | None:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        for section in ("statistics", "metrics"):
            block = payload.get(section)
            if not isinstance(block, dict) or self.metric_name not in block:
                continue
            try:
                return Decimal(str(block[self.metric_name]))
            except (InvalidOperation, ValueError):
                return None
        return None


__all__ = ["ConstraintDecision", "MetricConstraint", "OptimizationConstraint"]
