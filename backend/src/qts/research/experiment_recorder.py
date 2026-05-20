"""Notebook-friendly research experiment recording."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any

from qts.research.experiment_manifest import ExperimentManifestConfig, ExperimentManifestWriter
from qts.research.experiment_store import ExperimentStore, ExperimentStoreRecord


@dataclass(frozen=True, slots=True)
class ResearchExperimentRecorderConfig:
    """Input required to record one research experiment."""

    experiment_id: str
    strategy_name: str
    strategy_version: str
    manifest_root: Path
    store: ExperimentStore

    def __post_init__(self) -> None:
        self._require_non_empty("experiment_id", self.experiment_id)
        self._require_non_empty("strategy_name", self.strategy_name)
        self._require_non_empty("strategy_version", self.strategy_version)
        object.__setattr__(self, "experiment_id", self.experiment_id.strip())
        object.__setattr__(self, "strategy_name", self.strategy_name.strip())
        object.__setattr__(self, "strategy_version", self.strategy_version.strip())

    @staticmethod
    def _require_non_empty(field_name: str, value: str) -> None:
        if not value.strip():
            raise ValueError(f"{field_name} is required")


class ResearchExperimentRecorder:
    """Record research evidence as a manifest-backed experiment store entry."""

    def __init__(self, config: ResearchExperimentRecorderConfig) -> None:
        self._config = config
        self._config_payload: dict[str, Any] = {}
        self._metrics: dict[str, Any] = {}
        self._factor_versions: dict[str, str] = {}
        self._dataset_ids: list[str] = []
        self._artifact_paths: list[Path] = []

    def log_params(self, params: Mapping[str, Any]) -> None:
        """Merge experiment parameters into the manifest config payload."""

        self._config_payload.update(params)

    def log_metrics(self, metrics: Mapping[str, Any]) -> None:
        """Merge experiment metrics into the manifest metrics payload."""

        self._metrics.update(metrics)

    def log_metric(self, name: str, value: Any) -> None:
        """Record one experiment metric."""

        if not name.strip():
            raise ValueError("metric name is required")
        self._metrics[name.strip()] = value

    def log_factor_version(self, name: str, version: str) -> None:
        """Record the reviewed factor version used as research evidence."""

        factor_name = name.strip()
        factor_version = version.strip()
        if not factor_name:
            raise ValueError("factor name is required")
        if not factor_version:
            raise ValueError("factor version is required")
        self._factor_versions[factor_name] = factor_version

    def log_dataset_id(self, dataset_id: str) -> None:
        """Record one unique dataset identifier used by the experiment."""

        normalized = dataset_id.strip()
        if not normalized:
            raise ValueError("dataset_id is required")
        if normalized not in self._dataset_ids:
            self._dataset_ids.append(normalized)

    def log_artifact(self, path: Path) -> None:
        """Record an existing experiment artifact path."""

        if not path.exists():
            raise FileNotFoundError(f"experiment artifact not found: {path}")
        self._artifact_paths.append(path)

    def finalize(self, recorded_at: datetime | None = None) -> ExperimentStoreRecord:
        """Write the experiment manifest and index it in the experiment store."""

        writer = ExperimentManifestWriter(self._config.manifest_root)
        result = writer.write_manifest(
            ExperimentManifestConfig(
                experiment_id=self._config.experiment_id,
                strategy_name=self._config.strategy_name,
                strategy_version=self._config.strategy_version,
                factor_versions=self._factor_versions,
                dataset_ids=self._dataset_ids,
                config=self._config_payload,
                artifact_paths=self._artifact_paths,
                metrics=self._metrics,
            )
        )
        return self._config.store.record_manifest(
            result.manifest_path,
            recorded_at=recorded_at,
        )

    def __enter__(self) -> ResearchExperimentRecorder:
        """Return this recorder for context-managed experiment logging."""

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Finalize only successful context-managed experiments."""

        if exc_type is None:
            self.finalize()


__all__ = ["ResearchExperimentRecorder", "ResearchExperimentRecorderConfig"]
