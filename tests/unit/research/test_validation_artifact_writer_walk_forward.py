from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from qts.research.orchestrator.validation_artifact_writer import ValidationArtifactWriter


@dataclass(frozen=True)
class _RunResult:
    objective_value: str
    manifest_path: Path


def test_walk_forward_validation_verdicts_are_derived_from_train_test_gap(
    tmp_path: Path,
) -> None:
    trial_dir = tmp_path / "trial"
    paths = ValidationArtifactWriter().write(
        trial_dir=trial_dir,
        trial_id="trial-001",
        manifest_hash="sha256:manifest",
        backtest_manifest={
            "manifest_hash": "sha256:base",
            "statistics_hash": "sha256:base-stats",
            "statistics": {"total_return": "0.10", "avg_gross_exposure": "1"},
            "initial_cash": "100000",
        },
        metrics_payload={"objective": "train-test-gap"},
        parameters={},
        pipeline_config={},
        replay_manifest={"manifest_hash": "sha256:replay", "statistics_hash": "sha256:replay"},
        train_result=_RunResult("2.00", tmp_path / "train-manifest.json"),
        train_manifest={"manifest_hash": "sha256:train", "statistics_hash": "sha256:train-stats"},
        test_result=_RunResult("-0.50", tmp_path / "test-manifest.json"),
        test_manifest={"manifest_hash": "sha256:test", "statistics_hash": "sha256:test-stats"},
        failure_result=_RunResult("0", tmp_path / "failure-manifest.json"),
        failure_manifest={"manifest_hash": "sha256:failure"},
        stress_result=_RunResult("0", tmp_path / "stress-manifest.json"),
        stress_manifest={"manifest_hash": "sha256:stress", "initial_cash": "100000"},
        active_correlation_context=(),
    )

    wrapper = json.loads(paths["walk_forward_validation"].read_text(encoding="utf-8"))
    payload = wrapper["payload"]

    assert payload["consistent"] is False
    assert payload["test_windows"][0]["accepted"] is False
    assert payload["test_windows"][0]["score"] == -0.5
    assert payload["max_train_test_gap"] == 2.5
    assert payload["max_allowed_train_test_gap"] == 0.5
