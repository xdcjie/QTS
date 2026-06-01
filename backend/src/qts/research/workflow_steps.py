"""Workflow step implementations for ResearchWorkflowRunner.

Stateless step handlers (backtest, backtest-matrix, ablation, factor, portfolio,
trade-diagnostics, research-report, and gate steps) extracted from
ResearchWorkflowRunner (QTS-FINAL-011) as module functions threading
session/config/step; the runner dispatches to them from _run_step.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from operator import attrgetter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from qts.research.ablation import AblationPlan, AblationReport, AblationReportWriter, AblationRun
from qts.research.coercion import (
    float_mapping,
    iso_datetime,
    nested_float_mapping,
    optional_float,
    optional_int,
    optional_mapping,
    optional_string_tuple,
    string_tuple,
)
from qts.research.portfolio_ensemble import (
    evaluate_portfolio_ensemble,
    scan_portfolio_ensemble_allocations,
    scan_volatility_managed_allocations,
)
from qts.research.report import (
    ResearchWorkflowReport,
    ResearchWorkflowReportWriter,
)
from qts.research.trade_diagnostics import (
    TradeDiagnostic,
    TradeDiagnosticsArtifactWriter,
    TradeDiagnosticsReport,
)
from qts.research.workflow_support import (
    _FILENAME_SAFE_CHARS,
    _PERIOD_ROLES,
    _REPORT_ONLY_PERIOD_ROLES,
    _SCORING_PERIOD_ROLES,
    ResearchWorkflowStepResult,
    _load_json_mapping,
    _required_text,
    _review_decision_from_payload,
    _snapshot_protocol_payload,
    json_ready,
    materialized_replay_cache_dir,
)

if TYPE_CHECKING:
    from qts.research.workflow import (
        ResearchWorkflowConfig,
        ResearchWorkflowRunContext,
        ResearchWorkflowStepConfig,
    )


def _factor_candidates(
    session: Any,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    query = _required_text(step.payload, "query")
    batch = session.find_factor_candidates(
        query,
        sources=optional_string_tuple(step.payload.get("sources")),
        max_results=optional_int(step.payload.get("max_results")),
        from_year=optional_int(step.payload.get("from_year")),
        to_year=optional_int(step.payload.get("to_year")),
        refresh=bool(step.payload.get("refresh", False)),
    )
    specs = batch.specs
    result_query = batch.result.query
    outputs = {
        "candidate_count": len(specs),
        "query_id": result_query.query_id,
        "spec_names": [spec.name for spec in specs],
    }
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="factor candidates persisted",
        outputs=outputs,
    )


def _factor_review_gate(
    session: Any,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    status = str(step.payload.get("status", "accepted"))
    min_count = int(step.payload.get("min_count", 1))
    if min_count <= 0:
        raise ValueError("min_count must be positive")
    specs = session.list_factor_specs_by_status(status)
    outputs = {
        "matched_count": len(specs),
        "min_count": min_count,
        "spec_names": [spec.name for spec in specs],
        "status": status,
    }
    passed = len(specs) >= min_count
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed" if passed else "blocked",
        message="review gate passed" if passed else "review gate blocked workflow",
        outputs=outputs,
    )


def _implementation_gate(step: ResearchWorkflowStepConfig) -> ResearchWorkflowStepResult:
    required_modules = string_tuple(step.payload.get("required_modules", ()))
    required_strategy = step.payload.get("required_strategy")
    missing_modules = [module for module in required_modules if not _can_import(module)]
    missing_strategies: list[str] = []
    if required_strategy is not None and not _can_resolve_attribute(str(required_strategy)):
        missing_strategies.append(str(required_strategy))
    outputs = {
        "missing_modules": missing_modules,
        "missing_strategies": missing_strategies,
        "required_modules": list(required_modules),
        "required_strategy": required_strategy,
    }
    passed = not missing_modules and not missing_strategies
    message = "implementation gate passed" if passed else "implementation gate blocked workflow"
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed" if passed else "blocked",
        message=message,
        outputs=outputs,
    )


def _factor_evaluation(
    session: Any,
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    factor_name = _required_text(step.payload, "factor_name")
    factor_version = _required_text(step.payload, "factor_version")
    bucket_count = int(step.payload.get("bucket_count", 5))
    raw_snapshots = step.payload.get("snapshots")
    if not isinstance(raw_snapshots, list | tuple) or not raw_snapshots:
        raise ValueError("factor_evaluation requires non-empty snapshots")
    output_dir = step.payload.get("output_dir")
    resolved_snapshots: list[dict[str, object]] = []
    for snapshot in raw_snapshots:
        if not isinstance(snapshot, Mapping):
            raise ValueError("factor_evaluation snapshots must be mappings")
        factor_scores = snapshot.get("factor_scores")
        if not isinstance(factor_scores, str | Path):
            raise ValueError("factor_evaluation snapshot.factor_scores must be a path")
        forward_returns = snapshot.get("forward_returns")
        if not isinstance(forward_returns, str | Path):
            raise ValueError("factor_evaluation snapshot.forward_returns must be a path")
        resolved_snapshots.append(
            {
                **_snapshot_protocol_payload(snapshot),
                "as_of": json_ready(snapshot.get("as_of")),
                "factor_scores": str(config.resolve_path(factor_scores)),
                "forward_returns": str(config.resolve_path(forward_returns)),
            }
        )
    evaluated = session.evaluate_factor(
        factor_name=factor_name,
        factor_version=factor_version,
        snapshots=resolved_snapshots,
        bucket_count=bucket_count,
        output_dir=config.resolve_path(str(output_dir)) if output_dir is not None else None,
    )
    latest_result = evaluated[-1].result.metrics
    outputs = {
        "factor_name": factor_name,
        "factor_version": factor_version,
        "artifact_paths": [str(item.artifact_path) for item in evaluated],
        "snapshot_count": len(evaluated),
        "rank_ic": str(latest_result.rank_ic),
        "long_short_spread": str(latest_result.long_short_spread),
        "coverage": str(latest_result.coverage),
        "return_count": latest_result.return_count,
        "scored_count": latest_result.scored_count,
        "turnover": None if latest_result.turnover is None else str(latest_result.turnover),
    }
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="factor evaluation completed",
        outputs=outputs,
    )


def _ablation(
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    baseline = _required_text(step.payload, "baseline")
    modules = string_tuple(step.payload.get("modules", ()))
    primary_metric = _required_text(step.payload, "primary_metric")
    higher_is_better = step.payload.get("higher_is_better", True)
    if not isinstance(higher_is_better, bool):
        raise ValueError("higher_is_better must be a boolean")
    source_summary = step.payload.get("source_summary")
    if source_summary is not None:
        source_payload = _load_json_mapping(config.resolve_path(str(source_summary)))
        plan = AblationPlan.from_backtest_matrix_summary(
            source_payload,
            baseline=baseline,
            module_map=_module_map(step.payload.get("module_map")),
        )
    else:
        raw_runs = step.payload.get("runs")
        if not isinstance(raw_runs, list) or not raw_runs:
            raise ValueError("ablation runs must not be empty")
        runs = tuple(_ablation_run(raw_run, index=index) for index, raw_run in enumerate(raw_runs))
        plan = AblationPlan(
            baseline=baseline,
            modules=modules,
            runs=runs,
        )
    report = AblationReport.from_plan(
        plan,
        primary_metric=primary_metric,
        higher_is_better=higher_is_better,
    )
    output_root = step.payload.get("output_root", "ablation")
    if not isinstance(output_root, (str, Path)):
        raise ValueError("ablation output_root must be a path")
    writer = AblationReportWriter(config.resolve_path(output_root))
    paths = writer.write(
        report,
        json_path=str(step.payload.get("summary_output", "ablation-summary.json")),
        markdown_path=str(step.payload.get("report_output", "ablation-report.md")),
    )
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="ablation artifacts written",
        outputs={
            "ablation_summary": report.to_dict(),
            "artifact_path": str(paths.json_path),
            "artifact_paths": [str(paths.json_path), str(paths.markdown_path)],
            "report_path": str(paths.markdown_path),
        },
    )


def _trade_diagnostics(
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    raw_trades = step.payload.get("trades")
    if not isinstance(raw_trades, list) or not raw_trades:
        raise ValueError("trade_diagnostics trades must not be empty")
    trades = tuple(
        _trade_diagnostic(raw_trade, index=index) for index, raw_trade in enumerate(raw_trades)
    )
    output_root = step.payload.get("output_root", "trade-diagnostics")
    if not isinstance(output_root, (str, Path)):
        raise ValueError("trade_diagnostics output_root must be a path")
    report = TradeDiagnosticsReport(trades=trades)
    artifacts = TradeDiagnosticsArtifactWriter().write(
        config.resolve_path(output_root),
        report,
    )
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="trade diagnostics artifacts written",
        outputs={
            "artifact_path": str(artifacts.summary_path),
            "artifact_paths": [
                str(artifacts.trades_path),
                str(artifacts.summary_path),
                str(artifacts.markdown_path),
            ],
            "report_path": str(artifacts.markdown_path),
            "summary_path": str(artifacts.summary_path),
            "trade_count": len(trades),
            "trades_path": str(artifacts.trades_path),
        },
    )


def _research_report(
    config: ResearchWorkflowConfig,
    run_context: ResearchWorkflowRunContext,
    steps: tuple[ResearchWorkflowStepResult, ...],
    step: ResearchWorkflowStepConfig,
    *,
    idea_metadata: Mapping[str, Any] | None = None,
) -> ResearchWorkflowStepResult:
    from qts.research.workflow import ResearchWorkflowResult

    writer_root = (
        config.resolve_path(_required_text(step.payload, "output_root"))
        if "output_root" in step.payload
        else None
    )
    if writer_root is None:
        writer_root = config.workflow_config_path.parent / "research-workflow-reports"
    writer = ResearchWorkflowReportWriter(writer_root)
    report_output_path = str(step.payload.get("output_path", "workflow-report.md"))
    report = ResearchWorkflowReport.from_result(
        ResearchWorkflowResult(
            workflow_id=config.workflow_id,
            periods=config.periods,
            decision=_review_decision_from_payload(step.payload.get("decision")),
            run_context=run_context,
            route=config.route,
            idea_metadata=idea_metadata,
            status="completed",
            steps=steps,
        )
    )
    report_path = writer.write(report, output_path=report_output_path)
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="research report written",
        outputs={"decision": report.decision.to_payload(), "report_path": str(report_path)},
    )


def _portfolio_ensemble(
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    payload = dict(step.payload)
    raw_legs = payload.get("legs")
    if not isinstance(raw_legs, list):
        raise ValueError("portfolio_ensemble.legs must be a non-empty list")
    resolved_legs: list[dict[str, Any]] = []
    for index, raw_leg in enumerate(raw_legs):
        if not isinstance(raw_leg, Mapping):
            raise ValueError(f"portfolio_ensemble.legs[{index}] must be a mapping")
        leg_payload = dict(raw_leg)
        leg_payload["manifest_path"] = str(
            config.resolve_path(_required_text(leg_payload, "manifest_path"))
        )
        resolved_legs.append(leg_payload)
    payload["legs"] = resolved_legs
    result = evaluate_portfolio_ensemble(payload)
    summary_output = step.payload.get("summary_output")
    summary_path = (
        config.resolve_path(str(summary_output))
        if summary_output is not None
        else config.workflow_config_path.parent
        / f"{result['allocation_name']}-portfolio-ensemble-summary.json"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(json_ready(result), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="portfolio ensemble research summary written",
        outputs={
            "allocation_name": result["allocation_name"],
            "leg_count": result["leg_count"],
            "point_count": result["point_count"],
            "research_only": result["research_only"],
            "summary_path": str(summary_path),
        },
    )


def _portfolio_ensemble_scan(
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    payload = dict(step.payload)
    scan_periods = string_tuple(payload.get("periods"))
    period_roles = config.period_roles_for(scan_periods)
    if period_roles:
        payload["period_roles"] = period_roles
    payload["candidates"] = _resolved_period_manifest_candidates(
        config,
        step,
        kind_name="portfolio_ensemble_scan",
    )
    result = scan_portfolio_ensemble_allocations(payload)
    period_payloads = _named_period_payloads(config, scan_periods)
    report_only_periods = [
        period for period, role in period_roles.items() if role in _REPORT_ONLY_PERIOD_ROLES
    ]
    summary_payload = dict(result)
    if period_payloads:
        summary_payload["periods"] = period_payloads
        summary_payload["report_only_periods"] = report_only_periods
    summary_output = step.payload.get("summary_output")
    summary_path = (
        config.resolve_path(str(summary_output))
        if summary_output is not None
        else config.workflow_config_path.parent
        / f"{result['scan_name']}-portfolio-ensemble-scan-summary.json"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(json_ready(summary_payload), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    outputs: dict[str, Any] = {
        "candidate_count": result["candidate_count"],
        "evaluated_allocation_count": result["evaluated_allocation_count"],
        "satisfying_allocation_count": result["satisfying_allocation_count"],
        "summary_path": str(summary_path),
    }
    if period_payloads:
        outputs["periods"] = period_payloads
        outputs["report_only_periods"] = report_only_periods
        outputs["score_periods"] = result["score_periods"]
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="portfolio ensemble allocation scan written",
        outputs=outputs,
    )


def _portfolio_volatility_managed_scan(
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    payload = dict(step.payload)
    scan_periods = string_tuple(payload.get("periods"))
    period_roles = config.period_roles_for(scan_periods)
    if period_roles:
        payload["period_roles"] = period_roles
    payload["candidates"] = _resolved_period_manifest_candidates(
        config,
        step,
        kind_name="portfolio_volatility_managed_scan",
    )
    result = scan_volatility_managed_allocations(payload)
    period_payloads = _named_period_payloads(config, scan_periods)
    report_only_periods = [
        period for period, role in period_roles.items() if role in _REPORT_ONLY_PERIOD_ROLES
    ]
    summary_payload = dict(result)
    if period_payloads:
        summary_payload["periods"] = period_payloads
        summary_payload["report_only_periods"] = report_only_periods
    summary_output = step.payload.get("summary_output")
    summary_path = (
        config.resolve_path(str(summary_output))
        if summary_output is not None
        else config.workflow_config_path.parent
        / f"{result['scan_name']}-portfolio-volatility-managed-summary.json"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(json_ready(summary_payload), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    outputs = {
        "candidate_count": result["candidate_count"],
        "evaluated_parameter_count": result["evaluated_parameter_count"],
        "satisfying_allocation_count": result["satisfying_allocation_count"],
        "summary_path": str(summary_path),
    }
    if period_payloads:
        outputs["periods"] = period_payloads
        outputs["report_only_periods"] = report_only_periods
        outputs["selection_basis"] = result["selection_periods"]
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="portfolio volatility managed allocation scan written",
        outputs=outputs,
    )


def _resolved_period_manifest_candidates(
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
    *,
    kind_name: str,
) -> list[dict[str, Any]]:
    raw_candidates = step.payload.get("candidates")
    if not isinstance(raw_candidates, list):
        raise ValueError(f"{kind_name}.candidates must be a non-empty list")
    resolved_candidates: list[dict[str, Any]] = []
    for index, raw_candidate in enumerate(raw_candidates):
        if not isinstance(raw_candidate, Mapping):
            raise ValueError(f"{kind_name}.candidates[{index}] must be a mapping")
        candidate_payload = dict(raw_candidate)
        raw_manifests = candidate_payload.get("period_manifests")
        if not isinstance(raw_manifests, Mapping):
            raise ValueError(f"{kind_name}.candidate.period_manifests is required")
        candidate_payload["period_manifests"] = {
            str(period): str(config.resolve_path(str(path)))
            for period, path in raw_manifests.items()
        }
        resolved_candidates.append(candidate_payload)
    return resolved_candidates


def _named_period_payloads(
    config: ResearchWorkflowConfig,
    period_names: tuple[str, ...],
) -> list[dict[str, Any]]:
    period_by_name = config._period_by_name()
    return [
        _declared_period_payload(period_by_name[period_name])
        for period_name in period_names
        if period_name in period_by_name
    ]


def _declared_period_payload(period: Mapping[str, Any]) -> dict[str, Any]:
    end = period["end"]
    start = period["start"]
    return {
        "end": None if end is None else end.isoformat(),
        "name": str(period["name"]),
        "role": str(period["role"]),
        "start": start.isoformat(),
    }


def _factor_tearsheet(
    session: Any,
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    raw_artifact_paths = step.payload.get(
        "artifact_paths",
        step.payload.get("artifacts", ()),
    )
    artifact_paths = tuple(config.resolve_path(path) for path in string_tuple(raw_artifact_paths))
    if not artifact_paths:
        raise ValueError("factor_tearsheet requires artifact_paths")
    experiment_id = step.payload.get("experiment_id")
    if experiment_id is None:
        tearsheet = session.factor_tearsheet(artifact_paths)
        outputs = {
            "factor_name": tearsheet.factor_name,
            "factor_version": tearsheet.factor_version,
            "metrics": tearsheet.manifest_metrics(),
        }
    else:
        record = session.record_factor_tearsheet(
            artifact_paths,
            experiment_id=str(experiment_id),
            strategy_name=str(step.payload.get("strategy_name", "factor-tearsheet")),
            strategy_version=str(step.payload.get("strategy_version", "1")),
            dataset_ids=string_tuple(step.payload.get("dataset_ids", ())),
        )
        outputs = {
            "experiment_id": record.experiment_id,
            "manifest_path": str(record.manifest_path),
            "metrics": dict(record.metrics),
        }
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="factor tearsheet recorded",
        outputs=outputs,
    )


def _backtest(
    session: Any,
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    strategy_params = optional_mapping(step.payload.get("strategy_params")) or {}
    kwargs: dict[str, Any] = {"strategy_params": strategy_params}
    backtest_config = step.payload.get("backtest_config")
    if backtest_config is not None:
        kwargs["backtest_config_path"] = config.resolve_path(str(backtest_config))
    output_dir = step.payload.get("output_dir")
    if output_dir is not None:
        kwargs["output_dir"] = config.resolve_path(str(output_dir))
    materialized_cache_dir = materialized_replay_cache_dir(config, step.payload)
    if materialized_cache_dir is not None:
        kwargs["materialized_replay_cache_dir"] = materialized_cache_dir
    result = session.run_backtest(**kwargs)
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="backtest completed",
        outputs={
            "manifest_path": str(result.manifest_path),
            "processed_bars": result.processed_bars,
            "trading_bars": result.trading_bars,
        },
    )


def _backtest_matrix(
    session: Any,
    config: ResearchWorkflowConfig,
    step: ResearchWorkflowStepConfig,
) -> ResearchWorkflowStepResult:
    output_root = config.resolve_path(_required_text(step.payload, "output_root"))
    periods = _matrix_periods(config, step.payload.get("periods"))
    period_payloads = _period_payloads(periods)
    selection_basis = _selection_basis(period_payloads)
    report_only_periods = _report_only_period_names(period_payloads)
    candidates = _matrix_candidates(step.payload.get("candidates"))
    base_strategy_params = optional_mapping(step.payload.get("base_strategy_params")) or {}
    metrics = string_tuple(
        step.payload.get(
            "metrics",
            [
                "total_return",
                "sharpe_ratio",
                "max_drawdown",
                "total_trades",
                "profit_factor",
            ],
        )
    )
    kwargs: dict[str, Any] = {
        "base_strategy_params": base_strategy_params,
        "candidates": candidates,
        "metrics": metrics,
        "output_root": output_root,
        "periods": periods,
    }
    backtest_config = step.payload.get("backtest_config")
    if backtest_config is not None:
        kwargs["backtest_config_path"] = config.resolve_path(str(backtest_config))
    materialized_cache_dir = materialized_replay_cache_dir(config, step.payload)
    if materialized_cache_dir is not None:
        kwargs["materialized_replay_cache_dir"] = materialized_cache_dir
    rows = list(session.run_backtest_matrix(**kwargs))
    summary_payload = {
        "candidate_count": len(candidates),
        "metrics": list(metrics),
        "output_root": str(output_root),
        "period_count": len(periods),
        "rows": rows,
        "step_id": step.step_id,
        "workflow_id": config.workflow_id,
    }
    if period_payloads:
        summary_payload["periods"] = period_payloads
        summary_payload["report_only_periods"] = report_only_periods
        summary_payload["selection_basis"] = selection_basis
    summary_output = step.payload.get("summary_output")
    summary_path = (
        config.resolve_path(str(summary_output))
        if summary_output is not None
        else output_root / "summary.json"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(json_ready(summary_payload), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    outputs: dict[str, Any] = {
        "candidate_count": len(candidates),
        "period_count": len(periods),
        "run_count": len(rows),
        "summary_path": str(summary_path),
    }
    if period_payloads:
        outputs["periods"] = period_payloads
        outputs["report_only_periods"] = report_only_periods
        outputs["selection_basis"] = selection_basis
    return ResearchWorkflowStepResult(
        step_id=step.step_id,
        kind=step.kind,
        status="passed",
        message="backtest matrix completed",
        outputs=outputs,
    )


def _matrix_periods(
    config: ResearchWorkflowConfig,
    value: Any,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("backtest_matrix.periods must be a non-empty list")
    periods: list[dict[str, Any]] = []
    workflow_periods = config._period_by_name()
    for index, raw_period in enumerate(value):
        if isinstance(raw_period, str):
            declared = workflow_periods.get(raw_period)
            if declared is None:
                raise ValueError(f"unknown workflow period: {raw_period}")
            if declared["end"] is None:
                raise ValueError(f"backtest_matrix period {raw_period} requires end")
            periods.append(
                {
                    "end": declared["end"],
                    "name": declared["name"],
                    "role": declared["role"],
                    "start": declared["start"],
                }
            )
            continue
        if not isinstance(raw_period, Mapping):
            raise ValueError(f"backtest_matrix.periods[{index}] must be a mapping or period name")
        period = dict(raw_period)
        name = _safe_token(period, "name")
        role = period.get("role", config.period_role(name))
        if role is not None and str(role) not in _PERIOD_ROLES:
            raise ValueError(f"unsupported period role: {role}")
        periods.append(
            {
                "end": iso_datetime(period["end"], "end"),
                "name": name,
                "role": None if role is None else str(role),
                "start": iso_datetime(period["start"], "start"),
            }
        )
    return tuple(periods)


def _period_payloads(periods: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    return [
        {
            "end": None if period.get("end") is None else period["end"].isoformat(),
            "name": str(period["name"]),
            "role": period.get("role"),
            "start": period["start"].isoformat(),
        }
        for period in periods
        if period.get("role") is not None
    ]


def _selection_basis(periods: list[dict[str, Any]]) -> list[str]:
    return [
        str(period["name"]) for period in periods if period.get("role") in _SCORING_PERIOD_ROLES
    ]


def _report_only_period_names(periods: list[dict[str, Any]]) -> list[str]:
    return [
        str(period["name"]) for period in periods if period.get("role") in _REPORT_ONLY_PERIOD_ROLES
    ]


def _matrix_candidates(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("backtest_matrix.candidates must be a non-empty list")
    candidates: list[dict[str, Any]] = []
    for index, raw_candidate in enumerate(value):
        if not isinstance(raw_candidate, Mapping):
            raise ValueError(f"backtest_matrix.candidates[{index}] must be a mapping")
        candidate = dict(raw_candidate)
        strategy_params = optional_mapping(candidate.get("strategy_params")) or {}
        candidates.append(
            {
                "name": _safe_token(candidate, "name"),
                "strategy_params": strategy_params,
            }
        )
    return tuple(candidates)


def _safe_token(payload: Mapping[str, Any], field_name: str) -> str:
    value = _required_text(payload, field_name)
    if any(character not in _FILENAME_SAFE_CHARS for character in value):
        raise ValueError(f"{field_name} must be filename-safe")
    return value


def _module_map(value: Any) -> dict[str, tuple[str, ...]]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("module_map must be a mapping")
    return {str(key): string_tuple(item) for key, item in value.items()}


def _ablation_run(value: Any, *, index: int) -> AblationRun:
    if not isinstance(value, Mapping):
        raise ValueError(f"ablation runs[{index}] must be a mapping")
    return AblationRun(
        name=_required_text(value, "name"),
        modules=string_tuple(value.get("modules", ())),
        metrics=float_mapping(value.get("metrics"), field_name=f"runs[{index}].metrics"),
        split_metrics=nested_float_mapping(
            value.get("split_metrics"),
            field_name=f"runs[{index}].split_metrics",
        ),
        trade_count=optional_int(value.get("trade_count")),
        cost_stress_metrics=nested_float_mapping(
            value.get("cost_stress_metrics"),
            field_name=f"runs[{index}].cost_stress_metrics",
        ),
    )


def _trade_diagnostic(value: Any, *, index: int) -> TradeDiagnostic:
    if not isinstance(value, Mapping):
        raise ValueError(f"trade_diagnostics.trades[{index}] must be a mapping")
    return TradeDiagnostic(
        trade_id=_required_text(value, "trade_id"),
        strategy_id=_required_text(value, "strategy_id"),
        idea_id=_required_text(value, "idea_id"),
        symbol=_required_text(value, "symbol"),
        direction=_required_text(value, "direction"),
        quantity=value.get("quantity"),
        entry_time=iso_datetime(value.get("entry_time"), "entry_time"),
        exit_time=iso_datetime(value.get("exit_time"), "exit_time"),
        entry_price=optional_float(value.get("entry_price")),
        exit_price=optional_float(value.get("exit_price")),
        r_pnl=optional_float(value.get("r_pnl")),
        mae_r=optional_float(value.get("mae_r")),
        mfe_r=optional_float(value.get("mfe_r")),
        holding_bars=optional_int(value.get("holding_bars")),
        exit_reason=_required_text(value, "exit_reason"),
        time_bucket=_required_text(value, "time_bucket"),
        factor_snapshot=float_mapping(
            value.get("factor_snapshot"),
            field_name=f"trade_diagnostics.trades[{index}].factor_snapshot",
        ),
    )


def _can_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
    except ImportError:
        return False
    return True


def _can_resolve_attribute(value: str) -> bool:
    if ":" not in value:
        return False
    module_name, attribute_name = value.split(":", maxsplit=1)
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return False
    try:
        attrgetter(attribute_name)(module)
    except AttributeError:
        return False
    return True


__all__ = [
    "_ablation",
    "_backtest",
    "_backtest_matrix",
    "_factor_candidates",
    "_factor_evaluation",
    "_factor_review_gate",
    "_factor_tearsheet",
    "_implementation_gate",
    "_portfolio_ensemble",
    "_portfolio_ensemble_scan",
    "_portfolio_volatility_managed_scan",
    "_research_report",
    "_trade_diagnostics",
]
