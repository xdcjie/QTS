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

from tests.integration.research._autonomous_engine_plan_helpers import run_engine
from tests.unit.research.engine.test_autonomous_engine_trial_generation import (
    force_clean_reproducibility,
    write_campaign,
    write_data_paths,
)


def test_autonomous_gauntlet_consumes_validation_artifact_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # WIRING: a candidate that reaches the gauntlet produces artifact-backed,
    # hash-anchored gate decisions, including a correlation snapshot built from
    # the candidate's own returns when no prior candidate is active. The campaign
    # still honestly rejects at the promotion bar (no faked promotion).
    force_clean_reproducibility(monkeypatch)
    # Toy fixture is calibrated for same_bar_close economics so a candidate
    # reaches the gauntlet; this asserts gauntlet plumbing + honest rejection.
    _campaign_path, result = run_engine(tmp_path, fill_policy="same_bar_close")

    payload = json.loads(
        (result.output_root / "generation-000" / "validation_gauntlet.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["results"]
    for gauntlet_result in payload["results"]:
        for decision in gauntlet_result["gate_decisions"]:
            if decision["gate_name"] in ("deflated_sharpe", "pbo"):
                # Multiplicity gates read the selector's inline multiplicity-
                # adjustment evidence, not a backtest_pipeline artifact.
                continue
            assert Path(decision["evidence"]["artifact_path"]).exists()
            assert str(decision["evidence"]["payload_hash"]).startswith("sha256:")
            if decision["gate_name"] == "correlation":
                wrapper = json.loads(Path(decision["evidence"]["artifact_path"]).read_text())
                snapshot = wrapper["payload"]["active_portfolio_snapshot"]
                assert snapshot["active_portfolio_status"] == "no_active_candidates"
                assert snapshot["candidate_return_count"] > 0


def test_correlation_artifact_reports_prior_selected_equity_curve_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # WIRING: generation-001's correlation gate queries the prior generation's
    # selected equity-curve context and builds a real, candidate-backed snapshot.
    # HONESTY: generation-000 promoted nothing, so the snapshot honestly reports
    # "no_active_candidates" (empty active set) rather than fabricating a prior
    # portfolio, while still carrying the candidate's own return context.
    force_clean_reproducibility(monkeypatch)
    campaign_path = write_campaign(tmp_path, max_generations=2, fill_policy="same_bar_close")
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
        assert snapshot["active_portfolio_status"] == "no_active_candidates"
        assert snapshot["active_candidates"] == []
