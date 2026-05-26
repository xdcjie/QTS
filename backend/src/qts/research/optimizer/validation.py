"""Optimizer validation summary artifacts."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from qts.research.optimizer.constraints import MetricConstraint, OptimizationConstraint
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
    robustness_score: Decimal = Decimal("0")
    walk_forward_splits: tuple[dict[str, str], ...] = ()

    @classmethod
    def from_results(
        cls,
        results: Sequence[OptimizationResult],
        constraints: Iterable[OptimizationConstraint] = (),
        *,
        capital_metric_config: dict[str, Any] | None = None,
        walk_forward_plan: WalkForwardPlan | None = None,
    ) -> OptimizerValidationSummary:
        """Build a validation summary from ranked optimizer results."""
        materialized_constraints = tuple(constraints)
        accepted_runs: list[dict[str, Any]] = []
        rejections: list[dict[str, Any]] = []
        should_derive_capital_metrics = _should_derive_capital_metrics(
            materialized_constraints,
            capital_metric_config,
        )
        accepted_rank = 0
        for raw_index, result in enumerate(results, start=1):
            capital_metrics = (
                derive_capital_metrics(result, capital_metric_config)
                if should_derive_capital_metrics
                else {}
            )
            failed_reasons: list[str] = []
            for constraint in materialized_constraints:
                decision = constraint.evaluate(result, capital_metrics)
                if not decision.accepted:
                    failed_reasons.append(decision.reason)
            run_evidence = {
                **cls._result_evidence(result, capital_metrics=capital_metrics),
                "raw_rank": raw_index,
            }
            if failed_reasons:
                rejections.append(
                    {
                        **run_evidence,
                        "accepted_rank": None,
                        "reasons": tuple(failed_reasons),
                        "rejection_reasons": tuple(failed_reasons),
                    }
                )
            else:
                accepted_rank += 1
                accepted_runs.append({**run_evidence, "accepted_rank": accepted_rank})

        return cls(
            run_count=len(results),
            accepted_count=len(accepted_runs),
            rejected_count=len(rejections),
            accepted_runs=tuple(accepted_runs),
            rejections=tuple(rejections),
            robustness_score=_robustness_score(len(accepted_runs), len(results)),
            walk_forward_splits=(
                () if walk_forward_plan is None else walk_forward_plan.to_metadata()
            ),
        )

    @staticmethod
    def _result_evidence(
        result: OptimizationResult,
        *,
        capital_metrics: dict[str, str],
    ) -> dict[str, Any]:
        evidence: dict[str, Any] = {
            "manifest_hash": result.manifest_hash,
            "manifest_path": str(result.manifest_path),
            "objective_value": str(result.objective_value),
            "parameters": OptimizerValidationSummary._json_safe_parameters(result.parameters),
        }
        if capital_metrics:
            evidence["capital_metrics"] = capital_metrics
        return evidence

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
            "robustness_score": _decimal_text(self.robustness_score),
            "run_count": self.run_count,
            "walk_forward_splits": self.walk_forward_splits,
        }


@dataclass(frozen=True, slots=True)
class ResearchValidationPolicy:
    """Hard-gate policy over optimizer validation evidence."""

    require_passing_candidate: bool = False
    min_accepted_count: int | None = None
    min_robustness_score: Decimal | None = None
    require_walk_forward: bool = False
    require_failure_window: bool = False
    require_cost_stress: bool = False
    max_rejected_count: int | None = None

    def __post_init__(self) -> None:
        if self.min_accepted_count is not None and self.min_accepted_count < 0:
            raise ValueError("min_accepted_count must be non-negative")
        if self.max_rejected_count is not None and self.max_rejected_count < 0:
            raise ValueError("max_rejected_count must be non-negative")

    def evaluate(
        self,
        summary: OptimizerValidationSummary,
        *,
        walk_forward_present: bool = False,
        failure_window_present: bool = False,
        cost_stress_present: bool = False,
    ) -> dict[str, Any]:
        """Return machine-readable gate status for optimizer candidate review."""

        reasons: list[str] = []
        missing_evidence: list[str] = []
        if self.require_passing_candidate and summary.accepted_count == 0:
            reasons.append("require_passing_candidate: no accepted optimizer candidate")
        if self.min_accepted_count is not None and summary.accepted_count < self.min_accepted_count:
            reasons.append(
                f"min_accepted_count: {summary.accepted_count} < {self.min_accepted_count}"
            )
        if (
            self.min_robustness_score is not None
            and summary.robustness_score < self.min_robustness_score
        ):
            reasons.append(
                "min_robustness_score: "
                f"{_decimal_text(summary.robustness_score)} < "
                f"{_decimal_text(self.min_robustness_score)}"
            )
        if self.max_rejected_count is not None and summary.rejected_count > self.max_rejected_count:
            reasons.append(
                f"max_rejected_count: {summary.rejected_count} > {self.max_rejected_count}"
            )
        if self.require_walk_forward and not walk_forward_present:
            missing_evidence.append("walk_forward")
        if self.require_failure_window and not failure_window_present:
            missing_evidence.append("failure_window")
        if self.require_cost_stress and not cost_stress_present:
            missing_evidence.append("cost_stress")
        blocked = bool(reasons or missing_evidence)
        return {
            "accepted": not blocked,
            "accepted_count": summary.accepted_count,
            "blocked": blocked,
            "max_rejected_count": self.max_rejected_count,
            "min_accepted_count": self.min_accepted_count,
            "min_robustness_score": (
                None
                if self.min_robustness_score is None
                else _decimal_text(self.min_robustness_score)
            ),
            "missing_evidence": tuple(missing_evidence),
            "reasons": tuple(reasons),
            "rejected_count": summary.rejected_count,
            "rejection_reasons": tuple(
                reason
                for rejection in summary.rejections
                for reason in rejection.get("rejection_reasons", ())
            ),
            "require_cost_stress": self.require_cost_stress,
            "require_failure_window": self.require_failure_window,
            "require_passing_candidate": self.require_passing_candidate,
            "require_walk_forward": self.require_walk_forward,
            "robustness_score": _decimal_text(summary.robustness_score),
        }


class OptimizerValidationSummaryWriter:
    """Write optimizer validation summaries as deterministic JSON artifacts."""

    def write(self, path: Path, summary: OptimizerValidationSummary) -> None:
        """Write ``summary`` to ``path`` with stable formatting."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(summary.to_payload(), sort_keys=True, indent=2)
        path.write_text(f"{payload}\n", encoding="utf-8")


