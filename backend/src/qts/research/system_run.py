"""Manifest-driven research-system dry runs."""

from __future__ import annotations

import csv
import hashlib
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.artifact_graph import ResearchArtifactGraphWriter
from qts.research.audit_log import ResearchAuditLog
from qts.research.data_quality import DataQualityArtifact, DataQualityRunner
from qts.research.manifest import ResearchManifestV2, write_jsonl
from qts.research.metrics import ResearchMetrics
from qts.research.promotion import ResearchPromotionPolicy
from qts.research.registry import ResearchRunRegistry, new_record
from qts.research.report import ResearchSystemReport, ResearchSystemReportWriter
from qts.research.reproducibility import ReproducibilitySnapshot, ReproducibilitySnapshotV2
from qts.research.splits import ResearchSplitPlan


@dataclass(frozen=True, slots=True)
class ResearchDryRunResult:
    """Paths produced by a dry-run research-system execution."""

    run_id: str
    artifact_dir: Path
    registry_path: Path
    promotion_status: str

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready run result."""

        return {
            "artifact_dir": str(self.artifact_dir),
            "promotion_status": self.promotion_status,
            "registry_path": str(self.registry_path),
            "run_id": self.run_id,
        }


class ResearchDryRunRunner:
    """Produce complete research-system artifacts without running backtests."""

    def __init__(self, *, repo_root: Path) -> None:
        self._repo_root = repo_root

    def run(self, config_path: Path, *, argv: Sequence[str]) -> ResearchDryRunResult:
        """Run the manifest-driven dry-run path."""

        manifest = _load_manifest(config_path)
        artifact_dir = manifest.output_root / manifest.run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        manifest_copy = artifact_dir / "manifest.yaml"
        shutil.copyfile(config_path, manifest_copy)

        candidates = manifest.candidates()
        resolved_manifest = manifest.to_payload()
        reproducibility = ReproducibilitySnapshot.collect(
            repo_root=self._repo_root,
            manifest_hash=manifest.manifest_hash,
        )
        metrics = ResearchMetrics.dry_run(candidate_count=len(candidates))
        policy = ResearchPromotionPolicy.from_yaml(manifest.promotion_config)
        promotion_decision = policy.evaluate(
            run_id=manifest.run_id,
            strategy_id=manifest.strategy_id,
            metrics=metrics.to_payload(),
            reproducibility=reproducibility.to_payload(),
        )
        split_plan = ResearchSplitPlan.from_config(manifest.split_config)
        data_snapshot = self._data_snapshot(manifest)
        data_quality_artifact = self._data_quality_artifact(manifest, data_snapshot)
        data_quality_payload = _data_quality_payload_with_hash(data_quality_artifact)
        reproducibility_v2 = ReproducibilitySnapshotV2.collect(
            repo_root=self._repo_root,
            manifest_hash=manifest.manifest_hash,
            dependency_hashes=self._dependency_hashes(),
            config_hashes=self._config_hashes(
                manifest=manifest,
                config_path=config_path,
                resolved_manifest=resolved_manifest,
            ),
            data_hashes=self._data_hashes(data_snapshot),
            command_argv=tuple(argv),
            random_seeds=self._random_seeds(manifest),
            calendar_version=getattr(manifest, "calendar", "unknown"),
        )

        _write_json(artifact_dir / "resolved_manifest.json", resolved_manifest)
        _write_json(artifact_dir / "reproducibility.json", reproducibility.to_payload())
        _write_json(artifact_dir / "reproducibility_v2.json", reproducibility_v2.to_payload())
        _write_json(artifact_dir / "metrics.json", metrics.to_payload())
        _write_json(artifact_dir / "promotion_decision.json", promotion_decision.to_payload())
        _write_json(artifact_dir / "data_snapshot.json", data_snapshot)
        _write_json(artifact_dir / "data_quality.json", data_quality_payload)
        _write_json(artifact_dir / "splits.json", split_plan.to_payload())
        ResearchArtifactGraphWriter(artifact_dir).write_dry_run_artifacts(
            artifact_dir=artifact_dir,
            manifest_path=manifest_copy,
            resolved_manifest=resolved_manifest,
            metrics_payload=metrics.to_payload(),
            data_quality_payload=data_quality_payload,
            reproducibility_payload=reproducibility_v2.to_payload(),
            audit_log=ResearchAuditLog(artifact_dir),
        )

        write_jsonl(
            artifact_dir / "candidate_parameters.jsonl",
            [candidate.to_payload() for candidate in candidates],
        )
        write_jsonl(
            artifact_dir / "candidate_results.jsonl",
            [
                {
                    "candidate_id": candidate.candidate_id,
                    "metrics": {},
                    "parameters": dict(candidate.parameters),
                    "search_type": candidate.search_type,
                    "status": "dry_run_not_evaluated",
                }
                for candidate in candidates
            ],
        )
        write_jsonl(artifact_dir / "failures.jsonl", ())
        _write_ranking(artifact_dir / "ranking.csv", candidates)
        write_jsonl(
            artifact_dir / "command_log.jsonl",
            [
                {
                    "argv": list(argv),
                    "command": "run_research",
                    "mode": "dry_run",
                }
            ],
        )
        ResearchSystemReportWriter().write(
            artifact_dir / "report.md",
            ResearchSystemReport(
                manifest=resolved_manifest,
                metrics=metrics.to_payload(),
                promotion_decision=promotion_decision.to_payload(),
                reproducibility=reproducibility.to_payload(),
            ),
        )

        registry = ResearchRunRegistry.from_root(manifest.output_root)
        registry.append(
            new_record(
                run_id=manifest.run_id,
                manifest_hash=manifest.manifest_hash,
                artifact_dir=artifact_dir,
                status="dry_run",
                promotion_status=promotion_decision.status,
            )
        )
        return ResearchDryRunResult(
            run_id=manifest.run_id,
            artifact_dir=artifact_dir,
            registry_path=registry.index_path,
            promotion_status=promotion_decision.status,
        )

    def _data_snapshot(self, manifest: ResearchManifestV2) -> dict[str, Any]:
        data_config_hash = _file_sha256(manifest.data_config)
        strategy_config_hash = _file_sha256(manifest.default_config)
        dataset_files = self._dataset_files(manifest)
        return {
            "catalog": manifest.catalog,
            "data_config": str(manifest.data_config),
            "data_config_sha256": data_config_hash,
            "dataset_files": dataset_files,
            "dataset_id": manifest.dataset_id,
            "freeze_rule": "dataset files and split windows are recorded before metrics",
            "roots": list(manifest.roots),
            "strategy_config": str(manifest.default_config),
            "strategy_config_sha256": strategy_config_hash,
            "timeframe": manifest.timeframe,
        }

    def _dataset_files(self, manifest: ResearchManifestV2) -> list[dict[str, Any]]:
        payload = yaml.safe_load(manifest.data_config.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return []
        historical_data = payload.get("historical_data")
        if not isinstance(historical_data, dict):
            return []
        stores = historical_data.get("stores")
        catalogs = historical_data.get("catalogs")
        if not isinstance(stores, dict) or not isinstance(catalogs, dict):
            return []
        catalog = catalogs.get(manifest.catalog)
        if not isinstance(catalog, dict):
            return []
        store_name = catalog.get("store")
        store = stores.get(store_name)
        datasets = catalog.get("datasets")
        if not isinstance(store, dict) or not isinstance(datasets, dict):
            return []
        root_dir = Path(str(store.get("root_dir", "")))
        bars_dir = str(store.get("bars_dir", "data"))
        result: list[dict[str, Any]] = []
        for root in manifest.roots:
            dataset = datasets.get(root)
            if not isinstance(dataset, dict):
                result.append({"exists": False, "root": root, "reason": "dataset missing"})
                continue
            for bar in dataset.get("bars", []):
                if not isinstance(bar, dict):
                    continue
                path = root_dir / bars_dir / str(bar.get("file", ""))
                result.append(
                    {
                        "exists": path.exists(),
                        "path": str(path),
                        "root": root,
                        "sha256": _file_sha256(path) if path.exists() else None,
                        "timeframe": str(bar.get("timeframe", "")),
                    }
                )
        return result

    def _data_quality_artifact(
        self,
        manifest: ResearchManifestV2,
        data_snapshot: Mapping[str, Any],
    ) -> DataQualityArtifact:
        return DataQualityRunner(
            dataset_id=manifest.dataset_id,
            timeframe=manifest.timeframe,
            start=manifest.start,
            end=manifest.end,
            calendar=getattr(manifest, "calendar", None),
        ).run(data_snapshot)

    def _dependency_hashes(self) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for name in ("pyproject.toml", "uv.lock"):
            digest = _file_sha256(self._repo_root / name)
            if digest is not None:
                hashes[name] = digest
        return hashes

    @staticmethod
    def _config_hashes(
        *,
        manifest: ResearchManifestV2,
        config_path: Path,
        resolved_manifest: Mapping[str, Any],
    ) -> dict[str, str]:
        hashes = {"resolved_manifest": stable_json_hash(resolved_manifest)}
        for path in (
            config_path,
            manifest.data_config,
            manifest.default_config,
            manifest.promotion_config,
        ):
            digest = _file_sha256(path)
            hashes[str(path)] = digest or "unknown"
        return hashes

    @staticmethod
    def _data_hashes(data_snapshot: Mapping[str, Any]) -> dict[str, str]:
        result: dict[str, str] = {}
        for row in data_snapshot.get("dataset_files", ()):
            if not isinstance(row, Mapping):
                continue
            path = row.get("path")
            digest = row.get("sha256")
            if isinstance(path, str):
                result[path] = digest if isinstance(digest, str) and digest else "unknown"
        if not result:
            dataset_id = data_snapshot.get("dataset_id", "dataset")
            result[f"dataset:{dataset_id}"] = "unknown"
        return result

    @staticmethod
    def _random_seeds(manifest: ResearchManifestV2) -> dict[str, int]:
        seed = manifest.random_search.get("seed")
        if isinstance(seed, int):
            return {"research_manifest_random_search": seed}
        return {}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _data_quality_payload_with_hash(artifact: DataQualityArtifact) -> dict[str, Any]:
    payload = artifact.to_payload(include_artifact_hash=False)
    return artifact.to_payload(
        include_artifact_hash=True,
        artifact_hash=stable_json_hash(payload),
    )


def _write_ranking(path: Path, candidates: tuple[Any, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("rank", "candidate_id", "search_type", "objective_value", "status"),
        )
        writer.writeheader()
        for rank, candidate in enumerate(candidates, start=1):
            writer.writerow(
                {
                    "candidate_id": candidate.candidate_id,
                    "objective_value": "",
                    "rank": rank,
                    "search_type": candidate.search_type,
                    "status": "dry_run_not_evaluated",
                }
            )


def _load_manifest(path: Path) -> ResearchManifestV2:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping) and payload.get("schema_version") == 2:
        return ResearchManifestV2.from_yaml(path)
    raise ValueError("Research OS v1.0 requires schema_version=2")


__all__ = ["ResearchDryRunResult", "ResearchDryRunRunner"]
