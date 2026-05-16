from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qts.reporting.base import PLATFORM_BASELINE_VERSION
from qts.research import ExperimentManifestConfig, ExperimentManifestWriter


def test_experiment_manifest_contains_strategy_factor_dataset_versions(tmp_path: Path) -> None:
    writer = ExperimentManifestWriter(tmp_path / "artifacts" / "research")

    result = writer.write_manifest(
        ExperimentManifestConfig(
            experiment_id="exp-001",
            strategy_name="mean_reversion",
            strategy_version="2026.05",
            factor_versions={"momentum": "1.0.0", "quality": "2.1.0"},
            dataset_ids=["daily-bars-v3", "fundamentals-v1"],
            config={"lookback": 20, "rebalance": "weekly"},
            artifact_paths=[],
            metrics={"sharpe": 1.25},
        )
    )

    payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert payload["strategy_name"] == "mean_reversion"
    assert payload["strategy_version"] == "2026.05"
    assert payload["factor_versions"] == {"momentum": "1.0.0", "quality": "2.1.0"}
    assert payload["dataset_ids"] == ["daily-bars-v3", "fundamentals-v1"]
    assert payload["metrics"] == {"sharpe": 1.25}


def test_experiment_manifest_contains_platform_baseline_version(tmp_path: Path) -> None:
    writer = ExperimentManifestWriter(tmp_path / "artifacts" / "research")

    result = writer.write_manifest(
        ExperimentManifestConfig(
            experiment_id="exp-baseline",
            strategy_name="breakout",
            strategy_version="1",
            factor_versions={},
            dataset_ids=[],
            config={},
            artifact_paths=[],
            metrics={},
        )
    )

    payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert payload["platform_baseline_version"] == PLATFORM_BASELINE_VERSION


def test_same_experiment_input_produces_same_config_hash(tmp_path: Path) -> None:
    left = ExperimentManifestConfig(
        experiment_id="exp-stable-left",
        strategy_name="carry",
        strategy_version="1",
        factor_versions={"term_structure": "3"},
        dataset_ids=["futures-chain-v2"],
        config={"thresholds": {"entry": 0.7, "exit": 0.2}, "enabled": True},
        artifact_paths=[],
        metrics={"annual_return": 0.12},
    )
    right = ExperimentManifestConfig(
        experiment_id="exp-stable-right",
        strategy_name="carry",
        strategy_version="1",
        factor_versions={"term_structure": "3"},
        dataset_ids=["futures-chain-v2"],
        config={"enabled": True, "thresholds": {"exit": 0.2, "entry": 0.7}},
        artifact_paths=[],
        metrics={"annual_return": 0.12},
    )
    writer = ExperimentManifestWriter(tmp_path / "artifacts" / "research")

    left_result = writer.write_manifest(left)
    right_result = writer.write_manifest(right)

    assert left_result.payload["config_hash"] == right_result.payload["config_hash"]


def test_experiment_artifacts_are_addressable_by_hash(tmp_path: Path) -> None:
    equity_curve = tmp_path / "equity_curve.csv"
    equity_curve.write_text("date,equity\n2026-01-02,100000\n", encoding="utf-8")
    expected_hash = f"sha256:{hashlib.sha256(equity_curve.read_bytes()).hexdigest()}"
    writer = ExperimentManifestWriter(tmp_path / "artifacts" / "research")

    result = writer.write_manifest(
        ExperimentManifestConfig(
            experiment_id="exp-artifacts",
            strategy_name="pairs",
            strategy_version="1",
            factor_versions={},
            dataset_ids=["pairs-dataset-v1"],
            config={"zscore_window": 60},
            artifact_paths=[equity_curve],
            metrics={},
        )
    )

    payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert payload["artifact_hashes"] == {"equity_curve.csv": expected_hash}
    assert payload["artifact_paths_by_hash"] == {expected_hash: str(equity_curve)}
