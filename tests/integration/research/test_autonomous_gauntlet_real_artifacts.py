from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)
from qts.research.planner import GenerationApprovalRecord

from tests.integration.research._autonomous_engine_plan_helpers import run_engine
from tests.unit.research.engine.test_autonomous_engine_trial_generation import (
    write_campaign,
    write_data_paths,
)


def test_autonomous_gauntlet_consumes_validation_artifact_refs(tmp_path: Path) -> None:
    _campaign_path, result = run_engine(tmp_path)

    payload = json.loads(
        (result.output_root / "generation-000" / "validation_gauntlet.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["results"]
    for gauntlet_result in payload["results"]:
        for decision in gauntlet_result["gate_decisions"]:
            assert Path(decision["evidence"]["artifact_path"]).exists()
            assert str(decision["evidence"]["payload_hash"]).startswith("sha256:")


def test_correlation_artifact_uses_prior_selected_equity_curve_context(tmp_path: Path) -> None:
    campaign_path = write_campaign(tmp_path, max_generations=2)
    first_run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )
    first_result = AutonomousResearchEngine(repo_root=Path.cwd()).run(first_run)
    proposal = json.loads(first_result.next_generation_proposal_path.read_text(encoding="utf-8"))
    approval = GenerationApprovalRecord(
        proposal_id=str(proposal["proposal_id"]),
        proposal_hash=str(proposal["proposal_hash"]),
        decision="approved",
        reviewer="research-lead",
        decided_at=datetime(2026, 5, 27, tzinfo=UTC),
        reason="correlation evidence context reviewed",
        evidence_refs=(str(proposal["proposal_hash"]),),
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
        approval_records=(approval,),
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)
    payload = json.loads(
        (result.output_root / "generation-001" / "validation_gauntlet.json").read_text(
            encoding="utf-8"
        )
    )

    correlation_decisions = [
        decision
        for gauntlet_result in payload["results"]
        for decision in gauntlet_result["gate_decisions"]
        if decision["gate_name"] == "correlation"
    ]
    assert correlation_decisions
    for decision in correlation_decisions:
        wrapper = json.loads(Path(decision["evidence"]["artifact_path"]).read_text())
        snapshot = wrapper["payload"]["active_portfolio_snapshot"]
        assert snapshot["candidate_return_count"] > 0
        assert snapshot["active_candidates"]
        assert snapshot["active_candidates"][0]["common_return_count"] > 0
