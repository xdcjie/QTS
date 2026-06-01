"""Read-only research dashboard API routes."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]
from fastapi import APIRouter, HTTPException, Query, Request

from qts.api.schemas import (
    PromotionDecisionListSchema,
    ResearchReportListSchema,
    ResearchReportSchema,
    ResearchRunComparisonSchema,
    ResearchRunListSchema,
    StrategyLifecycleListSchema,
)
from qts.research.evidence_registry import EvidenceRegistry, ResearchEvidenceBundle
from qts.research.experiment_store import ExperimentStore, ExperimentStoreRecord
from qts.research.idea_registry import IdeaRegistry
from qts.research.registry import ResearchRunRecord, ResearchRunRegistry

router = APIRouter(prefix="/backtests/research")


@router.get("/runs", response_model=ResearchRunListSchema)
def list_research_runs(
    request: Request,
    strategy_name: str | None = Query(default=None, min_length=1),
    idea_id: str | None = Query(default=None, min_length=1),
    status: str | None = Query(default=None, min_length=1),
    limit: int | None = Query(default=None, ge=1),
) -> tuple[Any, ...]:
    """List indexed research runs from research artifact and experiment registries."""

    rows = tuple(
        row
        for row in _research_run_rows(request)
        if _matches_run_filter(row, strategy_name=strategy_name, idea_id=idea_id, status=status)
    )
    return rows[:limit] if limit is not None else rows


@router.get("/reports", response_model=ResearchReportListSchema)
def list_research_reports(request: Request) -> tuple[Any, ...]:
    """List indexed research evidence reports."""

    return tuple(_report_schema(bundle) for bundle in _evidence_registry(request).list())


@router.get("/reports/{evidence_bundle_id}", response_model=ResearchReportSchema)
def get_research_report(
    request: Request,
    evidence_bundle_id: str,
) -> Any:
    """Return one research evidence report with a bounded markdown preview."""

    bundle = _bundle_by_id(request, evidence_bundle_id)
    return _report_schema(bundle, include_preview=True)


@router.get(
    "/promotion-decisions",
    response_model=PromotionDecisionListSchema,
)
def list_promotion_decisions(request: Request) -> tuple[Any, ...]:
    """List research promotion decisions and candidate/readiness evidence."""

    decisions: list[Any] = []
    for path, payload in _promotion_candidate_payloads(_promotion_root(request)):
        decisions.append(
            {
                "decision_id": str(payload.get("promotion_candidate_id", path.stem)),
                "strategy_id": _optional_text(payload.get("strategy_id")),
                "evidence_bundle_id": _optional_text(payload.get("evidence_bundle_id")),
                "status": str(payload.get("status", "review_required")),
                "source": "promotion_candidate",
                "decided_at": None,
                "payload": dict(payload),
            }
        )
    for path, payload in _readiness_payloads(_readiness_root(request)):
        decisions.append(
            {
                "decision_id": str(path.relative_to(_readiness_root(request))),
                "strategy_id": _optional_text(payload.get("strategy_id")),
                "evidence_bundle_id": _optional_text(payload.get("evidence_bundle_id")),
                "status": str(
                    payload.get(
                        "target_status",
                        payload.get("paper_live_readiness_gate", "readiness_recorded"),
                    )
                ),
                "source": "readiness_gate",
                "decided_at": _optional_text(payload.get("decision_date")),
                "payload": dict(payload),
            }
        )
    return tuple(decisions)


@router.get("/lifecycle", response_model=StrategyLifecycleListSchema)
def list_strategy_lifecycle(request: Request) -> tuple[Any, ...]:
    """Return strategy lifecycle status from idea, evidence, and promotion records."""

    idea_status: dict[str, str] = {}
    for idea in IdeaRegistry(_idea_registry_root(request)).list_ideas():
        idea_status[idea.idea_id] = idea.status

    strategy_by_idea: dict[str, str] = {}
    for bundle in _evidence_registry(request).list():
        if bundle.idea_id and bundle.strategy_id:
            strategy_by_idea[bundle.idea_id] = bundle.strategy_id

    promotion_by_strategy = {
        str(payload["strategy_id"]): str(payload.get("status", "review_required"))
        for _, payload in _promotion_candidate_payloads(_promotion_root(request))
        if payload.get("strategy_id")
    }
    readiness_by_strategy = _latest_readiness_by_strategy(_readiness_root(request))

    strategy_ids = (
        set(promotion_by_strategy) | set(readiness_by_strategy) | set(strategy_by_idea.values())
    )
    rows: list[Any] = []
    for idea_id, status in idea_status.items():
        strategy_id = strategy_by_idea.get(idea_id, idea_id)
        strategy_ids.discard(strategy_id)
        rows.append(
            {
                "strategy_id": strategy_id,
                "idea_id": idea_id,
                "lifecycle_status": status,
                "promotion_status": promotion_by_strategy.get(strategy_id),
                "latest_readiness_status": readiness_by_strategy.get(strategy_id),
            }
        )
    for strategy_id in sorted(strategy_ids):
        rows.append(
            {
                "strategy_id": strategy_id,
                "idea_id": None,
                "lifecycle_status": "unknown",
                "promotion_status": promotion_by_strategy.get(strategy_id),
                "latest_readiness_status": readiness_by_strategy.get(strategy_id),
            }
        )
    return tuple(sorted(rows, key=lambda row: str(row["strategy_id"])))


@router.get("/compare", response_model=ResearchRunComparisonSchema)
def compare_research_runs(
    request: Request,
    left_run_id: str = Query(min_length=1),
    right_run_id: str = Query(min_length=1),
    metric: str = Query(min_length=1),
) -> Any:
    """Compare one numeric metric between two indexed research runs."""

    rows = {str(row["run_id"]): row for row in _research_run_rows(request)}
    left = rows.get(left_run_id)
    right = rows.get(right_run_id)
    if left is None or right is None:
        raise HTTPException(status_code=404, detail="research run not found")
    left_value = _numeric_metric(left, metric)
    right_value = _numeric_metric(right, metric)
    return {
        "left_run_id": left_run_id,
        "right_run_id": right_run_id,
        "metric": metric,
        "left_value": left_value,
        "right_value": right_value,
        "delta": left_value - right_value,
    }


def _experiment_store(request: Request) -> ExperimentStore:
    return ExperimentStore(
        _root_path(
            request,
            "research_experiment_store_root",
            "QTS_RESEARCH_EXPERIMENT_STORE_ROOT",
            Path("runs/research/meta"),
        )
    )


def _evidence_registry(request: Request) -> EvidenceRegistry:
    return EvidenceRegistry(
        _root_path(
            request,
            "research_evidence_root",
            "QTS_RESEARCH_EVIDENCE_ROOT",
            Path("runs/research/evidence"),
        )
    )


def _idea_registry_root(request: Request) -> Path:
    return _root_path(
        request,
        "research_idea_registry_root",
        "QTS_RESEARCH_IDEA_REGISTRY_ROOT",
        Path("runs/research/idea_registry"),
    )


def _promotion_root(request: Request) -> Path:
    return _root_path(
        request,
        "research_promotion_root",
        "QTS_RESEARCH_PROMOTION_ROOT",
        Path("configs/research/promotion"),
    )


def _readiness_root(request: Request) -> Path:
    return _root_path(
        request,
        "research_readiness_root",
        "QTS_RESEARCH_READINESS_ROOT",
        Path("artifacts/readiness"),
    )


def _artifact_registry(request: Request) -> ResearchRunRegistry:
    return ResearchRunRegistry.from_root(
        _root_path(
            request,
            "research_artifact_root",
            "QTS_RESEARCH_ARTIFACT_ROOT",
            Path("artifacts/research"),
        )
    )


def _root_path(request: Request, state_name: str, env_name: str, default: Path) -> Path:
    value = _state_root_value(request, state_name)
    if value is None:
        value = os.getenv(env_name)
    return default if value is None else Path(value)


def _state_root_value(request: Request, state_name: str) -> str | Path | None:
    state = request.app.state
    try:
        if state_name == "research_experiment_store_root":
            return cast(str | Path, state.research_experiment_store_root)
        if state_name == "research_evidence_root":
            return cast(str | Path, state.research_evidence_root)
        if state_name == "research_idea_registry_root":
            return cast(str | Path, state.research_idea_registry_root)
        if state_name == "research_promotion_root":
            return cast(str | Path, state.research_promotion_root)
        if state_name == "research_readiness_root":
            return cast(str | Path, state.research_readiness_root)
        if state_name == "research_artifact_root":
            return cast(str | Path, state.research_artifact_root)
    except AttributeError:
        return None
    raise ValueError(f"unsupported research state root: {state_name}")


def _research_run_rows(request: Request) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for artifact_record in _artifact_registry(request).list():
        row = _artifact_run_schema(artifact_record)
        rows.append(row)
        seen.add(str(row["run_id"]))
    for experiment_record in _experiment_store(request).list_runs():
        row = _experiment_run_schema(experiment_record)
        if str(row["run_id"]) in seen:
            continue
        rows.append(row)
    return tuple(sorted(rows, key=lambda row: str(row["recorded_at"]), reverse=True))


def _experiment_run_schema(record: ExperimentStoreRecord) -> dict[str, Any]:
    return {
        "run_id": record.experiment_id,
        "strategy_name": record.strategy_name,
        "strategy_version": record.strategy_version,
        "idea_id": record.idea_id,
        "recorded_at": record.recorded_at.isoformat(),
        "manifest_path": str(record.manifest_path),
        "dataset_ids": record.dataset_ids,
        "metrics": dict(record.metrics),
        "artifact_hashes": dict(record.artifact_hashes),
    }


def _artifact_run_schema(record: ResearchRunRecord) -> dict[str, Any]:
    manifest = _read_json_object(record.artifact_dir / "resolved_manifest.json")
    metrics = _read_json_object(record.artifact_dir / "metrics.json")
    strategy = _mapping_or_empty(manifest.get("strategy"))
    data = _mapping_or_empty(manifest.get("data"))
    dataset_id = _optional_text(data.get("dataset_id"))
    return {
        "run_id": record.run_id,
        "strategy_name": _optional_text(strategy.get("id")) or record.run_id,
        "strategy_version": _optional_text(strategy.get("entrypoint")) or "unknown",
        "idea_id": _optional_text(strategy.get("idea_id")),
        "recorded_at": record.recorded_at.isoformat(),
        "manifest_path": str(record.artifact_dir / "manifest.yaml"),
        "dataset_ids": (dataset_id,) if dataset_id is not None else (),
        "metrics": _dashboard_metrics(metrics, record),
        "artifact_hashes": {
            "manifest": record.manifest_hash,
            "artifact_dir": str(record.artifact_dir),
        },
    }


def _dashboard_metrics(
    metrics: Mapping[str, Any],
    record: ResearchRunRecord,
) -> dict[str, Any]:
    flattened: dict[str, Any] = {
        "promotion_status": record.promotion_status,
        "status": record.status,
    }
    for group_name, group_value in metrics.items():
        if not isinstance(group_value, Mapping):
            if _is_scalar(group_value):
                flattened[str(group_name)] = group_value
            continue
        for metric_name, metric_value in group_value.items():
            if not _is_scalar(metric_value):
                continue
            key = f"{group_name}.{metric_name}"
            flattened[key] = metric_value
            if metric_name in {"candidate_count", "sharpe", "total_return"}:
                flattened[str(metric_name)] = metric_value
    return flattened


def _matches_run_filter(
    row: Mapping[str, Any],
    *,
    strategy_name: str | None,
    idea_id: str | None,
    status: str | None,
) -> bool:
    if strategy_name and strategy_name.lower() not in str(row["strategy_name"]).lower():
        return False
    if idea_id and row.get("idea_id") != idea_id:
        return False
    metrics = _mapping_or_empty(row.get("metrics"))
    status_values = {
        str(metrics.get("promotion_status", "")).lower(),
        str(metrics.get("status", "")).lower(),
    }
    return not (status and status.lower() not in status_values)


def _report_schema(
    bundle: ResearchEvidenceBundle,
    *,
    include_preview: bool = False,
) -> Any:
    return {
        "evidence_bundle_id": bundle.evidence_bundle_id,
        "workflow_run_id": bundle.workflow_run_id,
        "strategy_id": bundle.strategy_id,
        "idea_id": bundle.idea_id,
        "report_path": bundle.report_path,
        "report_hash": bundle.report_hash,
        "status": bundle.status,
        "promotion_eligibility": bundle.promotion_eligibility,
        "report_preview": _report_preview(bundle.report_path) if include_preview else None,
    }


def _bundle_by_id(request: Request, evidence_bundle_id: str) -> ResearchEvidenceBundle:
    for bundle in _evidence_registry(request).list():
        if bundle.evidence_bundle_id == evidence_bundle_id:
            return bundle
    raise HTTPException(status_code=404, detail="research evidence bundle not found")


def _report_preview(report_path: str | None) -> str | None:
    if report_path is None:
        return None
    path = Path(report_path)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")[:4000]


def _numeric_metric(row: Mapping[str, Any], metric: str) -> float:
    value = _mapping_or_empty(row.get("metrics")).get(metric)
    if not isinstance(value, int | float):
        raise HTTPException(status_code=404, detail=f"numeric metric not found: {metric}")
    return float(value)


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _mapping_or_empty(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def _promotion_candidate_payloads(root: Path) -> tuple[tuple[Path, dict[str, Any]], ...]:
    if not root.exists():
        return ()
    payloads: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((*root.glob("*.yaml"), *root.glob("*.yml"))):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(payload, Mapping):
            payloads.append((path, dict(payload)))
    return tuple(payloads)


def _readiness_payloads(root: Path) -> tuple[tuple[Path, dict[str, Any]], ...]:
    if not root.exists():
        return ()
    payloads: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(root.glob("**/paper_live_gate_decision.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, Mapping):
            payloads.append((path, dict(payload)))
    return tuple(payloads)


def _latest_readiness_by_strategy(root: Path) -> dict[str, str]:
    latest: dict[str, tuple[str, str]] = {}
    for _, payload in _readiness_payloads(root):
        strategy_id = _optional_text(payload.get("strategy_id"))
        if strategy_id is None:
            continue
        decision_date = str(payload.get("decision_date", ""))
        status = str(
            payload.get("target_status", payload.get("paper_live_readiness_gate", "recorded"))
        )
        if strategy_id not in latest or decision_date > latest[strategy_id][0]:
            latest[strategy_id] = (decision_date, status)
    return {strategy_id: item[1] for strategy_id, item in latest.items()}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["router"]
