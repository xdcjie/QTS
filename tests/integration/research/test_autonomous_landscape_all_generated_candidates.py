from __future__ import annotations

from pathlib import Path

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_landscape_records_all_generated_candidates_including_budget_rejections(
    tmp_path: Path,
) -> None:
    _campaign_path, result = run_engine(
        tmp_path,
        max_trials_per_generation=3,
        max_total_trials=6,
        compute_budget_limit=1,
    )

    selected = read_jsonl(result.selected_candidates_path)
    rejected = read_jsonl(result.rejected_candidates_path)
    landscape = read_jsonl(result.fitness_landscape_path)

    assert len(landscape) == len(selected) + len(rejected)
    assert any(row["lifecycle_status"] == "budget_rejected" for row in landscape)
    assert all(row["lifecycle_status"] for row in landscape)
