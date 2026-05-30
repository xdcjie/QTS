from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from qts.research.artifact_graph import ResearchArtifactGraph
from qts.research.audit_log import ResearchAuditLog
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)
from qts.research.planner import GenerationApprovalRecord


def test_gc_si_autonomous_acceptance_campaign(tmp_path: Path) -> None:
    config_path = Path("configs/research/campaigns/gc_si_autonomous_v1.yaml")
    first_run = AutonomousResearchRun.from_yaml(
        config_path,
        data_paths=_write_data_paths(tmp_path),
        output_root=tmp_path / "gc_si_autonomous_v1",
    )
    first_result = AutonomousResearchEngine(repo_root=Path.cwd()).run(first_run)
    proposal = json.loads(first_result.next_generation_proposal_path.read_text(encoding="utf-8"))
    approval = GenerationApprovalRecord(
        proposal_id=str(proposal["proposal_id"]),
        proposal_hash=str(proposal["proposal_hash"]),
        decision="approved",
        reviewer="research-lead",
        decided_at=datetime(2026, 5, 27, tzinfo=UTC),
        reason="bounded next generation reviewed",
        evidence_refs=(str(proposal["proposal_hash"]),),
    )
    run = AutonomousResearchRun.from_yaml(
        config_path,
        data_paths=_write_data_paths(tmp_path),
        output_root=tmp_path / "gc_si_autonomous_v1",
        approval_records=(approval,),
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    # WIRING: the approved second generation runs end-to-end and the full honest
    # campaign artifact set is produced. HONESTY: the toy fixture clears no
    # candidate through the promotion bar, so the campaign honestly rejects
    # (promotion is not faked).
    assert result.status == "rejected"
    assert result.output_root == tmp_path / "gc_si_autonomous_v1"
    assert result.paper_live_launches == ()
    assert len(result.generations) >= 2
    assert result.validation_summary_path.exists()
    assert result.report_path.exists()

    expected_paths = (
        "campaign_config.json",
        "generation-000",
        "generation-001",
        "fitness_landscape.jsonl",
        "fitness_analytics.json",
        "next_generation_proposal.json",
        "selected_candidates.jsonl",
        "rejected_candidates.jsonl",
        "audit/audit_log.jsonl",
        "artifact_graph/artifact_graph.json",
        "report.md",
        "validation_summary.json",
    )
    for relative_path in expected_paths:
        assert (result.output_root / relative_path).exists(), relative_path

    # A rejected campaign promotes no candidate.
    assert _jsonl(result.selected_candidates_path) == []

    validation_summary = json.loads(result.validation_summary_path.read_text(encoding="utf-8"))
    assert validation_summary["status"] == "rejected"
    assert validation_summary["promotion_packet_count"] == 0
    assert validation_summary["rejected_candidate_count"] >= 1

    rejected_rows = _jsonl(result.rejected_candidates_path)
    assert rejected_rows
    assert all(row["reasons"] for row in rejected_rows)

    proposal = json.loads(result.next_generation_proposal_path.read_text(encoding="utf-8"))
    assert proposal["mutations"]
    assert proposal["proposal_hash"].startswith("sha256:")

    # The artifact graph is structurally valid and the audit chain is intact; a
    # rejected campaign has no promotion sub-chain, so the basic graph contract
    # is asserted rather than the release full-chain.
    graph = ResearchArtifactGraph.from_payload(
        json.loads(result.artifact_graph_path.read_text(encoding="utf-8"))
    )
    graph.validate()
    assert ResearchAuditLog(result.audit_log_path).verify_hash_chain() == ()
    assert "gc_si_autonomous_v1" in result.report_path.read_text(encoding="utf-8")


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_data_paths(tmp_path: Path) -> dict[str, Path]:
    data_dir = tmp_path / "input_data"
    data_dir.mkdir(exist_ok=True)
    return {
        "GC": _write_bars(data_dir / "gc.csv", base=100),
        "SI": _write_bars(data_dir / "si.csv", base=101),
    }


def _write_bars(path: Path, *, base: int) -> Path:
    path.write_text(
        "\n".join(
            ["timestamp,close"]
            + [
                f"2026-01-02T00:{minute:02d}:00+00:00,{price:.1f}"
                for minute, price in enumerate(_profit_factor_fixture_prices(base))
            ]
            + [""]
        ),
        encoding="utf-8",
    )
    return path


def _profit_factor_fixture_prices(base: int) -> tuple[int, ...]:
    return (
        *((base,) * 15),
        base + 1,
        base,
        base - 1,
        *((base - 1,) * 15),
        base,
        base + 3,
        base + 6,
        base + 9,
        base + 12,
        base + 8,
        base + 4,
        *((base + 4,) * 10),
    )