def derive_capital_metrics(
    result: OptimizationResult,
    config: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Derive account-capital research metrics from a backtest manifest."""

    payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    metrics = _manifest_metrics(payload)
    total_return = _optional_decimal(metrics.get("total_return"))
    initial_cash = _initial_cash(payload)
    if total_return is None or initial_cash is None:
        return {}

    derived: dict[str, str] = {
        "initial_cash": str(initial_cash),
        "pnl_usd": str(total_return * initial_cash),
    }
    total_trades = _optional_decimal(metrics.get("total_trades"))
    if total_trades is not None and total_trades != Decimal("0"):
        derived["pnl_per_trade"] = str((total_return * initial_cash) / total_trades)

    avg_gross_exposure = _optional_decimal(metrics.get("avg_gross_exposure"))
    if avg_gross_exposure is not None and avg_gross_exposure != Decimal("0"):
        derived["return_on_avg_gross_exposure"] = str(total_return / avg_gross_exposure)

    total_commission = _optional_decimal(metrics.get("total_commission")) or Decimal("0")
    total_slippage = _optional_decimal(metrics.get("total_slippage")) or Decimal("0")
    derived["gross_pnl_before_recorded_cost"] = str(
        (total_return * initial_cash) + total_commission + total_slippage
    )
    derived["net_pnl_usd"] = derived["pnl_usd"]

    margin_proxy = _margin_proxy(config)
    if margin_proxy is not None:
        derived["return_on_margin_proxy"] = str((total_return * initial_cash) / margin_proxy)
    return derived


def _manifest_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    for section in ("metrics", "statistics"):
        block = payload.get(section)
        if isinstance(block, dict):
            return block
    return {}


def _initial_cash(payload: dict[str, Any]) -> Decimal | None:
    topology = payload.get("runtime_topology")
    if isinstance(topology, dict):
        accounts = topology.get("accounts")
        if isinstance(accounts, list) and accounts:
            first = accounts[0]
            if isinstance(first, dict):
                value = _optional_decimal(first.get("initial_cash"))
                if value is not None:
                    return value
    value = _optional_decimal(payload.get("initial_cash"))
    if value is not None:
        return value
    return _optional_decimal(payload.get("starting_cash"))


def _margin_proxy(config: dict[str, Any] | None) -> Decimal | None:
    if config is None:
        return None
    for key in ("margin_proxy", "margin_proxy_usd"):
        value = _optional_decimal(config.get(key))
        if value is not None:
            if value <= Decimal("0"):
                raise ValueError(f"{key} must be positive")
            return value
    return None


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite():
        return None
    return parsed


def _robustness_score(accepted_count: int, run_count: int) -> Decimal:
    if run_count == 0:
        return Decimal("0")
    return (Decimal(accepted_count) / Decimal(run_count) * Decimal("100")).normalize()


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        return text.rstrip("0").rstrip(".")
    return text


def _should_derive_capital_metrics(
    constraints: Iterable[OptimizationConstraint],
    config: dict[str, Any] | None,
) -> bool:
    if config is not None:
        return True
    return any(
        isinstance(constraint, MetricConstraint) and constraint.metric_name in _CAPITAL_METRIC_NAMES
        for constraint in constraints
    )


_CAPITAL_METRIC_NAMES = frozenset(
    {
        "gross_pnl_before_recorded_cost",
        "initial_cash",
        "net_pnl_usd",
        "pnl_per_trade",
        "pnl_usd",
        "return_on_avg_gross_exposure",
        "return_on_margin_proxy",
    }
)


__all__ = [
    "OptimizerValidationSummary",
    "OptimizerValidationSummaryWriter",
    "ResearchValidationPolicy",
    "derive_capital_metrics",
]
