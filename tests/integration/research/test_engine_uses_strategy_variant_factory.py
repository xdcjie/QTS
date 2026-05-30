from __future__ import annotations

import json
from pathlib import Path

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_engine_records_strategy_variant_hash_for_every_candidate(tmp_path: Path) -> None:
    # WIRING: the strategy-variant factory produces a hashed strategy_variant.json
    # for each trial and the candidate row records the matching id/hash.
    # HONESTY: the toy fixture promotes nothing, so the wiring is asserted against
    # a rejected candidate (the artifact-graph promotion sub-chain, which only
    # exists for promoted candidates, is intentionally absent).
    _, result = run_engine(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=3,
        max_total_trials=3,
    )

    assert read_jsonl(result.selected_candidates_path) == []
    candidate = read_jsonl(result.rejected_candidates_path)[0]
    strategy_variant_path = (
        result.generations[0].experiment_result.output_dir
        / "trials"
        / candidate["trial_id"]
        / "strategy_variant.json"
    )
    strategy_variant_payload = json.loads(strategy_variant_path.read_text(encoding="utf-8"))

    assert strategy_variant_payload["strategy_variant_id"] == candidate["strategy_variant_id"]
    assert strategy_variant_payload["strategy_variant_hash"] == candidate["strategy_variant_hash"]
    assert strategy_variant_payload["factor_hash"].startswith("sha256:")
    assert strategy_variant_payload["manifest_patch_hash"].startswith("sha256:")
    assert strategy_variant_payload["template_id"] == "momentum_template"
