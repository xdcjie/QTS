from __future__ import annotations

import json
from pathlib import Path

from qts.research.search import TrialBudgetLedger

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_engine_enforces_trial_and_compute_budgets(tmp_path: Path) -> None:
    _, result = run_engine(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=3,
        max_total_trials=3,
        max_family_trials=3,
        compute_budget_limit=2,
    )

    ledger_path = result.output_root / "trial_budget_ledger.jsonl"
    records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    assert [record["payload"]["accepted"] for record in records] == [True, True, False]
    assert "compute budget exceeded" in records[-1]["payload"]["decision_reason"]
    assert TrialBudgetLedger(ledger_path).verify_hash_chain() == ()
    assert len(read_jsonl(result.fitness_landscape_path)) == 2
    budget_rejections = [
        row for row in read_jsonl(result.rejected_candidates_path) if row.get("budget_rejected")
    ]
    assert len(budget_rejections) == 1
    assert budget_rejections[0]["budget_record_id"] == records[-1]["record_id"]
    assert "compute budget exceeded" in budget_rejections[0]["reasons"][0]
