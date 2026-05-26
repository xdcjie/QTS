"""Research experiment manifest writing."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.reporting.base import PLATFORM_BASELINE_VERSION


@dataclass(frozen=True, slots=True)
class ExperimentManifestConfig:
    """Input required to write a reproducible research experiment manifest."""

    experiment_id: str
    strategy_name: str
    strategy_version: str
    factor_versions: Mapping[str, str]
    dataset_ids: Sequence[str]
    config: Mapping[str, Any]
    artifact_paths: Sequence[Path]
    metrics: Mapping[str, Any]
    idea_id: str | None = None

    def __post_init__(self) -> None:
        self._require_non_empty("experiment_id", self.experiment_id)
        self._require_non_empty("strategy_name", self.strategy_name)
        self._require_non_empty("strategy_version", self.strategy_version)
        if self.idea_id is not None:
            self._require_non_empty("idea_id", self.idea_id)
            object.__setattr__(self, "idea_id", self.idea_id.strip())

    @property
    def config_hash(self) -> str:
        """Return a deterministic hash for the experiment definition."""

        seed: dict[str, Any] = {
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "factor_versions": dict(self.factor_versions),
            "dataset_ids": list(self.dataset_ids),
            "config": self.config,
        }
        if self.idea_id is not None:
            seed["idea_id"] = self.idea_id
        return stable_json_hash(seed)

    @staticmethod
    def _require_non_empty(field_name: str, value: str) -> None:
        if not value.strip():
            raise ValueError(f"{field_name} is required")


@dataclass(frozen=True, slots=True)
class ExperimentManifestResult:
    """Result of writing a research experiment manifest."""

    manifest_path: Path
    payload: Mapping[str, object]


class ExperimentManifestWriter:
    """Write reproducible research experiment manifests."""

    def __init__(self, root_dir: Path = Path("artifacts/research")) -> None:
        self._root_dir = root_dir

    def write_manifest(self, config: ExperimentManifestConfig) -> ExperimentManifestResult:
        """Write `manifest.json` under the experiment artifact directory."""

        artifact_hashes: dict[str, str] = {}
        artifact_paths_by_hash: dict[str, str] = {}
        for artifact_path in config.artifact_paths:
            digest = self._sha256_file(artifact_path)
            artifact_name = artifact_path.name
            if artifact_name in artifact_hashes:
                raise ValueError(f"duplicate artifact name: {artifact_name}")
            artifact_hashes[artifact_name] = digest
            artifact_paths_by_hash[digest] = str(artifact_path)

        payload: dict[str, object] = {
            "experiment_id": config.experiment_id,
            "platform_baseline_version": PLATFORM_BASELINE_VERSION,
            "strategy_name": config.strategy_name,
            "strategy_version": config.strategy_version,
            "factor_versions": dict(config.factor_versions),
            "dataset_ids": list(config.dataset_ids),
            "config_hash": config.config_hash,
            "artifact_hashes": artifact_hashes,
            "artifact_paths_by_hash": artifact_paths_by_hash,
            "metrics": dict(config.metrics),
        }
        if config.idea_id is not None:
            payload["idea_id"] = config.idea_id
        manifest_path = self._root_dir / config.experiment_id / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return ExperimentManifestResult(manifest_path=manifest_path, payload=payload)

    @staticmethod
    def _sha256_file(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as artifact:
            for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                hasher.update(chunk)
        return f"sha256:{hasher.hexdigest()}"


__all__ = [
    "ExperimentManifestConfig",
    "ExperimentManifestResult",
    "ExperimentManifestWriter",
]
