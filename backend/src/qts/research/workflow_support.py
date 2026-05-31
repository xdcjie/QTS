"""Shared stateless helpers for the research workflow runner and its step modules.

JSON-readiness coercion and materialized replay-cache path resolution extracted from
ResearchWorkflowRunner (QTS-FINAL-011) so step modules and the runner share one home.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qts.research.workflow import ResearchWorkflowConfig


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


__all__ = ["json_ready", "materialized_replay_cache_dir"]
