"""Gate-based research workflow orchestration."""

from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.research.optimizer import (
    FailureWindow,
    MetricConstraint,
    OptimizerValidationSummary,
    OptimizerValidationSummaryWriter,
    WalkForwardPlan,
    WalkForwardRobustnessPolicy,
    WalkForwardSplit,
    derive_capital_metrics,
)
from qts.research.portfolio_ensemble import (
    evaluate_portfolio_ensemble,
    scan_portfolio_ensemble_allocations,
    scan_volatility_managed_allocations,
)
from qts.research.report import ResearchWorkflowReport, ResearchWorkflowReportWriter


@dataclass(frozen=True, slots=True)
class ResearchWorkflowStepConfig:
    """One validated workflow step declaration."""

    step_id: str
    kind: str
    payload: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ResearchWorkflowConfig:
    """Owns validated gate-based research workflow configuration."""

    workflow_config_path: Path
    workflow_id: str
    steps: tuple[ResearchWorkflowStepConfig, ...]

    @classmethod
    def from_yaml(cls, path: str | Path) -> ResearchWorkflowConfig:
        """Load and validate a research workflow YAML file."""

        workflow_path = Path(path)
        if not workflow_path.exists():
            raise FileNotFoundError(f"research workflow config not found: {workflow_path}")
        raw = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("research workflow config must be a YAML mapping")
        version = raw.get("version")
        if version != 1:
            raise ValueError("research workflow version must be 1")
        workflow_id = cls._required_safe_token(raw, "workflow_id")
        raw_steps = raw.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError("research workflow steps must not be empty")
        steps = tuple(cls._step_from_payload(index, item) for index, item in enumerate(raw_steps))
        return cls(
            workflow_config_path=workflow_path,
            workflow_id=workflow_id,
            steps=steps,
        )

    @staticmethod
    def _step_from_payload(index: int, payload: Any) -> ResearchWorkflowStepConfig:
        if not isinstance(payload, dict):
            raise ValueError(f"research workflow steps[{index}] must be a mapping")
        ResearchWorkflowConfig._reject_forbidden_keys(payload)
        step_id = ResearchWorkflowConfig._required_safe_token(payload, "id")
        kind = _required_text(payload, "kind")
        if kind not in _ALLOWED_STEP_KINDS:
            raise ValueError(f"unsupported workflow step kind: {kind}")
        step_payload = {
            str(key): value for key, value in payload.items() if key not in {"id", "kind"}
        }
        if kind == "implementation_gate":
            ResearchWorkflowConfig._validate_implementation_gate_payload(step_payload)
        return ResearchWorkflowStepConfig(
            step_id=step_id,
            kind=kind,
            payload=step_payload,
        )

    def resolve_path(self, value: str | Path) -> Path:
        """Resolve workflow-local paths relative to the workflow config file."""

        path = Path(value)
        if path.is_absolute():
            return path
        return self.workflow_config_path.parent / path

    @staticmethod
    def _required_safe_token(payload: Mapping[str, Any], field_name: str) -> str:
        value = _required_text(payload, field_name)
        if any(character not in _FILENAME_SAFE_CHARS for character in value):
            raise ValueError(f"{field_name} must be filename-safe")
        return value

    @staticmethod
    def _reject_forbidden_keys(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key)
                if key_text in _FORBIDDEN_WORKFLOW_KEYS:
                    raise ValueError(f"forbidden workflow key: {key_text}")
                ResearchWorkflowConfig._reject_forbidden_keys(item)
        elif isinstance(value, list):
            for item in value:
                ResearchWorkflowConfig._reject_forbidden_keys(item)

    @staticmethod
    def _validate_implementation_gate_payload(payload: Mapping[str, Any]) -> None:
        module_names = ResearchWorkflowConfig._string_sequence(
            payload.get("required_modules", ()),
            field_name="required_modules",
        )
        required_strategy = payload.get("required_strategy")
        if required_strategy is not None:
            module_names += (ResearchWorkflowConfig._strategy_module_name(str(required_strategy)),)
        for module_name in module_names:
            ResearchWorkflowConfig._reject_internal_implementation_import(module_name)

    @staticmethod
    def _string_sequence(value: Any, *, field_name: str) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, list | tuple):
            raise ValueError(f"{field_name} must be a sequence")
        return tuple(str(item) for item in value)

    @staticmethod
    def _strategy_module_name(value: str) -> str:
        if ":" not in value:
            return value
        return value.split(":", maxsplit=1)[0]

    @staticmethod
    def _reject_internal_implementation_import(module_name: str) -> None:
        if module_name == "qts" or (
            module_name.startswith("qts.")
            and not any(
                module_name == prefix or module_name.startswith(f"{prefix}.")
                for prefix in _ALLOWED_IMPLEMENTATION_QTS_PREFIXES
            )
        ):
            raise ValueError(f"implementation_gate cannot require internal module: {module_name}")


