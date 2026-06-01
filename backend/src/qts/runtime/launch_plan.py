"""Immutable runtime launch plans.

A launch plan is the runtime-facing artifact produced after promotion review.
It is content-addressed and contains the exact runtime/operations payload that
operator commands reference when starting paper or live sessions.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from qts.core.hashing import stable_json_dumps, stable_json_hash


@dataclass(frozen=True, slots=True)
class RuntimeLaunchPlan:
    """Content-addressed launch configuration for a runtime start command."""

    promotion_candidate_id: str
    target_mode: str
    strategy_id: str
    source_module: str
    target_module: str
    idea_id: str
    evidence_bundle_id: str
    runtime: Mapping[str, Any] = field(default_factory=dict)
    operations: Mapping[str, Any] = field(default_factory=dict)
    source_packet_hash: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        required_values = {
            "promotion_candidate_id": self.promotion_candidate_id,
            "target_mode": self.target_mode,
            "strategy_id": self.strategy_id,
            "target_module": self.target_module,
            "evidence_bundle_id": self.evidence_bundle_id,
        }
        for field_name, value in required_values.items():
            if not str(value).strip():
                raise ValueError(f"{field_name} is required for RuntimeLaunchPlan")
        object.__setattr__(self, "runtime", self._canonical_mapping(self.runtime))
        object.__setattr__(self, "operations", self._canonical_mapping(self.operations))

    @property
    def content_hash(self) -> str:
        """Return the stable hash of the launch plan payload."""

        return stable_json_hash(self.to_payload())

    @property
    def config_ref(self) -> str:
        """Return the operator-facing content-addressed config reference."""

        return f"launch-plan://{self._safe_candidate_id()}/{self._hash_suffix()}"

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready launch plan payload."""

        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "promotion_candidate_id": self.promotion_candidate_id,
            "target_mode": self.target_mode,
            "strategy_id": self.strategy_id,
            "source_module": self.source_module,
            "target_module": self.target_module,
            "idea_id": self.idea_id,
            "evidence_bundle_id": self.evidence_bundle_id,
            "runtime": dict(self.runtime),
            "operations": dict(self.operations),
        }
        if self.source_packet_hash is not None:
            payload["source_packet_hash"] = self.source_packet_hash
        return payload

    def write_to(self, directory: Path) -> Path:
        """Materialize the launch plan under ``directory`` and return its path."""

        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self._safe_candidate_id()}-{self._hash_suffix()}.json"
        path.write_text(stable_json_dumps(self.to_payload()) + "\n", encoding="utf-8")
        return path

    def _safe_candidate_id(self) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", self.promotion_candidate_id.strip())
        return safe.strip("-") or "candidate"

    def _hash_suffix(self) -> str:
        return self.content_hash.removeprefix("sha256:")

    @staticmethod
    def _canonical_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
        """Return a detached, JSON-canonical copy for stable hashing."""

        return cast(dict[str, Any], json.loads(stable_json_dumps(dict(value))))


__all__ = ["RuntimeLaunchPlan"]
