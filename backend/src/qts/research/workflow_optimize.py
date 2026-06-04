"""Optimizer workflow step for ResearchWorkflowRunner.

Owns the optimize step (parameter sweep + walk-forward / failure-window validation
scorecard assembly) extracted from ResearchWorkflowRunner (QTS-FINAL-011) as stateless
module functions threading session/config/step.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from qts.research.coercion import (
    iso_date,
    optional_bool,
    optional_decimal,
    optional_int,
    optional_mapping,
    optional_non_negative_int,
    required_mapping,
    string_tuple,
)
from qts.research.optimizer import (
    FailureWindow,
    MetricConstraint,
    OptimizerValidationSummary,
    OptimizerValidationSummaryWriter,
    ResearchValidationPolicy,
    WalkForwardPlan,
    WalkForwardRobustnessPolicy,
    WalkForwardSplit,
    derive_capital_metrics,
)
from qts.research.workflow_support import json_ready, materialized_replay_cache_dir

if TYPE_CHECKING:
    from qts.research.workflow import (
        ResearchWorkflowConfig,
        ResearchWorkflowStepConfig,
        ResearchWorkflowStepResult,
    )


def optimize_step(
    session: Any,
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    from qts.research.workflow import ResearchWorkflowStepResult

    parameters = required_mapping(step.payload, "parameters")
    kwargs: dict[str, Any] = {
        "parameters": {str(key): list(value) for key, value in parameters.items()},
    }
    objective_metric = step.payload.get("objective_metric")
    if objective_metric is not None:
        kwargs["objective_metric"] = str(objective_metric)
    raw_equity_curve_sample_interval = step.payload.get("equity_curve_sample_interval")
    equity_curve_sample_interval = 1
    runtime_kwargs: dict[str, Any] = {}
    if raw_equity_curve_sample_interval is not None:
        equity_curve_sample_interval = _positive_int(
            raw_equity_curve_sample_interval,
            "equity_curve_sample_interval",
        )
        runtime_kwargs["equity_curve_sample_interval"] = equity_curve_sample_interval
        kwargs["equity_curve_sample_interval"] = equity_curve_sample_interval
    output_root = step.payload.get("output_root")
    if output_root is not None:
        kwargs["output_root"] = config.resolve_path(str(output_root))
    materialized_cache_dir = materialized_replay_cache_dir(config, step.payload)
    if materialized_cache_dir is not None:
        kwargs["materialized_replay_cache_dir"] = materialized_cache_dir
    results = session.optimize(**kwargs)
    capital_metric_config = optional_mapping(step.payload.get("capital_metrics"))
    constraints = _validation_constraints(step.payload.get("validation"))
    validation_summary = OptimizerValidationSummary.from_results(
        results,
        constraints,
        capital_metric_config=capital_metric_config,
    )
    validation_policy = _research_validation_policy(step.payload)
    validation_output = step.payload.get("validation_output")
    validation_output_path: Path | None = None
    if validation_output is not None:
        validation_output_path = config.resolve_path(str(validation_output))
        OptimizerValidationSummaryWriter().write(validation_output_path, validation_summary)
    walk_forward_payload = _walk_forward_payload(step.payload.get("validation"))
    walk_forward_summary_payload: dict[str, Any] | None = None
    walk_forward_robustness_payload: dict[str, Any] | None = None
    walk_forward_output_path: Path | None = None
    failure_veto_payload = _failure_window_veto_payload(step.payload.get("validation"))
    failure_veto_summary_payload: dict[str, Any] | None = None
    failure_veto_output_path: Path | None = None
    failure_veto_blocked = False
    if walk_forward_payload is not None:
        plan = _walk_forward_plan(walk_forward_payload)
        top_n = int(walk_forward_payload.get("top_n", 1))
        if top_n <= 0:
            raise ValueError("validation.walk_forward.top_n must be positive")
        walk_forward_output_root = walk_forward_payload.get("output_root")
        walk_forward_summary = session.validate_optimizer_walk_forward(
            candidate_parameters=tuple(dict(result.parameters) for result in results[:top_n]),
            constraints=constraints,
            capital_metric_config=capital_metric_config,
            objective_metric=(None if objective_metric is None else str(objective_metric)),
            output_root=(
                None
                if walk_forward_output_root is None
                else config.resolve_path(str(walk_forward_output_root))
            ),
            plan=plan,
            materialized_replay_cache_dir=materialized_cache_dir,
            **runtime_kwargs,
        )
        walk_forward_summary_payload = walk_forward_summary.to_payload()
        robustness_policy = _walk_forward_robustness_policy(walk_forward_payload.get("robustness"))
        if robustness_policy is not None:
            walk_forward_robustness_payload = robustness_policy.evaluate(
                walk_forward_summary
            ).to_payload()
        raw_walk_forward_output = walk_forward_payload.get("summary_output")
        if raw_walk_forward_output is not None:
            walk_forward_output_path = config.resolve_path(str(raw_walk_forward_output))
            output_payload = dict(walk_forward_summary_payload)
            if walk_forward_robustness_payload is not None:
                output_payload["robustness"] = walk_forward_robustness_payload
            walk_forward_output_path.parent.mkdir(parents=True, exist_ok=True)
            walk_forward_output_path.write_text(
                json.dumps(
                    json_ready(output_payload),
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
    if failure_veto_payload is not None:
        top_n = int(failure_veto_payload.get("top_n", 1))
        if top_n <= 0:
            raise ValueError("validation.failure_window_veto.top_n must be positive")
        require_passing_candidate = _failure_veto_require_passing_candidate(failure_veto_payload)
        failure_veto_output_root = failure_veto_payload.get("output_root")
        failure_veto_summary = session.validate_optimizer_failure_window_veto(
            candidate_parameters=tuple(dict(result.parameters) for result in results[:top_n]),
            constraints=_failure_veto_constraints(failure_veto_payload),
            capital_metric_config=capital_metric_config,
            objective_metric=(None if objective_metric is None else str(objective_metric)),
            output_root=(
                None
                if failure_veto_output_root is None
                else config.resolve_path(str(failure_veto_output_root))
            ),
            windows=_failure_windows(
                failure_veto_payload,
                field_name="windows",
                report_only=False,
            ),
            report_only_windows=_failure_windows(
                failure_veto_payload,
                field_name="report_only_windows",
                report_only=True,
            ),
            materialized_replay_cache_dir=materialized_cache_dir,
            **runtime_kwargs,
        )
        failure_veto_summary_payload = failure_veto_summary.to_payload()
        raw_failure_veto_output = failure_veto_payload.get("summary_output")
        if raw_failure_veto_output is not None:
            failure_veto_output_path = config.resolve_path(str(raw_failure_veto_output))
            failure_veto_output_path.parent.mkdir(parents=True, exist_ok=True)
            failure_veto_output_path.write_text(
                json.dumps(
                    json_ready(failure_veto_summary_payload),
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        decision = failure_veto_summary_payload.get("decision", {})
        failure_veto_blocked = (
            require_passing_candidate
            and isinstance(decision, Mapping)
            and decision.get("accepted") is False
        )
    validation_payload = optional_mapping(step.payload.get("validation")) or {}
    validation_policy_payload = validation_policy.evaluate(
        validation_summary,
        walk_forward_present=walk_forward_summary_payload is not None,
        failure_window_present=failure_veto_summary_payload is not None,
        cost_stress_present=validation_payload.get("cost_stress") is not None,
    )
    ranked_results = []
    for result in results:
        ranked_result = {
            "manifest_hash": result.manifest_hash,
            "manifest_path": str(result.manifest_path),
            "objective_value": str(result.objective_value),
            "parameters": dict(result.parameters),
        }
        runtime = _optimizer_result_runtime(result)
        if runtime:
            ranked_result["runtime"] = runtime
        if capital_metric_config is not None:
            ranked_result["capital_metrics"] = derive_capital_metrics(
                result,
                capital_metric_config,
            )
        ranked_results.append(ranked_result)
    outputs: dict[str, Any] = {
        "ranked_results": ranked_results,
        "run_count": len(results),
        "equity_curve_sample_interval": equity_curve_sample_interval,
        "validation_output": (
            None if validation_output_path is None else str(validation_output_path)
        ),
        "validation_summary": validation_summary.to_payload(),
        "validation_policy": validation_policy_payload,
        "validation_scorecard": _validation_scorecard(
            validation_policy_payload=validation_policy_payload,
            validation=validation_payload,
        ),
    }
    if walk_forward_summary_payload is not None:
        outputs["walk_forward_validation"] = walk_forward_summary_payload
        outputs["walk_forward_validation_output"] = (
            None if walk_forward_output_path is None else str(walk_forward_output_path)
        )
        if walk_forward_robustness_payload is not None:
            outputs["walk_forward_robustness"] = walk_forward_robustness_payload
    if failure_veto_summary_payload is not None:
        outputs["failure_window_veto"] = failure_veto_summary_payload
        outputs["failure_window_veto_output"] = (
            None if failure_veto_output_path is None else str(failure_veto_output_path)
        )
    validation_policy_blocked = bool(validation_policy_payload.get("blocked", False))
    blocked = failure_veto_blocked or validation_policy_blocked
    message = "optimization completed"
    if failure_veto_blocked:
        message = "failure-window veto blocked workflow"
    elif validation_policy_blocked:
        message = "optimizer validation policy blocked workflow"
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="blocked" if blocked else "passed",
        message=message,
        outputs=outputs,
    )


def _optimizer_result_runtime(result: Any) -> dict[str, Any]:
    runtime: dict[str, Any] = {}
    if result.processed_bars is not None:
        runtime["processed_bars"] = result.processed_bars
    if result.trading_bars is not None:
        runtime["trading_bars"] = result.trading_bars
    if result.elapsed_seconds is not None:
        runtime["elapsed_seconds"] = str(result.elapsed_seconds)
    if result.bars_per_second is not None:
        runtime["bars_per_second"] = str(result.bars_per_second)
    if result.equity_curve_sample_interval is not None:
        runtime["equity_curve_sample_interval"] = result.equity_curve_sample_interval
    return runtime


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer")
    parsed = optional_int(value)
    if parsed is None or parsed < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return parsed


def _failure_veto_constraints(
    value: Mapping[str, Any],
) -> tuple[MetricConstraint, ...]:
    raw_constraints = value.get("constraints")
    if raw_constraints is None or not isinstance(raw_constraints, list) or not raw_constraints:
        raise ValueError("validation.failure_window_veto.constraints must be a non-empty list")
    return _metric_constraints_from_sequence(
        raw_constraints,
        field_name="validation.failure_window_veto.constraints",
    )


def _failure_veto_require_passing_candidate(value: Mapping[str, Any]) -> bool:
    raw_value = value.get("require_passing_candidate", False)
    if not isinstance(raw_value, bool):
        raise ValueError(
            "validation.failure_window_veto.require_passing_candidate must be a boolean"
        )
    return raw_value


def _failure_window_veto_payload(value: Any) -> dict[str, Any] | None:
    validation = optional_mapping(value)
    if validation is None:
        return None
    raw_veto = validation.get("failure_window_veto")
    if raw_veto is None:
        return None
    if not isinstance(raw_veto, Mapping):
        raise ValueError("validation.failure_window_veto must be a mapping")
    return dict(raw_veto)


def _failure_windows(
    value: Mapping[str, Any],
    *,
    field_name: str,
    report_only: bool,
) -> tuple[FailureWindow, ...]:
    raw_windows = value.get(field_name)
    if raw_windows is None:
        if field_name == "windows":
            raise ValueError("validation.failure_window_veto.windows must be a non-empty list")
        return ()
    if field_name == "windows" and (not isinstance(raw_windows, list) or not raw_windows):
        raise ValueError("validation.failure_window_veto.windows must be a non-empty list")
    if not isinstance(raw_windows, list):
        raise ValueError(f"validation.failure_window_veto.{field_name} must be a list")
    windows: list[FailureWindow] = []
    for index, raw_window in enumerate(raw_windows):
        if not isinstance(raw_window, Mapping):
            raise ValueError(
                f"validation.failure_window_veto.{field_name}[{index}] must be a mapping"
            )
        window = dict(raw_window)
        windows.append(
            FailureWindow(
                name=str(window["name"]),
                start=iso_date(window["start"], "start"),
                end=iso_date(window["end"], "end"),
                report_only=report_only,
            )
        )
    return tuple(windows)


def _metric_constraints_from_sequence(
    value: Any,
    *,
    field_name: str,
) -> tuple[MetricConstraint, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    constraints: list[MetricConstraint] = []
    for index, raw_constraint in enumerate(value):
        if not isinstance(raw_constraint, Mapping):
            raise ValueError(f"{field_name}[{index}] must be a mapping")
        constraint = dict(raw_constraint)
        constraints.append(
            MetricConstraint(
                metric_name=str(constraint["metric"]),
                operator=str(constraint["operator"]),
                threshold=Decimal(str(constraint["threshold"])),
            )
        )
    return tuple(constraints)


def _research_validation_policy(step_payload: Mapping[str, Any]) -> ResearchValidationPolicy:
    raw_policy = optional_mapping(step_payload.get("validation_policy")) or {}
    validation = optional_mapping(step_payload.get("validation")) or {}
    raw_required = raw_policy.get(
        "require_passing_candidate",
        validation.get("require_passing_candidate", False),
    )
    if not isinstance(raw_required, bool):
        raise ValueError("validation_policy.require_passing_candidate must be a boolean")
    return ResearchValidationPolicy(
        require_passing_candidate=raw_required,
        min_accepted_count=optional_non_negative_int(
            raw_policy.get("min_accepted_count"),
            field_name="validation_policy.min_accepted_count",
        ),
        min_robustness_score=optional_decimal(
            raw_policy.get("min_robustness_score"),
            field_name="validation_policy.min_robustness_score",
        ),
        require_walk_forward=optional_bool(
            raw_policy.get("require_walk_forward", False),
            field_name="validation_policy.require_walk_forward",
        ),
        require_failure_window=optional_bool(
            raw_policy.get("require_failure_window", False),
            field_name="validation_policy.require_failure_window",
        ),
        require_cost_stress=optional_bool(
            raw_policy.get("require_cost_stress", False),
            field_name="validation_policy.require_cost_stress",
        ),
        max_rejected_count=optional_non_negative_int(
            raw_policy.get("max_rejected_count"),
            field_name="validation_policy.max_rejected_count",
        ),
    )


def _validation_constraints(value: Any) -> tuple[MetricConstraint, ...]:
    validation = optional_mapping(value)
    if validation is None:
        return ()
    raw_constraints = validation.get("constraints")
    if raw_constraints is None:
        return ()
    return _metric_constraints_from_sequence(
        raw_constraints,
        field_name="validation.constraints",
    )


def _validation_scorecard(
    *,
    validation_policy_payload: Mapping[str, Any],
    validation: Any,
) -> dict[str, Any]:
    validation_payload = optional_mapping(validation) or {}
    return {
        "cost_stress_status": (
            "configured" if validation_payload.get("cost_stress") is not None else "not_configured"
        ),
        "failure_window_status": (
            "configured"
            if validation_payload.get("failure_window_veto") is not None
            else "not_configured"
        ),
        "rejection_reasons": list(validation_policy_payload.get("rejection_reasons", ())),
        "validation_policy_missing_evidence": list(
            validation_policy_payload.get("missing_evidence", ())
        ),
        "validation_policy_reasons": list(validation_policy_payload.get("reasons", ())),
        "robustness_score": validation_policy_payload.get("robustness_score", "0"),
        "walk_forward_status": (
            "configured" if validation_payload.get("walk_forward") is not None else "not_configured"
        ),
    }


def _walk_forward_payload(value: Any) -> dict[str, Any] | None:
    validation = optional_mapping(value)
    if validation is None:
        return None
    raw_walk_forward = validation.get("walk_forward")
    if raw_walk_forward is None:
        return None
    if not isinstance(raw_walk_forward, Mapping):
        raise ValueError("validation.walk_forward must be a mapping")
    return dict(raw_walk_forward)


def _walk_forward_plan(value: Mapping[str, Any]) -> WalkForwardPlan:
    raw_splits = value.get("splits")
    if not isinstance(raw_splits, list) or not raw_splits:
        raise ValueError("validation.walk_forward.splits must be a non-empty list")
    splits: list[WalkForwardSplit] = []
    for index, raw_split in enumerate(raw_splits):
        if not isinstance(raw_split, Mapping):
            raise ValueError(f"validation.walk_forward.splits[{index}] must be a mapping")
        split = dict(raw_split)
        splits.append(
            WalkForwardSplit(
                name=str(split["name"]),
                train_start=iso_date(split["train_start"], "train_start"),
                train_end=iso_date(split["train_end"], "train_end"),
                test_start=iso_date(split["test_start"], "test_start"),
                test_end=iso_date(split["test_end"], "test_end"),
            )
        )
    return WalkForwardPlan(tuple(splits))


def _walk_forward_robustness_policy(
    value: Any,
) -> WalkForwardRobustnessPolicy | None:
    payload = optional_mapping(value)
    if payload is None:
        return None
    phases = string_tuple(payload.get("phases", ["test"]))
    return WalkForwardRobustnessPolicy(
        phases=phases,
        min_windows=optional_int(payload.get("min_windows")),
        max_losing_windows=optional_int(payload.get("max_losing_windows")),
        min_window_pnl_usd=optional_decimal(payload.get("min_window_pnl_usd")),
        min_window_best_objective=optional_decimal(payload.get("min_window_best_objective")),
        min_total_pnl_usd=optional_decimal(payload.get("min_total_pnl_usd")),
    )


__all__ = ["optimize_step"]
