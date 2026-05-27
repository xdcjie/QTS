from __future__ import annotations

import json
from pathlib import Path

from qts.research.artifact_graph import ResearchArtifactGraph
from qts.research.audit_log import ResearchAuditLog
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)


def test_gc_si_autonomous_acceptance_campaign(tmp_path: Path) -> None:
    config_path = Path("configs/research/campaigns/gc_si_autonomous_v1.yaml")
    run = AutonomousResearchRun.from_yaml(
        config_path,
        data_paths=_write_data_paths(tmp_path),
        output_root=tmp_path / "gc_si_autonomous_v1",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    assert result.status == "accepted"
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
        "evidence/index.jsonl",
        "packets",
        "audit/audit_log.jsonl",
        "artifact_graph/artifact_graph.json",
        "report.md",
        "validation_summary.json",
    )
    for relative_path in expected_paths:
        assert (result.output_root / relative_path).exists(), relative_path

    validation_summary = json.loads(result.validation_summary_path.read_text(encoding="utf-8"))
    assert validation_summary["status"] == "accepted"
    assert validation_summary["promotion_packet_count"] >= 1
    assert validation_summary["rejected_candidate_count"] >= 1

    rejected_rows = _jsonl(result.rejected_candidates_path)
    assert rejected_rows
    assert all(row["reasons"] for row in rejected_rows)

    proposal = json.loads(result.next_generation_proposal_path.read_text(encoding="utf-8"))
    assert proposal["evidence_refs"]
    assert proposal["requires_human_approval"] is True

    graph = ResearchArtifactGraph.from_payload(
        json.loads(result.artifact_graph_path.read_text(encoding="utf-8"))
    )
    graph.validate_full_chain()
    assert ResearchAuditLog(result.audit_log_path).verify_hash_chain() == ()
    assert "gc_si_autonomous_v1" in result.report_path.read_text(encoding="utf-8")


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_data_paths(tmp_path: Path) -> dict[str, Path]:
    data_dir = tmp_path / "input_data"
    data_dir.mkdir()
    return {
        "GC": _write_bars(data_dir / "gc.csv", base=100),
        "SI": _write_bars(data_dir / "si.csv", base=101),
    }


def _write_bars(path: Path, *, base: int) -> Path:
    path.write_text(
        "\n".join(
            [
                "timestamp,close",
                f"2026-01-02T00:00:00+00:00,{base}.0",
                f"2026-01-02T00:01:00+00:00,{base}.5",
                f"2026-01-02T00:02:00+00:00,{base + 1}.0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path
