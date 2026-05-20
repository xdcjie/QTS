"""Deterministic research experiment index."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qts.core.time import require_aware_datetime


@dataclass(frozen=True, slots=True)
class ExperimentStoreRecord:
    """One indexed research experiment manifest."""

    experiment_id: str
    manifest_path: Path
    recorded_at: datetime
    platform_baseline_version: str
    strategy_name: str
    strategy_version: str
    factor_versions: Mapping[str, str]
    dataset_ids: tuple[str, ...]
    config_hash: str
    artifact_hashes: Mapping[str, str]
    metrics: Mapping[str, Any]

    @classmethod
    def from_manifest(
        cls,
        manifest_path: Path,
        *,
        recorded_at: datetime,
    ) -> ExperimentStoreRecord:
        """Create a store record from a deterministic experiment manifest."""

        if not manifest_path.exists():
            raise FileNotFoundError(f"experiment manifest not found: {manifest_path}")
        require_aware_datetime(recorded_at, name="recorded_at")
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("experiment manifest must contain a JSON object")
        return cls(
            experiment_id=cls._required_text(payload, "experiment_id"),
            manifest_path=manifest_path,
            recorded_at=recorded_at,
            platform_baseline_version=cls._required_text(payload, "platform_baseline_version"),
            strategy_name=cls._required_text(payload, "strategy_name"),
            strategy_version=cls._required_text(payload, "strategy_version"),
            factor_versions=cls._string_mapping(payload, "factor_versions"),
            dataset_ids=cls._string_tuple(payload, "dataset_ids"),
            config_hash=cls._required_text(payload, "config_hash"),
            artifact_hashes=cls._string_mapping(payload, "artifact_hashes"),
            metrics=cls._mapping(payload, "metrics"),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ExperimentStoreRecord:
        """Rehydrate one record from the store index payload."""

        recorded_at = datetime.fromisoformat(cls._required_text(payload, "recorded_at"))
        require_aware_datetime(recorded_at, name="recorded_at")
        return cls(
            experiment_id=cls._required_text(payload, "experiment_id"),
            manifest_path=Path(cls._required_text(payload, "manifest_path")),
            recorded_at=recorded_at,
            platform_baseline_version=cls._required_text(payload, "platform_baseline_version"),
            strategy_name=cls._required_text(payload, "strategy_name"),
            strategy_version=cls._required_text(payload, "strategy_version"),
            factor_versions=cls._string_mapping(payload, "factor_versions"),
            dataset_ids=cls._string_tuple(payload, "dataset_ids"),
            config_hash=cls._required_text(payload, "config_hash"),
            artifact_hashes=cls._string_mapping(payload, "artifact_hashes"),
            metrics=cls._mapping(payload, "metrics"),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready record payload."""

        return {
            "artifact_hashes": dict(self.artifact_hashes),
            "config_hash": self.config_hash,
            "dataset_ids": list(self.dataset_ids),
            "experiment_id": self.experiment_id,
            "factor_versions": dict(self.factor_versions),
            "manifest_path": str(self.manifest_path),
            "metrics": dict(self.metrics),
            "platform_baseline_version": self.platform_baseline_version,
            "recorded_at": self.recorded_at.isoformat(),
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
        }

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} is required")
        return value

    @staticmethod
    def _mapping(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
        value = payload.get(field_name)
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a JSON object")
        return dict(value)

    @classmethod
    def _string_mapping(cls, payload: Mapping[str, Any], field_name: str) -> dict[str, str]:
        value = cls._mapping(payload, field_name)
        result: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, str):
                raise ValueError(f"{field_name} must contain string keys and values")
            result[key] = item
        return result

    @staticmethod
    def _string_tuple(payload: Mapping[str, Any], field_name: str) -> tuple[str, ...]:
        value = payload.get(field_name)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"{field_name} must be a JSON string list")
        return tuple(value)


class ExperimentStore:
    """Owns a deterministic JSONL index of research experiment manifests."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    @property
    def index_path(self) -> Path:
        """Return the JSONL index path used by this store."""

        return self._root_dir / "experiments.jsonl"

    def record_manifest(
        self,
        manifest_path: Path,
        *,
        recorded_at: datetime | None = None,
    ) -> ExperimentStoreRecord:
        """Index an experiment manifest and return the stored record."""

        record = ExperimentStoreRecord.from_manifest(
            manifest_path,
            recorded_at=datetime.now(UTC) if recorded_at is None else recorded_at,
        )
        by_experiment_id = {item.experiment_id: item for item in self.list_runs()}
        by_experiment_id[record.experiment_id] = record
        self._write_records(tuple(by_experiment_id.values()))
        return record

    def list_runs(self, *, limit: int | None = None) -> tuple[ExperimentStoreRecord, ...]:
        """Return indexed experiment records, newest first."""

        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")
        if not self.index_path.exists():
            return ()
        records: list[ExperimentStoreRecord] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("experiment store index row must be a JSON object")
            records.append(ExperimentStoreRecord.from_payload(payload))
        sorted_records = self._sort_records(tuple(records))
        if limit is None:
            return sorted_records
        return sorted_records[:limit]

    def _write_records(self, records: tuple[ExperimentStoreRecord, ...]) -> None:
        self._root_dir.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(record.to_payload(), sort_keys=True)
            for record in self._sort_records(records)
        ]
        self.index_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    @staticmethod
    def _sort_records(
        records: tuple[ExperimentStoreRecord, ...],
    ) -> tuple[ExperimentStoreRecord, ...]:
        by_id = sorted(records, key=lambda record: record.experiment_id)
        return tuple(sorted(by_id, key=lambda record: record.recorded_at, reverse=True))


__all__ = ["ExperimentStore", "ExperimentStoreRecord"]
