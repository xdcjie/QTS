"""Shared reporting contracts.

ReportWriter and RuntimeArtifactWriter describe output boundaries for
persisting runtime results. Mode-specific writers own concrete formats.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

RUNTIME_ARTIFACT_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class RuntimeManifest:
    """Shared runtime manifest fields emitted by backtest, paper, and live modes."""

    run_id: str
    runtime_mode: str
    event_schema_version: str
    artifact_schema_version: str
    config_hash: str
    topology_hash: str | None
    created_at: datetime
    finalized_at: datetime

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> RuntimeManifest:
        """Validate and normalize a runtime manifest payload."""
        topology_hash = payload.get("topology_hash")
        if topology_hash is None:
            runtime_topology = payload.get("runtime_topology")
            if isinstance(runtime_topology, Mapping):
                topology_hash = runtime_topology.get("topology_hash")
        return cls(
            run_id=str(payload["run_id"]),
            runtime_mode=str(payload["runtime_mode"]),
            event_schema_version=str(payload["event_schema_version"]),
            artifact_schema_version=str(payload["artifact_schema_version"]),
            config_hash=str(payload["config_hash"]),
            topology_hash=str(topology_hash) if topology_hash is not None else None,
            created_at=cls._aware_datetime_from_payload(payload, "created_at"),
            finalized_at=cls._aware_datetime_from_payload(payload, "finalized_at"),
        )

    def to_payload(self) -> dict[str, object]:
        """Serialize shared manifest fields."""
        return {
            "run_id": self.run_id,
            "runtime_mode": self.runtime_mode,
            "event_schema_version": self.event_schema_version,
            "artifact_schema_version": self.artifact_schema_version,
            "config_hash": self.config_hash,
            "topology_hash": self.topology_hash,
            "created_at": self.created_at.isoformat(),
            "finalized_at": self.finalized_at.isoformat(),
        }

    @staticmethod
    def _aware_datetime_from_payload(payload: Mapping[str, object], key: str) -> datetime:
        value = payload[key]
        if not isinstance(value, str):
            raise TypeError(f"{key} must be an ISO datetime string")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError(f"{key} must be timezone-aware")
        return parsed


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
    "RUNTIME_ARTIFACT_SCHEMA_VERSION",
    "ReportWriter",
    "RuntimeArtifactWriter",
    "RuntimeManifest",
]
