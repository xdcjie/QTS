"""Shared reporting contracts.

ReportWriter and RuntimeArtifactWriter describe output boundaries for
persisting runtime results. Mode-specific writers own concrete formats.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from qts.core.hashing import stable_json_hash

RUNTIME_ARTIFACT_SCHEMA_VERSION = "1"
PLATFORM_BASELINE_VERSION = "qts-platform-v1"
NON_BROKER_SOURCE_COMMIT = "not-applicable-backtest"
NON_BROKER_HASH_SENTINEL = "sha256:not-applicable-backtest"
CANONICAL_RUNTIME_MANIFEST_FIELDS = (
    "run_id",
    "runtime_instance_id",
    "runtime_mode",
    "market_data_environment",
    "execution_environment",
    "account_environment",
    "order_submission_permission",
    "config_hash",
    "topology_hash",
    "startup_checklist_hash",
    "event_schema_version",
    "artifact_schema_version",
    "platform_baseline_version",
    "created_at",
    "source_commit",
    "operator_identity_hash",
)


@dataclass(frozen=True, slots=True)
class RuntimeManifest:
    """Shared runtime manifest fields emitted by backtest, paper, and live modes."""

    run_id: str
    runtime_instance_id: str
    runtime_mode: str
    market_data_environment: str
    execution_environment: str
    account_environment: str
    order_submission_permission: bool
    event_schema_version: str
    artifact_schema_version: str
    config_hash: str
    topology_hash: str
    startup_checklist_hash: str
    created_at: datetime
    source_commit: str
    operator_identity_hash: str
    platform_baseline_version: str
    manifest_hash: str
    finalized_at: datetime | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> RuntimeManifest:
        """Validate and normalize a runtime manifest payload."""
        cls.validate_payload(payload)
        topology_hash = payload.get("topology_hash")
        if topology_hash is None:
            runtime_topology = payload.get("runtime_topology")
            if isinstance(runtime_topology, Mapping):
                topology_hash = runtime_topology.get("topology_hash")
        if topology_hash is None:
            raise ValueError("missing required runtime manifest field: topology_hash")
        finalized_at = (
            cls._aware_datetime_from_payload(payload, "finalized_at")
            if "finalized_at" in payload
            else None
        )
        manifest_hash = cls.hash_payload(payload)
        declared_manifest_hash = payload.get("manifest_hash")
        if declared_manifest_hash is not None and str(declared_manifest_hash) != manifest_hash:
            raise ValueError("manifest_hash does not match canonical runtime manifest payload")
        return cls(
            run_id=str(payload["run_id"]),
            runtime_instance_id=str(payload["runtime_instance_id"]),
            runtime_mode=str(payload["runtime_mode"]),
            market_data_environment=str(payload["market_data_environment"]),
            execution_environment=str(payload["execution_environment"]),
            account_environment=str(payload["account_environment"]),
            order_submission_permission=cls._bool_from_payload(
                payload, "order_submission_permission"
            ),
            event_schema_version=str(payload["event_schema_version"]),
            artifact_schema_version=str(payload["artifact_schema_version"]),
            config_hash=str(payload["config_hash"]),
            topology_hash=str(topology_hash),
            startup_checklist_hash=str(payload["startup_checklist_hash"]),
            created_at=cls._aware_datetime_from_payload(payload, "created_at"),
            source_commit=str(payload["source_commit"]),
            operator_identity_hash=str(payload["operator_identity_hash"]),
            platform_baseline_version=str(payload["platform_baseline_version"]),
            manifest_hash=manifest_hash,
            finalized_at=finalized_at,
        )

    def to_payload(self) -> dict[str, object]:
        """Serialize shared manifest fields."""
        payload: dict[str, object] = {
            "run_id": self.run_id,
            "runtime_instance_id": self.runtime_instance_id,
            "runtime_mode": self.runtime_mode,
            "market_data_environment": self.market_data_environment,
            "execution_environment": self.execution_environment,
            "account_environment": self.account_environment,
            "order_submission_permission": self.order_submission_permission,
            "event_schema_version": self.event_schema_version,
            "artifact_schema_version": self.artifact_schema_version,
            "config_hash": self.config_hash,
            "topology_hash": self.topology_hash,
            "startup_checklist_hash": self.startup_checklist_hash,
            "created_at": self.created_at.isoformat(),
            "source_commit": self.source_commit,
            "operator_identity_hash": self.operator_identity_hash,
            "platform_baseline_version": self.platform_baseline_version,
            "manifest_hash": self.manifest_hash,
        }
        if self.finalized_at is not None:
            payload["finalized_at"] = self.finalized_at.isoformat()
        return payload

    @classmethod
    def validate_payload(cls, payload: Mapping[str, object]) -> None:
        """Require the canonical runtime manifest field set."""
        for key in CANONICAL_RUNTIME_MANIFEST_FIELDS:
            cls._require_payload_value(payload, key)
        cls._aware_datetime_from_payload(payload, "created_at")
        cls._bool_from_payload(payload, "order_submission_permission")

    @staticmethod
    def hash_payload(payload: Mapping[str, object]) -> str:
        """Return the deterministic manifest hash, excluding the hash field itself."""
        hash_payload = dict(payload)
        hash_payload.pop("manifest_hash", None)
        return stable_json_hash(hash_payload)

    @staticmethod
    def _aware_datetime_from_payload(payload: Mapping[str, object], key: str) -> datetime:
        value = payload[key]
        if not isinstance(value, str):
            raise TypeError(f"{key} must be an ISO datetime string")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError(f"{key} must be timezone-aware")
        return parsed

    @staticmethod
    def _bool_from_payload(payload: Mapping[str, object], key: str) -> bool:
        value = payload[key]
        if not isinstance(value, bool):
            raise TypeError(f"{key} must be a boolean")
        return value

    @staticmethod
    def _require_payload_value(payload: Mapping[str, object], key: str) -> None:
        if key not in payload:
            raise ValueError(f"missing required runtime manifest field: {key}")
        value = payload[key]
        if value is None or value == "":
            raise ValueError(f"missing required runtime manifest field: {key}")


@dataclass(frozen=True, slots=True)
class RuntimeManifestRecord:
    """Queryable runtime manifest loaded from a manifest artifact path."""

    path: Path
    payload: Mapping[str, object]
    manifest: RuntimeManifest

    @classmethod
    def load(cls, path: Path) -> RuntimeManifestRecord:
        """Load and validate a runtime manifest artifact."""
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("runtime manifest artifact must contain a JSON object")
        manifest = RuntimeManifest.from_payload(payload)
        return cls(path=path, payload=payload, manifest=manifest)

    @property
    def manifest_hash(self) -> str:
        """Return the deterministic canonical manifest hash."""
        return self.manifest.manifest_hash

    def query(self, field: str) -> object:
        """Return a top-level manifest value by canonical field name."""
        if field == "manifest_hash":
            return self.manifest_hash
        if field not in self.payload:
            raise KeyError(field)
        return self.payload[field]


@runtime_checkable
class ReportWriter(Protocol):
    """Boundary for writing and finalizing run-level report manifests."""

    def write_manifest(self, *args: Any, **kwargs: Any) -> object:
        """Write a run manifest."""
        ...

    def finalize(self) -> object:
        """Finalize the report writer."""
        ...


@runtime_checkable
class RuntimeArtifactWriter(Protocol):
    """Boundary for persisting runtime artifact files."""

    def write_event(self, payload: Mapping[str, object]) -> object:
        """Write one runtime event artifact row."""
        ...

    def write_snapshot(self, payload: Mapping[str, object]) -> object:
        """Write one runtime snapshot artifact row."""
        ...

    def write_manifest(self, manifest: RuntimeManifest | Mapping[str, object]) -> object:
        """Write a runtime manifest artifact."""
        ...

    def finalize(self, *args: Any, **kwargs: Any) -> object:
        """Finalize artifact outputs."""
        ...


__all__ = [
    "CANONICAL_RUNTIME_MANIFEST_FIELDS",
    "NON_BROKER_HASH_SENTINEL",
    "NON_BROKER_SOURCE_COMMIT",
    "PLATFORM_BASELINE_VERSION",
    "RUNTIME_ARTIFACT_SCHEMA_VERSION",
    "ReportWriter",
    "RuntimeArtifactWriter",
    "RuntimeManifest",
    "RuntimeManifestRecord",
]