@dataclass(frozen=True, slots=True)
class ResearchWorkflowStepResult:
    """One deterministic workflow step execution result."""

    step_id: str
    kind: str
    status: str
    message: str
    outputs: Mapping[str, Any]

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready step result payload."""

        return {
            "id": self.step_id,
            "kind": self.kind,
            "message": self.message,
            "outputs": _json_ready(self.outputs),
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class ResearchWorkflowResult:
    """Deterministic workflow execution result."""

    workflow_id: str
    status: str
    steps: tuple[ResearchWorkflowStepResult, ...]

    @property
    def succeeded(self) -> bool:
        """Return whether all executed workflow steps passed."""

        return self.status == "completed"

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready workflow result payload."""

        return {
            "status": self.status,
            "steps": [step.to_payload() for step in self.steps],
            "workflow_id": self.workflow_id,
        }


class ResearchWorkflowRunner:
    """Runs research workflow steps through ``ResearchSession`` public APIs."""

    def run(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        *,
        step_id: str | None = None,
        from_step_id: str | None = None,
        to_step_id: str | None = None,
    ) -> ResearchWorkflowResult:
        """Run a workflow until completion or a blocking gate."""

        results: list[ResearchWorkflowStepResult] = []
        overall_status = "completed"
        for step in self._selected_steps(
            config,
            step_id=step_id,
            from_step_id=from_step_id,
            to_step_id=to_step_id,
        ):
            result = self._run_step(session, config, step, steps=tuple(results))
            results.append(result)
            if result.status != "passed":
                overall_status = "failed" if result.status == "failed" else "blocked"
                if (
                    result.status == "failed"
                    or step.kind in _HARD_STOP_STEP_KINDS
                    or step.payload.get("on_fail", "stop") == "stop"
                ):
                    break
        return ResearchWorkflowResult(
            workflow_id=config.workflow_id,
            status=overall_status,
            steps=tuple(results),
        )

    def _selected_steps(
        self,
        config: ResearchWorkflowConfig,
        *,
        step_id: str | None,
        from_step_id: str | None,
        to_step_id: str | None,
    ) -> tuple[ResearchWorkflowStepConfig, ...]:
        self._validate_selection(
            step_id=step_id,
            from_step_id=from_step_id,
            to_step_id=to_step_id,
        )
        if step_id is None and from_step_id is None and to_step_id is None:
            return config.steps
        step_index_by_id = {step.step_id: index for index, step in enumerate(config.steps)}
        if step_id is not None:
            return (config.steps[self._step_index(step_index_by_id, step_id)],)
        start_index = (
            0 if from_step_id is None else self._step_index(step_index_by_id, from_step_id)
        )
        end_index = (
            len(config.steps) - 1
            if to_step_id is None
            else self._step_index(step_index_by_id, to_step_id)
        )
        if start_index > end_index:
            raise ValueError(
                "workflow step range is empty: "
                f"{config.steps[start_index].step_id} is after {config.steps[end_index].step_id}"
            )
        return config.steps[start_index : end_index + 1]

    @staticmethod
    def _validate_selection(
        *,
        step_id: str | None,
        from_step_id: str | None,
        to_step_id: str | None,
    ) -> None:
        if step_id is not None and (from_step_id is not None or to_step_id is not None):
            raise ValueError("--step cannot be combined with --from-step or --to-step")
        for field_name, value in {
            "step_id": step_id,
            "from_step_id": from_step_id,
            "to_step_id": to_step_id,
        }.items():
            if value is not None and not value.strip():
                raise ValueError(f"{field_name} must not be empty")

    @staticmethod
    def _step_index(step_index_by_id: Mapping[str, int], step_id: str) -> int:
        try:
            return step_index_by_id[step_id]
        except KeyError as exc:
            raise ValueError(f"workflow step not found: {step_id}") from exc

    def _run_step(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
        *,
        steps: tuple[ResearchWorkflowStepResult, ...],
    ) -> ResearchWorkflowStepResult:
        try:
            if step.kind == "factor_candidates":
                return self._factor_candidates(session, step)
            if step.kind == "factor_review_gate":
                return self._factor_review_gate(session, step)
            if step.kind == "implementation_gate":
                return self._implementation_gate(step)
            if step.kind == "factor_evaluation":
                return self._factor_evaluation(session, config, step)
            if step.kind == "factor_tearsheet":
                return self._factor_tearsheet(session, config, step)
            if step.kind == "backtest":
                return self._backtest(session, config, step)
            if step.kind == "backtest_matrix":
                return self._backtest_matrix(session, config, step)
            if step.kind == "optimize":
                return self._optimize(session, config, step)
            if step.kind == "portfolio_ensemble":
                return self._portfolio_ensemble(config, step)
            if step.kind == "portfolio_ensemble_scan":
                return self._portfolio_ensemble_scan(config, step)
            if step.kind == "portfolio_volatility_managed_scan":
                return self._portfolio_volatility_managed_scan(config, step)
            if step.kind == "research_report":
                return self._research_report(config, steps, step)
        except Exception as exc:  # pragma: no cover - exercised by CLI integration.
            return ResearchWorkflowStepResult(
                step_id=step.step_id,
                kind=step.kind,
                status="failed",
                message=str(exc),
                outputs={},
            )
        raise ValueError(f"unsupported workflow step kind: {step.kind}")

    def _factor_candidates(
        self,
        session: Any,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        query = _required_text(step.payload, "query")
        batch = session.find_factor_candidates(
            query,
            sources=self._optional_string_tuple(step.payload.get("sources")),
            max_results=self._optional_int(step.payload.get("max_results")),
            from_year=self._optional_int(step.payload.get("from_year")),
            to_year=self._optional_int(step.payload.get("to_year")),
            refresh=bool(step.payload.get("refresh", False)),
        )
        specs = tuple(getattr(batch, "specs", ()))
        result_query = getattr(getattr(batch, "result", None), "query", None)
        outputs = {
            "candidate_count": len(specs),
            "query_id": getattr(result_query, "query_id", ""),
            "spec_names": [getattr(spec, "name", "") for spec in specs],
        }
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="factor candidates persisted",
            outputs=outputs,
        )

    def _factor_review_gate(
        self,
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
            "spec_names": [getattr(spec, "name", "") for spec in specs],
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

    def _implementation_gate(self, step: ResearchWorkflowStepConfig) -> ResearchWorkflowStepResult:
        required_modules = self._string_tuple(step.payload.get("required_modules", ()))
        required_strategy = step.payload.get("required_strategy")
        missing_modules = [module for module in required_modules if not self._can_import(module)]
        missing_strategies: list[str] = []
        if required_strategy is not None and not self._can_resolve_attribute(
            str(required_strategy)
        ):
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
        self,
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
                    "as_of": snapshot.get("as_of"),
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

    def _research_report(
        self,
        config: ResearchWorkflowConfig,
        steps: tuple[ResearchWorkflowStepResult, ...],
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
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
            outputs={"report_path": str(report_path)},
        )

    def _portfolio_ensemble(
        self,
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
            json.dumps(_json_ready(result), sort_keys=True, indent=2) + "\n",
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
        self,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        payload = dict(step.payload)
        payload["candidates"] = self._resolved_period_manifest_candidates(
            config,
            step,
            kind_name="portfolio_ensemble_scan",
        )
        result = scan_portfolio_ensemble_allocations(payload)
        summary_output = step.payload.get("summary_output")
        summary_path = (
            config.resolve_path(str(summary_output))
            if summary_output is not None
            else config.workflow_config_path.parent
            / f"{result['scan_name']}-portfolio-ensemble-scan-summary.json"
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(_json_ready(result), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="portfolio ensemble allocation scan written",
            outputs={
                "candidate_count": result["candidate_count"],
                "evaluated_allocation_count": result["evaluated_allocation_count"],
                "satisfying_allocation_count": result["satisfying_allocation_count"],
                "summary_path": str(summary_path),
            },
        )

    def _portfolio_volatility_managed_scan(
        self,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        payload = dict(step.payload)
        payload["candidates"] = self._resolved_period_manifest_candidates(
            config,
            step,
            kind_name="portfolio_volatility_managed_scan",
        )
        result = scan_volatility_managed_allocations(payload)
        summary_output = step.payload.get("summary_output")
        summary_path = (
            config.resolve_path(str(summary_output))
            if summary_output is not None
            else config.workflow_config_path.parent
            / f"{result['scan_name']}-portfolio-volatility-managed-summary.json"
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(_json_ready(result), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="portfolio volatility managed allocation scan written",
            outputs={
                "candidate_count": result["candidate_count"],
                "evaluated_parameter_count": result["evaluated_parameter_count"],
                "satisfying_allocation_count": result["satisfying_allocation_count"],
                "summary_path": str(summary_path),
            },
        )

    def _resolved_period_manifest_candidates(
        self,
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

    def _factor_tearsheet(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        raw_artifact_paths = step.payload.get(
            "artifact_paths",
            step.payload.get("artifacts", ()),
        )
        artifact_paths = tuple(
            config.resolve_path(path) for path in self._string_tuple(raw_artifact_paths)
        )
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
                dataset_ids=self._string_tuple(step.payload.get("dataset_ids", ())),
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
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        strategy_params = self._optional_mapping(step.payload.get("strategy_params")) or {}
        kwargs: dict[str, Any] = {"strategy_params": strategy_params}
        backtest_config = step.payload.get("backtest_config")
        if backtest_config is not None:
            kwargs["backtest_config_path"] = config.resolve_path(str(backtest_config))
        output_dir = step.payload.get("output_dir")
        if output_dir is not None:
            kwargs["output_dir"] = config.resolve_path(str(output_dir))
        materialized_cache_dir = self._materialized_replay_cache_dir(config, step.payload)
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
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        output_root = config.resolve_path(_required_text(step.payload, "output_root"))
        periods = self._matrix_periods(step.payload.get("periods"))
        candidates = self._matrix_candidates(step.payload.get("candidates"))
        base_strategy_params = (
            self._optional_mapping(step.payload.get("base_strategy_params")) or {}
        )
        metrics = self._string_tuple(
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
        materialized_cache_dir = self._materialized_replay_cache_dir(config, step.payload)
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
        summary_output = step.payload.get("summary_output")
        summary_path = (
            config.resolve_path(str(summary_output))
            if summary_output is not None
            else output_root / "summary.json"
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(_json_ready(summary_payload), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="backtest matrix completed",
            outputs={
                "candidate_count": len(candidates),
                "period_count": len(periods),
                "run_count": len(rows),
                "summary_path": str(summary_path),
            },
        )

    def _optimize(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        parameters = self._required_mapping(step.payload, "parameters")
        kwargs: dict[str, Any] = {
            "parameters": {str(key): list(value) for key, value in parameters.items()},
        }
        objective_metric = step.payload.get("objective_metric")
        if objective_metric is not None:
            kwargs["objective_metric"] = str(objective_metric)
        output_root = step.payload.get("output_root")
        if output_root is not None:
            kwargs["output_root"] = config.resolve_path(str(output_root))
        materialized_cache_dir = self._materialized_replay_cache_dir(config, step.payload)
        if materialized_cache_dir is not None:
            kwargs["materialized_replay_cache_dir"] = materialized_cache_dir
        results = session.optimize(**kwargs)
        capital_metric_config = self._optional_mapping(step.payload.get("capital_metrics"))
        constraints = self._validation_constraints(step.payload.get("validation"))
        validation_summary = OptimizerValidationSummary.from_results(
            results,
            constraints,
            capital_metric_config=capital_metric_config,
        )
        validation_output = step.payload.get("validation_output")
        validation_output_path: Path | None = None
        if validation_output is not None:
            validation_output_path = config.resolve_path(str(validation_output))
            OptimizerValidationSummaryWriter().write(validation_output_path, validation_summary)
        walk_forward_payload = self._walk_forward_payload(step.payload.get("validation"))
        walk_forward_summary_payload: dict[str, Any] | None = None
        walk_forward_robustness_payload: dict[str, Any] | None = None
        walk_forward_output_path: Path | None = None
        failure_veto_payload = self._failure_window_veto_payload(step.payload.get("validation"))
        failure_veto_summary_payload: dict[str, Any] | None = None
        failure_veto_output_path: Path | None = None
        failure_veto_blocked = False
        if walk_forward_payload is not None:
            plan = self._walk_forward_plan(walk_forward_payload)
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
            )
            walk_forward_summary_payload = walk_forward_summary.to_payload()
            robustness_policy = self._walk_forward_robustness_policy(
                walk_forward_payload.get("robustness")
            )
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
                        _json_ready(output_payload),
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
            require_passing_candidate = self._failure_veto_require_passing_candidate(
                failure_veto_payload
            )
            failure_veto_output_root = failure_veto_payload.get("output_root")
            failure_veto_summary = session.validate_optimizer_failure_window_veto(
                candidate_parameters=tuple(dict(result.parameters) for result in results[:top_n]),
                constraints=self._failure_veto_constraints(failure_veto_payload),
                capital_metric_config=capital_metric_config,
                objective_metric=(None if objective_metric is None else str(objective_metric)),
                output_root=(
                    None
                    if failure_veto_output_root is None
                    else config.resolve_path(str(failure_veto_output_root))
                ),
                windows=self._failure_windows(
                    failure_veto_payload,
                    field_name="windows",
                    report_only=False,
                ),
                report_only_windows=self._failure_windows(
                    failure_veto_payload,
                    field_name="report_only_windows",
                    report_only=True,
                ),
                materialized_replay_cache_dir=materialized_cache_dir,
            )
            failure_veto_summary_payload = failure_veto_summary.to_payload()
            raw_failure_veto_output = failure_veto_payload.get("summary_output")
            if raw_failure_veto_output is not None:
                failure_veto_output_path = config.resolve_path(str(raw_failure_veto_output))
                failure_veto_output_path.parent.mkdir(parents=True, exist_ok=True)
                failure_veto_output_path.write_text(
                    json.dumps(
                        _json_ready(failure_veto_summary_payload),
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
        ranked_results = []
        for result in results:
            ranked_result = {
                "manifest_hash": result.manifest_hash,
                "manifest_path": str(result.manifest_path),
                "objective_value": str(result.objective_value),
                "parameters": dict(result.parameters),
            }
            if capital_metric_config is not None:
                ranked_result["capital_metrics"] = derive_capital_metrics(
                    result,
                    capital_metric_config,
                )
            ranked_results.append(ranked_result)
        outputs: dict[str, Any] = {
            "ranked_results": ranked_results,
            "run_count": len(results),
            "validation_output": (
                None if validation_output_path is None else str(validation_output_path)
            ),
            "validation_summary": validation_summary.to_payload(),
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
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="blocked" if failure_veto_blocked else "passed",
            message=(
                "failure-window veto blocked workflow"
                if failure_veto_blocked
                else "optimization completed"
            ),
            outputs=outputs,
        )

    def _validation_constraints(self, value: Any) -> tuple[MetricConstraint, ...]:
        validation = self._optional_mapping(value)
        if validation is None:
            return ()
        raw_constraints = validation.get("constraints")
        if raw_constraints is None:
            return ()
        return self._metric_constraints_from_sequence(
            raw_constraints,
            field_name="validation.constraints",
        )

    def _materialized_replay_cache_dir(
        self,
        config: ResearchWorkflowConfig,
        payload: Mapping[str, Any],
    ) -> Path | None:
        value = payload.get("materialized_replay_cache")
        if value is None or value is False:
            return None
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("materialized_replay_cache must not be empty")
            return config.resolve_path(value)
        if isinstance(value, Mapping):
            if not bool(value.get("enabled", False)):
                return None
            raw_cache_dir = value.get("cache_dir")
            if not isinstance(raw_cache_dir, str) or not raw_cache_dir.strip():
                raise ValueError("materialized_replay_cache.cache_dir is required")
            return config.resolve_path(raw_cache_dir)
        raise ValueError("materialized_replay_cache must be a path or mapping")

    def _metric_constraints_from_sequence(
        self,
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

    def _walk_forward_payload(self, value: Any) -> dict[str, Any] | None:
        validation = self._optional_mapping(value)
        if validation is None:
            return None
        raw_walk_forward = validation.get("walk_forward")
        if raw_walk_forward is None:
            return None
        if not isinstance(raw_walk_forward, Mapping):
            raise ValueError("validation.walk_forward must be a mapping")
        return dict(raw_walk_forward)

    def _failure_window_veto_payload(self, value: Any) -> dict[str, Any] | None:
        validation = self._optional_mapping(value)
        if validation is None:
            return None
        raw_veto = validation.get("failure_window_veto")
        if raw_veto is None:
            return None
        if not isinstance(raw_veto, Mapping):
            raise ValueError("validation.failure_window_veto must be a mapping")
        return dict(raw_veto)

    def _failure_veto_constraints(
        self,
        value: Mapping[str, Any],
    ) -> tuple[MetricConstraint, ...]:
        raw_constraints = value.get("constraints")
        if raw_constraints is None or not isinstance(raw_constraints, list) or not raw_constraints:
            raise ValueError("validation.failure_window_veto.constraints must be a non-empty list")
        return self._metric_constraints_from_sequence(
            raw_constraints,
            field_name="validation.failure_window_veto.constraints",
        )

    @staticmethod
    def _failure_veto_require_passing_candidate(value: Mapping[str, Any]) -> bool:
        raw_value = value.get("require_passing_candidate", False)
        if not isinstance(raw_value, bool):
            raise ValueError(
                "validation.failure_window_veto.require_passing_candidate must be a boolean"
            )
        return raw_value

    def _failure_windows(
        self,
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
                    start=self._iso_date(window["start"], "start"),
                    end=self._iso_date(window["end"], "end"),
                    report_only=report_only,
                )
            )
        return tuple(windows)

    def _walk_forward_plan(self, value: Mapping[str, Any]) -> WalkForwardPlan:
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
                    train_start=self._iso_date(split["train_start"], "train_start"),
                    train_end=self._iso_date(split["train_end"], "train_end"),
                    test_start=self._iso_date(split["test_start"], "test_start"),
                    test_end=self._iso_date(split["test_end"], "test_end"),
                )
            )
        return WalkForwardPlan(tuple(splits))

    def _matrix_periods(self, value: Any) -> tuple[dict[str, Any], ...]:
        if not isinstance(value, list) or not value:
            raise ValueError("backtest_matrix.periods must be a non-empty list")
        periods: list[dict[str, Any]] = []
        for index, raw_period in enumerate(value):
            if not isinstance(raw_period, Mapping):
                raise ValueError(f"backtest_matrix.periods[{index}] must be a mapping")
            period = dict(raw_period)
            periods.append(
                {
                    "end": self._iso_datetime(period["end"], "end"),
                    "name": self._safe_token(period, "name"),
                    "start": self._iso_datetime(period["start"], "start"),
                }
            )
        return tuple(periods)

    def _matrix_candidates(self, value: Any) -> tuple[dict[str, Any], ...]:
        if not isinstance(value, list) or not value:
            raise ValueError("backtest_matrix.candidates must be a non-empty list")
        candidates: list[dict[str, Any]] = []
        for index, raw_candidate in enumerate(value):
            if not isinstance(raw_candidate, Mapping):
                raise ValueError(f"backtest_matrix.candidates[{index}] must be a mapping")
            candidate = dict(raw_candidate)
            strategy_params = self._optional_mapping(candidate.get("strategy_params")) or {}
            candidates.append(
                {
                    "name": self._safe_token(candidate, "name"),
                    "strategy_params": strategy_params,
                }
            )
        return tuple(candidates)

    @staticmethod
    def _safe_token(payload: Mapping[str, Any], field_name: str) -> str:
        value = _required_text(payload, field_name)
        if any(character not in _FILENAME_SAFE_CHARS for character in value):
            raise ValueError(f"{field_name} must be filename-safe")
        return value

    def _walk_forward_robustness_policy(
        self,
        value: Any,
    ) -> WalkForwardRobustnessPolicy | None:
        payload = self._optional_mapping(value)
        if payload is None:
            return None
        phases = self._string_tuple(payload.get("phases", ["test"]))
        return WalkForwardRobustnessPolicy(
            phases=phases,
            min_windows=self._optional_int(payload.get("min_windows")),
            max_losing_windows=self._optional_int(payload.get("max_losing_windows")),
            min_window_pnl_usd=self._optional_decimal(payload.get("min_window_pnl_usd")),
            min_window_best_objective=self._optional_decimal(
                payload.get("min_window_best_objective")
            ),
            min_total_pnl_usd=self._optional_decimal(payload.get("min_total_pnl_usd")),
        )

    @staticmethod
    def _iso_date(value: Any, field_name: str) -> date:
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO date") from exc

    @staticmethod
    def _iso_datetime(value: Any, field_name: str) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        if isinstance(value, date):
            return datetime.combine(value, time.min, tzinfo=UTC)
        text = str(value)
        if len(text) == len("YYYY-MM-DD"):
            return datetime.combine(date.fromisoformat(text), time.min, tzinfo=UTC)
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO datetime or date") from exc
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)

    @staticmethod
    def _required_mapping(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
        value = payload.get(field_name)
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a mapping")
        return dict(value)

    @staticmethod
    def _optional_mapping(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError("value must be a mapping")
        return dict(value)

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None:
            return None
        return int(value)

    @staticmethod
    def _optional_decimal(value: Any) -> Decimal | None:
        if value is None:
            return None
        return Decimal(str(value))

    @staticmethod
    def _string_tuple(value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, list | tuple):
            raise ValueError("value must be a sequence")
        return tuple(str(item) for item in value)

    @classmethod
    def _optional_string_tuple(cls, value: Any) -> tuple[str, ...] | None:
        if value is None:
            return None
        return cls._string_tuple(value)

    @staticmethod
    def _can_import(module_name: str) -> bool:
        try:
            importlib.import_module(module_name)
        except ImportError:
            return False
        return True

    @staticmethod
    def _can_resolve_attribute(value: str) -> bool:
        if ":" not in value:
            return False
        module_name, attribute_name = value.split(":", maxsplit=1)
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return False
        return hasattr(module, attribute_name)


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_ready(item) for item in value]
    return value


__all__ = [
    "ResearchWorkflowConfig",
    "ResearchWorkflowResult",
    "ResearchWorkflowRunner",
    "ResearchWorkflowStepConfig",
    "ResearchWorkflowStepResult",
]

_ALLOWED_STEP_KINDS = frozenset(
    {
        "backtest",
        "backtest_matrix",
        "factor_candidates",
        "factor_review_gate",
        "factor_evaluation",
        "factor_tearsheet",
        "implementation_gate",
        "optimize",
        "portfolio_ensemble",
        "portfolio_ensemble_scan",
        "portfolio_volatility_managed_scan",
        "research_report",
    }
)
_HARD_STOP_STEP_KINDS = frozenset({"factor_review_gate", "implementation_gate"})
_ALLOWED_IMPLEMENTATION_QTS_PREFIXES = ("qts.factors", "qts.indicators")
_FORBIDDEN_WORKFLOW_KEYS = frozenset(
    {
        "broker",
        "generate_code",
        "live",
        "orders",
        "paper",
        "promote",
        "promotion",
        "runtime",
        "trade",
    }
)
_FILENAME_SAFE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
