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
    write_campaign,
    write_data_paths,
)


def test_engine_requires_approved_generation_record_before_generation_one(
    tmp_path: Path,
) -> None:
    campaign_path = write_campaign(
        tmp_path,
        max_generations=2,
        max_trials_per_generation=2,
        max_total_trials=4,
    )
    data_paths = write_data_paths(tmp_path)
    base_run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=data_paths,
        output_root=tmp_path / "run",
    )

    blocked = AutonomousResearchEngine(repo_root=Path.cwd()).run(base_run)
    assert blocked.status == "pending_human_approval"
    assert not (blocked.output_root / "generation-001").exists()

    proposal = json.loads(blocked.next_generation_proposal_path.read_text(encoding="utf-8"))
    approval = GenerationApprovalRecord(
        proposal_id=str(proposal["proposal_id"]),
        proposal_hash=str(proposal["proposal_hash"]),
        decision="approved",
        reviewer="research-lead",
        decided_at=datetime(2026, 5, 27, tzinfo=UTC),
        reason="bounded next generation approved",
        evidence_refs=(str(proposal["proposal_hash"]),),
    )
    approved_run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=data_paths,
        output_root=tmp_path / "run",
        approval_records=(approval,),
    )

    approved = AutonomousResearchEngine(repo_root=Path.cwd()).run(approved_run)

    # WIRING: the matching approval lets the engine proceed past the human gate
    # and run generation-001. HONESTY: the toy fixture promotes nothing across
    # either generation, so the campaign honestly rejects.
    assert (approved.output_root / "generation-001").exists()
    assert approved.status == "rejected"
