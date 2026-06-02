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

_LAUNCH_PLAN_SCHEME = "launch-plan://"


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

        return f"{_LAUNCH_PLAN_SCHEME}{self._safe_candidate_id()}/{self._hash_suffix()}"

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

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> RuntimeLaunchPlan:
        """Reconstruct a launch plan from a persisted payload."""

        return cls(
            schema_version=int(payload.get("schema_version", 1)),
            promotion_candidate_id=str(payload["promotion_candidate_id"]),
            target_mode=str(payload["target_mode"]),
            strategy_id=str(payload["strategy_id"]),
            source_module=str(payload.get("source_module", "")),
            target_module=str(payload["target_module"]),
            idea_id=str(payload.get("idea_id", "")),
            evidence_bundle_id=str(payload["evidence_bundle_id"]),
            runtime=cast(Mapping[str, Any], payload.get("runtime", {})),
            operations=cast(Mapping[str, Any], payload.get("operations", {})),
            source_packet_hash=(
                str(payload["source_packet_hash"]) if payload.get("source_packet_hash") else None
            ),
        )

    def _safe_candidate_id(self) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", self.promotion_candidate_id.strip())
        return safe.strip("-") or "candidate"

    def _hash_suffix(self) -> str:
        return self.content_hash.removeprefix("sha256:")

    @staticmethod
    def _canonical_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
        """Return a detached, JSON-canonical copy for stable hashing."""

        return cast(dict[str, Any], json.loads(stable_json_dumps(dict(value))))


@dataclass(frozen=True, slots=True)
class RuntimeLaunchPlanResolution:
    """Verified launch-plan resolution evidence used by runtime start."""

    plan: RuntimeLaunchPlan
    path: Path
    config_ref: str
    content_hash: str


class RuntimeLaunchPlanStore:
    """Content-addressed filesystem store for immutable runtime launch plans."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    @property
    def directory(self) -> Path:
        """Return the filesystem root used for launch-plan materialization."""

        return self._directory

    def write(self, plan: RuntimeLaunchPlan) -> RuntimeLaunchPlanResolution:
        """Persist ``plan`` and return verified write evidence."""

        path = plan.write_to(self._directory)
        return RuntimeLaunchPlanResolution(
            plan=plan,
            path=path,
            config_ref=plan.config_ref,
            content_hash=plan.content_hash,
        )

    def resolve(self, config_ref: str, *, expected_hash: str) -> RuntimeLaunchPlanResolution:
        """Resolve and verify a content-addressed launch plan.

        The operator command must provide both the config reference and the
        expected content hash.  A missing file, mismatched ref suffix, or changed
        payload rejects the runtime start before any session can be built.
        """

        candidate_id, ref_hash = self._parse_config_ref(config_ref)
        self._require_hash(expected_hash)
        expected_suffix = expected_hash.removeprefix("sha256:")
        if ref_hash != expected_suffix:
            raise ValueError("launch plan config_ref hash does not match expected_hash")
        path = self._directory / f"{candidate_id}-{ref_hash}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("launch plan payload must be a JSON object")
        plan = RuntimeLaunchPlan.from_payload(cast(dict[str, Any], payload))
        actual_hash = plan.content_hash
        if actual_hash != expected_hash:
            raise ValueError("launch plan hash mismatch")
        if plan.config_ref != config_ref:
            raise ValueError("launch plan config_ref mismatch")
        return RuntimeLaunchPlanResolution(
            plan=plan,
            path=path,
            config_ref=config_ref,
            content_hash=actual_hash,
        )

    @staticmethod
    def _parse_config_ref(config_ref: str) -> tuple[str, str]:
        if not config_ref.startswith(_LAUNCH_PLAN_SCHEME):
            raise ValueError("config_ref must be a launch-plan:// reference")
        remainder = config_ref.removeprefix(_LAUNCH_PLAN_SCHEME)
        parts = remainder.split("/", 1)
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise ValueError("config_ref must identify launch-plan candidate and hash")
        RuntimeLaunchPlanStore._require_hash(f"sha256:{parts[1]}")
        return parts[0], parts[1]

    @staticmethod
    def _require_hash(value: str) -> None:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
            raise ValueError("launch plan hash must be a sha256:<64 hex> value")


__all__ = [
    "RuntimeLaunchPlan",
    "RuntimeLaunchPlanResolution",
    "RuntimeLaunchPlanStore",
]
