from __future__ import annotations

import json
from pathlib import Path

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_engine_trials_derive_metrics_from_backtest_pipeline_artifacts(
    tmp_path: Path,
) -> None:
    _, result = run_engine(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=2,
        max_total_trials=2,
    )

    generation = result.generations[0]
    trial = generation.experiment_result.trials[0]
    metrics = json.loads(trial.metrics_path.read_text(encoding="utf-8"))
    manifest = json.loads(trial.manifest_path.read_text(encoding="utf-8"))

    # WIRING: trial metrics are derived from the real backtest pipeline artifacts
    # (not a synthetic stub), and the manifest hashes anchor those artifacts.
    assert metrics["research"]["metrics_source"] == "backtest_pipeline"
    assert metrics["backtest"]["manifest_hash"] == trial.manifest_hash
    assert Path(metrics["backtest"]["manifest_path"]).exists()
    assert manifest["backtest_manifest_hash"] == trial.manifest_hash
    assert manifest["artifact_hashes"]["backtest_manifest"].startswith("sha256:")

    # HONESTY: the toy fixture promotes nothing, so the campaign carries no
    # selected candidate; the rejected candidate still records the same
    # backtest-pipeline metrics source rather than faking promotion.
    assert read_jsonl(result.selected_candidates_path) == []
    rejected = read_jsonl(result.rejected_candidates_path)
    assert rejected
    assert all(
        row.get("metrics", {}).get("research", {}).get("metrics_source") == "backtest_pipeline"
        for row in rejected
        if row.get("metrics")
    )
