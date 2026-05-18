"""Optimizer validation summary artifacts."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.research.optimizer.constraints import OptimizationConstraint
from qts.research.optimizer.result import OptimizationResult
from qts.research.optimizer.walk_forward import WalkForwardPlan


@dataclass(frozen=True, slots=True)
class OptimizerValidationSummary:
    """Accepted/rejected optimizer run summary with validation evidence."""

    run_count: int
    accepted_count: int
    rejected_count: int
    accepted_runs: tuple[dict[str, Any], ...]
    rejections: tuple[dict[str, Any], ...]
    walk_forward_splits: tuple[dict[str, str], ...] = ()

    @classmethod
    def from_results(
        cls,
        results: Sequence[OptimizationResult],
        constraints: Iterable[OptimizationConstraint] = (),
        *,
        walk_forward_plan: WalkForwardPlan | None = None,
    ) -> OptimizerValidationSummary:
        """Build a validation summary from ranked optimizer results."""
        materialized_constraints = tuple(constraints)
        accepted_runs: list[dict[str, Any]] = []
        rejections: list[dict[str, Any]] = []
        for result in results:
            failed_reasons: list[str] = []
            for constraint in materialized_constraints:
                decision = constraint.evaluate(result)
                if not decision.accepted:
                    failed_reasons.append(decision.reason)
            run_evidence = cls._result_evidence(result)
            if failed_reasons:
                rejections.append({**run_evidence, "reasons": tuple(failed_reasons)})
            else:
                accepted_runs.append(run_evidence)

        return cls(
            run_count=len(results),
            accepted_count=len(accepted_runs),
            rejected_count=len(rejections),
            accepted_runs=tuple(accepted_runs),
            rejections=tuple(rejections),
            walk_forward_splits=(
                () if walk_forward_plan is None else walk_forward_plan.to_metadata()
            ),
        )

    @staticmethod
    def _result_evidence(result: OptimizationResult) -> dict[str, Any]:
        return {
            "manifest_hash": result.manifest_hash,
            "manifest_path": str(result.manifest_path),
            "objective_value": str(result.objective_value),
            "parameters": OptimizerValidationSummary._json_safe_parameters(result.parameters),
        }

    @staticmethod
    def _json_safe_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
        return {
            str(name): OptimizerValidationSummary._json_safe_parameter_value(value, path=str(name))
            for name, value in parameters.items()
        }

    @staticmethod
    def _json_safe_parameter_value(value: Any, *, path: str) -> Any:
        if isinstance(value, Decimal):
            if not value.is_finite():
                raise ValueError(f"optimizer parameter {path} must be finite")
            return str(value)
        if value is None or isinstance(value, (str, bool, int)):
            return value
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(f"optimizer parameter {path} must be finite")
            return value
        if isinstance(value, (list, tuple)):
            return [
                OptimizerValidationSummary._json_safe_parameter_value(item, path=f"{path}[{index}]")
                for index, item in enumerate(value)
            ]
        raise ValueError(f"unsupported optimizer parameter value at {path}: {type(value).__name__}")

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready payload."""
        return {
            "accepted_count": self.accepted_count,
            "accepted_runs": self.accepted_runs,
            "rejected_count": self.rejected_count,
            "rejections": self.rejections,
            "run_count": self.run_count,
            "walk_forward_splits": self.walk_forward_splits,
        }


class OptimizerValidationSummaryWriter:
    """Write optimizer validation summaries as deterministic JSON artifacts."""

    def write(self, path: Path, summary: OptimizerValidationSummary) -> None:
        """Write ``summary`` to ``path`` with stable formatting."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(summary.to_payload(), sort_keys=True, indent=2)
        path.write_text(f"{payload}\n", encoding="utf-8")


__all__ = ["OptimizerValidationSummary", "OptimizerValidationSummaryWriter"]
