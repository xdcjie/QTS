from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.research import ExperimentManifestConfig, ExperimentManifestWriter, ExperimentStore


def _write_manifest(
    tmp_path: Path,
    *,
    experiment_id: str,
    strategy_name: str = "mean_reversion",
    metrics: dict[str, object] | None = None,
) -> Path:
    writer = ExperimentManifestWriter(tmp_path / "artifacts" / "research")
    result = writer.write_manifest(
        ExperimentManifestConfig(
            experiment_id=experiment_id,
            strategy_name=strategy_name,
            strategy_version="1",
            factor_versions={"momentum": "1"},
            dataset_ids=["daily-bars-v1"],
            config={"lookback": 20},
            artifact_paths=[],
            metrics={} if metrics is None else metrics,
        )
    )
    return result.manifest_path


def test_experiment_store_records_manifest_in_deterministic_jsonl(tmp_path: Path) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        experiment_id="exp-001",
        metrics={"sharpe_ratio": "1.25"},
    )
    store = ExperimentStore(tmp_path / "research-index")

    record = store.record_manifest(
        manifest_path,
        recorded_at=datetime(2026, 5, 20, 12, 30, tzinfo=UTC),
    )

    assert record.experiment_id == "exp-001"
    assert record.strategy_name == "mean_reversion"
    assert record.dataset_ids == ("daily-bars-v1",)
    assert record.factor_versions == {"momentum": "1"}
    assert record.metrics == {"sharpe_ratio": "1.25"}
    payloads = [
        json.loads(line) for line in store.index_path.read_text(encoding="utf-8").splitlines()
    ]
    assert payloads == [
        {
            "artifact_hashes": {},
            "config_hash": record.config_hash,
            "dataset_ids": ["daily-bars-v1"],
            "experiment_id": "exp-001",
            "factor_versions": {"momentum": "1"},
            "manifest_path": str(manifest_path),
            "metrics": {"sharpe_ratio": "1.25"},
            "platform_baseline_version": record.platform_baseline_version,
            "recorded_at": "2026-05-20T12:30:00+00:00",
            "strategy_name": "mean_reversion",
            "strategy_version": "1",
        }
    ]


def test_experiment_store_lists_most_recent_records_first(tmp_path: Path) -> None:
    store = ExperimentStore(tmp_path / "research-index")
    older = _write_manifest(tmp_path, experiment_id="exp-old", strategy_name="older")
    newer = _write_manifest(tmp_path, experiment_id="exp-new", strategy_name="newer")

    store.record_manifest(older, recorded_at=datetime(2026, 5, 19, tzinfo=UTC))
    store.record_manifest(newer, recorded_at=datetime(2026, 5, 20, tzinfo=UTC))

    records = store.list_runs()

    assert [record.experiment_id for record in records] == ["exp-new", "exp-old"]
    assert [record.experiment_id for record in store.list_runs(limit=1)] == ["exp-new"]


def test_experiment_store_replaces_existing_experiment_id(tmp_path: Path) -> None:
    store = ExperimentStore(tmp_path / "research-index")
    first = _write_manifest(
        tmp_path,
        experiment_id="exp-001",
        strategy_name="first",
        metrics={"total_return": "0.01"},
    )
    replacement = _write_manifest(
        tmp_path,
        experiment_id="exp-001",
        strategy_name="replacement",
        metrics={"total_return": "0.02"},
    )

    store.record_manifest(first, recorded_at=datetime(2026, 5, 19, tzinfo=UTC))
    record = store.record_manifest(
        replacement,
        recorded_at=datetime(2026, 5, 20, tzinfo=UTC),
    )

    records = store.list_runs()
    assert records == (record,)
    assert records[0].strategy_name == "replacement"
    assert records[0].metrics == {"total_return": "0.02"}


def test_experiment_store_rejects_missing_manifest_path(tmp_path: Path) -> None:
    store = ExperimentStore(tmp_path / "research-index")

    with pytest.raises(FileNotFoundError, match="experiment manifest not found"):
        store.record_manifest(tmp_path / "missing" / "manifest.json")
