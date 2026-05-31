"""Stateless trial-processing helpers for ResearchExperimentRunner.

Validation reruns, backtest-window config resolution, artifact hashing/manifest
refresh, metrics extraction, and JSON/YAML I/O utilities extracted from
ResearchExperimentRunner (QTS-FINAL-011) as pure module functions (no trial state).
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_dumps
from qts.research.optimizer.parameter_space import ParameterGrid, ParameterSpace
from qts.research.optimizer.pipeline import BacktestPipelineJob, BacktestPipelineRunner
from qts.research.orchestrator.validation_artifact_writer import (
    manifest_artifact_row_count,
    manifest_decimal,
    write_stable_json,
)


def _artifact_row_count(manifest: Mapping[str, Any], artifact_name: str) -> int:
    return manifest_artifact_row_count(manifest, artifact_name)


def _attach_validation_artifacts_to_workflow_summary(
    workflow_summary_path: Path,
    validation_artifact_paths: Mapping[str, Path],
) -> None:
    summary = _read_json_mapping(workflow_summary_path)
    raw_steps = summary.get("steps")
    if not isinstance(raw_steps, Sequence) or isinstance(raw_steps, str):
        raise ValueError(f"workflow summary steps must be a sequence: {workflow_summary_path}")
    steps = [dict(step) for step in raw_steps if isinstance(step, Mapping)]
    existing_ids = {str(step.get("id", "")) for step in steps}
    for artifact_name, artifact_path in sorted(validation_artifact_paths.items()):
        if artifact_name in existing_ids:
            continue
        steps.append(
            {
                "id": artifact_name,
                "kind": "validation_artifact",
                "outputs": {"artifact_path": str(artifact_path)},
                "status": "passed",
            }
        )
    _write_json(workflow_summary_path, {**dict(summary), "steps": steps})


def _audit_time(trial_index: int, event_index: int) -> datetime:
    return datetime(2026, 5, 26, tzinfo=UTC) + timedelta(seconds=(trial_index * 10) + event_index)


def _backtest_config_window(base_config_path: Path) -> tuple[datetime, datetime]:
    payload = _yaml_mapping(base_config_path)
    start = datetime.fromisoformat(str(payload["start"]).replace("Z", "+00:00"))
    end = datetime.fromisoformat(str(payload["end"]).replace("Z", "+00:00"))
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError(f"backtest validation window must be timezone-aware: {base_config_path}")
    start = start.astimezone(UTC)
    end = end.astimezone(UTC)
    if start >= end:
        raise ValueError(f"invalid backtest validation window: {start} >= {end}")
    return start, end


def _backtest_manifest_from_metrics(metrics_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    backtest = _mapping(metrics_payload.get("backtest", {}), "backtest")
    manifest_path_text = backtest.get("manifest_path")
    if not isinstance(manifest_path_text, str) or not manifest_path_text.strip():
        raise ValueError("metrics backtest.manifest_path is required for validation artifacts")
    return _read_json_mapping(Path(manifest_path_text))


def _backtest_pipeline_config_from_payloads(
    manifest_payload: Mapping[str, Any],
    trial: Mapping[str, Any],
) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for field_name in ("backtest", "backtest_pipeline"):
        value = manifest_payload.get(field_name)
        if isinstance(value, Mapping):
            config.update(dict(value))
    trial_config = trial.get("backtest_pipeline")
    if isinstance(trial_config, Mapping):
        config.update(dict(trial_config))
    for field_name in (
        "backtest_config_path",
        "base_config_path",
        "objective_metric",
        "materialized_replay_cache_dir",
    ):
        if field_name in trial:
            config[field_name] = trial[field_name]
    return config


def _cost_stress_config_path(*, base_config_path: Path, output_dir: Path) -> Path:
    payload = _yaml_mapping(base_config_path)
    cost_payload = payload.get("cost_model", {})
    if not isinstance(cost_payload, Mapping):
        raise ValueError(f"cost_model must be a mapping: {base_config_path}")
    stressed_cost = dict(cost_payload)
    stressed_cost["fixed_commission_per_contract"] = str(
        _decimal(stressed_cost.get("fixed_commission_per_contract", 0)) + Decimal("1")
    )
    stressed_cost["slippage_bps"] = str(
        _decimal(stressed_cost.get("slippage_bps", 0)) + Decimal("1")
    )
    payload["cost_model"] = stressed_cost
    path = output_dir / "cost_stress.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _data_hashes(data: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    checked_paths = data.get("checked_paths", ())
    if isinstance(checked_paths, Sequence) and not isinstance(checked_paths, str):
        for path_text in checked_paths:
            path = Path(str(path_text))
            result[str(path)] = _sha256_path(path) if path.exists() else "sha256:missing"
    return result


def _data_quality_windows(value: Any) -> tuple[Mapping[str, str], ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, str):
        return ()
    windows: list[Mapping[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        start = item.get("start")
        end = item.get("end")
        if isinstance(start, str) and isinstance(end, str):
            windows.append({"end": end, "start": start})
    return tuple(windows)


def _decimal(value: Any) -> Decimal:
    return manifest_decimal(value)


def _edge_type(family: str) -> str:
    allowed = {
        "carry",
        "cross_sectional_momentum",
        "event_driven",
        "execution_alpha",
        "liquidity",
        "macro",
        "macro_regime",
        "mean_reversion",
        "microstructure",
        "momentum",
        "quality",
        "relative_value",
        "reversal",
        "seasonality",
        "sentiment",
        "term_structure",
        "time_series_momentum",
        "value",
        "volatility",
    }
    if family in allowed:
        return family
    if family == "spread":
        return "relative_value"
    if family == "breakout":
        return "time_series_momentum"
    return "momentum"


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _merged_manifest(
    base: Mapping[str, Any],
    patch: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(base)
    for key, value in patch.items():
        current = result.get(key)
        if isinstance(current, Mapping) and isinstance(value, Mapping):
            result[str(key)] = _merged_manifest(current, value)
        else:
            result[str(key)] = value
    return dict(json.loads(stable_json_dumps(result)).items())


def _oos_returns_from_manifest(manifest: Mapping[str, Any]) -> list[float]:
    """Return the per-period return series from the backtest equity-curve artifact.

    The Probability-of-Backtest-Overfitting (PBO/CSCV) estimator needs the
    realized return series; it is derived from the equity_curve artifact the
    backtest writes. Returns an empty list when the artifact is absent so the
    PBO computation degrades to its documented neutral value.
    """
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return []
    equity_artifact = artifacts.get("equity_curve")
    if not isinstance(equity_artifact, Mapping):
        return []
    path_text = equity_artifact.get("path")
    if not isinstance(path_text, str) or not path_text.strip():
        return []
    path = Path(path_text)
    if not path.exists():
        return []
    equities: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            return []
        if not isinstance(row, Mapping):
            continue
        equity = _optional_metric_float(row.get("equity"))
        if equity is not None:
            equities.append(equity)
    returns: list[float] = []
    for index in range(1, len(equities)):
        previous = equities[index - 1]
        if previous != 0.0:
            returns.append((equities[index] - previous) / previous)
    return returns


def _optional_metric_float(value: Any) -> float | None:
    """Coerce a serialized scalar metric to float, or None when absent."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _optional_metric_int(value: Any) -> int | None:
    """Coerce a serialized count metric to int, or None when absent."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _pipeline_parameters(
    parameters: Mapping[str, Any],
    pipeline_config: Mapping[str, Any],
) -> dict[str, Any]:
    defaults = pipeline_config.get("strategy_parameter_defaults", {})
    if defaults is not None and not isinstance(defaults, Mapping):
        raise ValueError("backtest_pipeline strategy_parameter_defaults must be a mapping")
    result: dict[str, Any] = dict(defaults or {})

    parameter_map = pipeline_config.get("strategy_parameter_map")
    if parameter_map is not None:
        if not isinstance(parameter_map, Mapping):
            raise ValueError("backtest_pipeline strategy_parameter_map must be a mapping")
        for source_name, target_name in sorted(parameter_map.items()):
            source = str(source_name)
            if source not in parameters:
                raise ValueError(
                    f"backtest_pipeline strategy parameter missing from trial parameters: {source}"
                )
            result[str(target_name)] = parameters[source]
        return result

    parameter_names = pipeline_config.get("strategy_parameter_names")
    if parameter_names is None:
        result.update(dict(parameters))
        return result
    if not isinstance(parameter_names, Sequence) or isinstance(parameter_names, str):
        raise ValueError("backtest_pipeline strategy_parameter_names must be a sequence")
    for name in tuple(str(item) for item in parameter_names):
        if name not in parameters:
            raise ValueError(
                f"backtest_pipeline strategy parameter missing from trial parameters: {name}"
            )
        result[name] = parameters[name]
    return result


def _python_hash_seed() -> int:
    value = sys.hash_info.width
    return int(value)


def _read_json_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON file must contain an object: {path}")
    return dict(payload)


def _refresh_manifest_artifact_hash(
    *,
    manifest_path: Path,
    artifact_name: str,
    artifact_path: Path,
) -> None:
    """Update a trial manifest's recorded hash for a rewritten artifact.

    Keeps ``artifact_hashes[artifact_name]`` and ``artifact_paths_by_hash``
    consistent with the artifact's current on-disk content so evidence
    bundle verification can recompute the hash from a registered path.
    """
    manifest = dict(_read_json_mapping(manifest_path))
    artifact_hashes = dict(_mapping(manifest.get("artifact_hashes", {}), "artifact_hashes"))
    if artifact_name not in artifact_hashes:
        return
    stale_hash = artifact_hashes[artifact_name]
    fresh_hash = _sha256_path(artifact_path)
    if fresh_hash == stale_hash:
        return
    artifact_hashes[artifact_name] = fresh_hash
    artifact_paths_by_hash = dict(
        _mapping(manifest.get("artifact_paths_by_hash", {}), "artifact_paths_by_hash")
    )
    artifact_paths_by_hash.pop(stale_hash, None)
    artifact_paths_by_hash[fresh_hash] = str(artifact_path)
    manifest["artifact_hashes"] = artifact_hashes
    manifest["artifact_paths_by_hash"] = artifact_paths_by_hash
    _write_json(manifest_path, manifest)


def _run_validation_backtest(
    *,
    base_config_path: Path,
    parameters: Mapping[str, Any],
    objective_metric: str,
    output_root: Path,
    materialized_replay_cache_dir: Path | None,
) -> tuple[Any, Mapping[str, Any]]:
    result = BacktestPipelineRunner().run(
        BacktestPipelineJob(
            base_config_path=base_config_path,
            parameter_grid=ParameterGrid(
                *(
                    ParameterSpace(name=str(name), values=(value,))
                    for name, value in sorted(parameters.items())
                )
            ),
            output_root=output_root,
            objective_metric=objective_metric,
            materialized_replay_cache_dir=materialized_replay_cache_dir,
        )
    )
    if len(result) != 1:
        raise ValueError("validation backtest must produce exactly one result")
    validation_result = result[0]
    return validation_result, _read_json_mapping(Path(validation_result.manifest_path))


def _run_walk_forward_reruns(
    *,
    base_config_path: Path,
    parameters: Mapping[str, Any],
    objective_metric: str,
    output_root: Path,
    materialized_replay_cache_dir: Path | None,
) -> tuple[Any, Mapping[str, Any], Any, Mapping[str, Any]]:
    start, end = _backtest_config_window(base_config_path)
    midpoint = start + ((end - start) / 2)
    if midpoint <= start or midpoint >= end:
        raise ValueError(f"cannot split backtest window for walk-forward: {start} -> {end}")
    config_dir = output_root / "configs"
    train_config = _window_config_path(
        base_config_path=base_config_path,
        output_path=config_dir / "walk_forward_train.yaml",
        start=start,
        end=midpoint,
    )
    test_config = _window_config_path(
        base_config_path=base_config_path,
        output_path=config_dir / "walk_forward_test.yaml",
        start=midpoint,
        end=end,
    )
    train_result, train_manifest = _run_validation_backtest(
        base_config_path=train_config,
        parameters=parameters,
        objective_metric=objective_metric,
        output_root=output_root / "train",
        materialized_replay_cache_dir=materialized_replay_cache_dir,
    )
    test_result, test_manifest = _run_validation_backtest(
        base_config_path=test_config,
        parameters=parameters,
        objective_metric=objective_metric,
        output_root=output_root / "test",
        materialized_replay_cache_dir=materialized_replay_cache_dir,
    )
    return train_result, train_manifest, test_result, test_manifest


def _sha256_path(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _trial_status(trial: Mapping[str, Any]) -> str:
    return "failed" if trial.get("status") == "failed" else "succeeded"


def _window_config_path(
    *,
    base_config_path: Path,
    output_path: Path,
    start: datetime,
    end: datetime,
) -> Path:
    payload = _yaml_mapping(base_config_path)
    payload["start"] = start.isoformat()
    payload["end"] = end.isoformat()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return output_path


def _write_json(path: Path, payload: Any) -> None:
    write_stable_json(path, payload)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(dict(row), sort_keys=True) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _write_report(path: Path, *, trial_id: str, status: str) -> None:
    path.write_text(
        f"# Research Trial Report\n\ntrial_id: {trial_id}\nstatus: {status}\n",
        encoding="utf-8",
    )


def _write_strategy_variant_artifact(
    *,
    trial_dir: Path,
    trial: Mapping[str, Any],
    manifest_payload: Mapping[str, Any],
) -> Path | None:
    strategy_variant_id = trial.get("strategy_variant_id")
    strategy_variant_hash = trial.get("strategy_variant_hash")
    if strategy_variant_id is None and strategy_variant_hash is None:
        return None
    path = trial_dir / "strategy_variant.json"
    manifest_patch = trial.get("manifest_patch")
    research_factory = {}
    if isinstance(manifest_patch, Mapping):
        research_factory_raw = manifest_patch.get("research_factory", {})
        if isinstance(research_factory_raw, Mapping):
            research_factory = dict(research_factory_raw)
    payload = {
        "candidate_id": trial.get("candidate_id"),
        "candidate_space_hash": trial.get("candidate_space_hash"),
        "factor_hash": trial.get("factor_hash"),
        "family": trial.get("family"),
        "manifest_patch": dict(manifest_patch) if isinstance(manifest_patch, Mapping) else {},
        "manifest_patch_hash": manifest_payload.get("manifest_patch_hash"),
        "parameters": dict(_mapping(trial.get("parameters", {}), "parameters")),
        "strategy_variant_hash": None
        if strategy_variant_hash is None
        else str(strategy_variant_hash),
        "strategy_variant_id": None if strategy_variant_id is None else str(strategy_variant_id),
        "template_id": research_factory.get("template_id"),
        "trial_id": _text(trial.get("trial_id"), "trial_id"),
    }
    _write_json(path, payload)
    return path


def _yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    return dict(payload)


__all__ = [
    "_artifact_row_count",
    "_attach_validation_artifacts_to_workflow_summary",
    "_audit_time",
    "_backtest_config_window",
    "_backtest_manifest_from_metrics",
    "_backtest_pipeline_config_from_payloads",
    "_cost_stress_config_path",
    "_data_hashes",
    "_data_quality_windows",
    "_decimal",
    "_edge_type",
    "_mapping",
    "_merged_manifest",
    "_oos_returns_from_manifest",
    "_optional_metric_float",
    "_optional_metric_int",
    "_pipeline_parameters",
    "_python_hash_seed",
    "_read_json_mapping",
    "_refresh_manifest_artifact_hash",
    "_run_validation_backtest",
    "_run_walk_forward_reruns",
    "_sha256_path",
    "_text",
    "_trial_status",
    "_window_config_path",
    "_write_json",
    "_write_jsonl",
    "_write_report",
    "_write_strategy_variant_artifact",
    "_yaml_mapping",
]
