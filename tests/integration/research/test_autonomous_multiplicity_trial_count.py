"""Integration: the autonomous engine records the real generated trial count.

The multiplicity correction must be computed against the number of configurations
actually tried in the generation, and that count must be serialized on the
generation's ``selection_result.json`` so the haircut is auditable. This drives the
real engine over a generation of candidates and asserts the recorded
``trial_count`` equals the number of generated candidates passed to the selector
(one selector input per configuration tried), at ``generation`` scope.
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_selection_result_trial_count_equals_generated_candidate_count(
    tmp_path: Path,
) -> None:
    _campaign_path, result = run_engine(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=4,
        max_total_trials=4,
    )

    selection_dir = result.output_root / "generation-000" / "selection"
    candidate_results = read_jsonl(selection_dir / "candidate_results.jsonl")
    generated_count = len(candidate_results)
    assert generated_count >= 1

    selection_result = json.loads(
        (selection_dir / "selection_result.json").read_text(encoding="utf-8")
    )

    # The recorded trial count is the cardinality of the generated candidates the
    # selector saw this generation -- the real N, not the default of 1.
    assert selection_result["trial_count"] == generated_count
    assert selection_result["multiplicity_scope"] == "generation"
    assert selection_result["false_discovery_rate"] is not None

    # Every per-candidate adjustment was computed against the same campaign-level N.
    for candidate in (
        selection_result["selected_candidates"] + selection_result["rejected_candidates"]
    ):
        adjustment = candidate.get("multiplicity_adjustment")
        if adjustment is not None:
            assert adjustment["trial_count"] == generated_count
