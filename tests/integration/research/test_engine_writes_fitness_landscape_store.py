from __future__ import annotations

from pathlib import Path

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_engine_writes_complete_fitness_landscape_points(tmp_path: Path) -> None:
    _, result = run_engine(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=3,
        max_total_trials=3,
    )

    rows = read_jsonl(result.fitness_landscape_path)
    selected = read_jsonl(result.selected_candidates_path)[0]
    accepted = [row for row in rows if row["accepted"]]
    rejected = [row for row in rows if not row["accepted"]]

    assert len(rows) == 3
    assert rejected
    assert accepted[0]["evidence_bundle_id"] == selected["evidence_bundle_id"]
    assert accepted[0]["promotion_packet_id"] == selected["promotion_candidate_id"]
    assert accepted[0]["evidence_bundle_id"] != accepted[0]["trial_id"]
    assert all(row["point_hash"].startswith("sha256:") for row in rows)
