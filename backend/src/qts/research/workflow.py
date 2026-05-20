"""Gate-based research workflow orchestration."""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


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

    def run(self, session: Any, config: ResearchWorkflowConfig) -> ResearchWorkflowResult:
        """Run a workflow until completion or a blocking gate."""

        results: list[ResearchWorkflowStepResult] = []
        overall_status = "completed"
        for step in config.steps:
            result = self._run_step(session, config, step)
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

    def _run_step(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        try:
            if step.kind == "factor_candidates":
                return self._factor_candidates(session, step)
            if step.kind == "factor_review_gate":
                return self._factor_review_gate(session, step)
            if step.kind == "implementation_gate":
                return self._implementation_gate(step)
            if step.kind == "factor_tearsheet":
                return self._factor_tearsheet(session, config, step)
            if step.kind == "backtest":
                return self._backtest(session, config, step)
            if step.kind == "optimize":
                return self._optimize(session, config, step)
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
        output_dir = step.payload.get("output_dir")
        if output_dir is not None:
            kwargs["output_dir"] = config.resolve_path(str(output_dir))
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
        results = session.optimize(**kwargs)
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="optimization completed",
            outputs={
                "ranked_results": [
                    {
                        "manifest_hash": result.manifest_hash,
                        "manifest_path": str(result.manifest_path),
                        "objective_value": str(result.objective_value),
                        "parameters": dict(result.parameters),
                    }
                    for result in results
                ],
                "run_count": len(results),
            },
        )

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
        "factor_candidates",
        "factor_review_gate",
        "factor_tearsheet",
        "implementation_gate",
        "optimize",
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
