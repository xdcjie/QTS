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
    rejected = [row for row in rows if not row["accepted"]]

    # WIRING: every trial produces a complete, hash-anchored landscape point with
    # a distinct evidence bundle id. HONESTY: the toy fixture promotes nothing, so
    # every landscape point is honestly marked not-accepted (no faked promotion).
    assert len(rows) == 3
    assert read_jsonl(result.selected_candidates_path) == []
    assert rejected == rows
    assert all(row["evidence_bundle_id"] for row in rows)
    assert all(row["evidence_bundle_id"] != row["trial_id"] for row in rows)
    assert all(row["point_hash"].startswith("sha256:") for row in rows)
    generation_rows = read_jsonl(result.generations[0].landscape_path)
    assert generation_rows == rows
    assert all("parameters" not in row for row in generation_rows)
    assert all(row["parameter_hash"].startswith("sha256:") for row in generation_rows)
