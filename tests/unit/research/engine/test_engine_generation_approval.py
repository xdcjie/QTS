from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)
from qts.research.planner import GenerationApprovalRecord

from .test_autonomous_engine_trial_generation import (
    force_clean_reproducibility,
    write_campaign,
    write_data_paths,
)


def test_engine_stops_before_generation_greater_than_zero_without_approval(
    tmp_path: Path,
) -> None:
    campaign_path = write_campaign(
        tmp_path,
        max_generations=2,
        max_trials_per_generation=2,
        max_total_trials=4,
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    assert result.status == "pending_human_approval"
    assert [generation.generation_id for generation in result.generations] == ["generation-000"]
    summary = json.loads(result.validation_summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "pending_human_approval"


def test_engine_runs_generation_greater_than_zero_with_matching_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    force_clean_reproducibility(monkeypatch)
    campaign_path = write_campaign(
        tmp_path,
        max_generations=2,
        max_trials_per_generation=2,
        max_total_trials=4,
    )
    base_run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )
    first = AutonomousResearchEngine(repo_root=Path.cwd()).run(base_run)
    proposal = json.loads(first.next_generation_proposal_path.read_text(encoding="utf-8"))

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
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
        approval_records=(approval,),
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(approved_run)

    assert result.status == "accepted"
    assert [generation.generation_id for generation in result.generations] == [
        "generation-000",
        "generation-001",
    ]


def test_engine_rejects_generation_approval_for_wrong_proposal_hash(tmp_path: Path) -> None:
    campaign_path = write_campaign(
        tmp_path,
        max_generations=2,
        max_trials_per_generation=2,
        max_total_trials=4,
    )
    approval = GenerationApprovalRecord(
        proposal_id="engine_campaign:generation-001",
        proposal_hash="sha256:not-the-generated-proposal",
        decision="approved",
        reviewer="research-lead",
        decided_at=datetime(2026, 5, 27, tzinfo=UTC),
        reason="wrong artifact",
        evidence_refs=("review-ticket",),
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
        approval_records=(approval,),
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    assert result.status == "pending_human_approval"
    summary = json.loads(result.validation_summary_path.read_text(encoding="utf-8"))
    assert "approval proposal_hash does not match" in " ".join(summary["approval_reasons"])
