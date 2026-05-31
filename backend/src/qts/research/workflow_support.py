"""Shared stateless helpers and value types for the research workflow.

JSON coercion, replay-cache path resolution, the step-result record, period-role
constants, and payload-parsing helpers shared by ResearchWorkflowRunner, its step
modules, and the workflow config/route parsers (QTS-FINAL-011).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from qts.research.report import (
    ResearchReviewDecision,
)

if TYPE_CHECKING:
    from qts.research.workflow import ResearchWorkflowConfig

_FILENAME_SAFE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
_SCORING_PERIOD_ROLES = frozenset({"anchor", "selection", "validation"})
_REPORT_ONLY_PERIOD_ROLES = frozenset({"holdout_report_only", "true_oos_report_only"})
_PERIOD_ROLES = _SCORING_PERIOD_ROLES | _REPORT_ONLY_PERIOD_ROLES


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    to_payload = getattr(value, "to_payload", None)
    if callable(to_payload):
        return json_ready(to_payload())
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [json_ready(item) for item in value]
    return value


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
            "outputs": json_ready(self.outputs),
            "status": self.status,
        }


def materialized_replay_cache_dir(
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


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _snapshot_protocol_payload(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "available_at",
        "forward_return_end",
        "forward_return_start",
        "source_data_end",
    )
    return {field: json_ready(snapshot[field]) for field in fields if field in snapshot}


def _review_decision_from_payload(value: Any) -> ResearchReviewDecision | None:
    if value is None:
        return None
    if isinstance(value, ResearchReviewDecision):
        return value
    if not isinstance(value, Mapping):
        raise ValueError("research_report.decision must be a mapping")
    return ResearchReviewDecision(
        status=str(value.get("status", "keep_researching")),
        reviewer=None if value.get("reviewer") is None else str(value["reviewer"]),
        reason=_string_or_sequence_tuple(value.get("reason", ()), field_name="decision.reason"),
        required_next_evidence=_string_or_sequence_tuple(
            value.get("required_next_evidence", ()),
            field_name="decision.required_next_evidence",
        ),
        evidence_bundle_id=(
            None if value.get("evidence_bundle_id") is None else str(value["evidence_bundle_id"])
        ),
        trade_diagnostics_available=bool(value.get("trade_diagnostics_available", False)),
        validation_scorecard_available=bool(value.get("validation_scorecard_available", False)),
        cost_stress_available=bool(value.get("cost_stress_available", False)),
    )


def _string_or_sequence_tuple(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return () if not text else (text,)
    if not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a string or sequence")
    return tuple(str(item) for item in value)


def _string_sequence(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field_name} must be a sequence")
    return tuple(str(item) for item in value)


__all__ = [
    "_FILENAME_SAFE_CHARS",
    "_PERIOD_ROLES",
    "_REPORT_ONLY_PERIOD_ROLES",
    "_SCORING_PERIOD_ROLES",
    "ResearchWorkflowStepResult",
    "_load_json_mapping",
    "_required_text",
    "_review_decision_from_payload",
    "_snapshot_protocol_payload",
    "_string_or_sequence_tuple",
    "_string_sequence",
    "json_ready",
    "materialized_replay_cache_dir",
]
