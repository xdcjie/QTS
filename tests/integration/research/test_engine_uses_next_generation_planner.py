from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)
from qts.research.planner import GenerationApprovalRecord

from tests.integration.research._autonomous_engine_plan_helpers import (
    read_jsonl,
    run_engine,
    write_campaign,
    write_data_paths,
)


def test_engine_uses_next_generation_planner_with_evidence_refs(tmp_path: Path) -> None:
    _, result = run_engine(
        tmp_path,
        families=("momentum", "breakout"),
        max_trials_per_generation=4,
        max_total_trials=4,
    )

    proposal = json.loads(result.next_generation_proposal_path.read_text(encoding="utf-8"))
    assert proposal["proposal_hash"].startswith("sha256:")
    assert proposal["requires_human_approval"] is True
    assert proposal["evidence_refs"]
    assert proposal["mutations"]
    assert all(mutation["reason"] for mutation in proposal["mutations"])
    assert all(mutation["evidence_refs"] for mutation in proposal["mutations"])
    assert proposal["trial_budget_state"]["requested_trials"] <= 4


def test_approved_next_generation_proposal_drives_candidate_generation(
    tmp_path: Path,
) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum", "breakout"),
        max_generations=2,
        max_trials_per_generation=4,
        max_total_trials=8,
    )
    data_paths = write_data_paths(tmp_path)
    blocked = AutonomousResearchEngine(repo_root=Path.cwd()).run(
        AutonomousResearchRun.from_yaml(
            campaign_path,
            data_paths=data_paths,
            output_root=tmp_path / "run",
        )
    )
    proposal = json.loads(blocked.next_generation_proposal_path.read_text(encoding="utf-8"))
    approval = GenerationApprovalRecord(
        proposal_id=str(proposal["proposal_id"]),
        proposal_hash=str(proposal["proposal_hash"]),
        decision="approved",
        reviewer="research-lead",
        decided_at=datetime(2026, 5, 27, tzinfo=UTC),
        reason="proposal feedback reviewed",
        evidence_refs=(str(proposal["proposal_hash"]),),
    )

    approved = AutonomousResearchEngine(repo_root=Path.cwd()).run(
        AutonomousResearchRun.from_yaml(
            campaign_path,
            data_paths=data_paths,
            output_root=tmp_path / "run",
            approval_records=(approval,),
        )
    )

    focus_mutation = next(
        mutation
        for mutation in proposal["mutations"]
        if mutation["mutation_type"] == "search_space"
    )
    best_family = focus_mutation["payload"]["strategy_family"]
    generation_one_rows = read_jsonl(
        approved.output_root / "generation-001" / "candidate_parameters.jsonl"
    )
    assert generation_one_rows[0]["family"] == best_family
    assert all(row["proposal_application"]["applied"] for row in generation_one_rows)
    assert {mutation["mutation_id"] for mutation in proposal["mutations"]} == set(
        generation_one_rows[0]["proposal_application"]["mutation_ids"]
    )
