from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from qts.research.audit_log import ResearchAuditLog
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)
from qts.research.planner import GenerationApprovalRecord

from tests.unit.research.engine.test_autonomous_engine_trial_generation import (
    _multi_month_fixture_csv,
)


def test_autonomous_engine_runs_two_bounded_generations_without_runtime_launch(
    tmp_path: Path,
) -> None:
    config_path = Path("configs/research/campaigns/gc_si_autonomous_v1.yaml")
    first_run = AutonomousResearchRun.from_yaml(
        config_path,
        data_paths=_write_data_paths(tmp_path),
        output_root=tmp_path / "autonomous",
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
        output_root=tmp_path / "autonomous",
        approval_records=(approval,),
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    assert result.status == "accepted"
    assert result.paper_live_launches == ()
    assert [generation.generation_id for generation in result.generations] == [
        "generation-000",
        "generation-001",
    ]
    assert all(generation.trial_count >= 3 for generation in result.generations)
    assert all(generation.audit_record_count > 0 for generation in result.generations)
    assert all(generation.landscape_path.exists() for generation in result.generations)
    assert all(
        generation.next_generation_proposal_path.exists() for generation in result.generations
    )

    landscape_rows = _jsonl(result.fitness_landscape_path)
    assert len(landscape_rows) == sum(generation.trial_count for generation in result.generations)
    assert {row["generation_id"] for row in landscape_rows} == {
        "generation-000",
        "generation-001",
    }
    assert all(str(row["artifact_graph_hash"]).startswith("sha256:") for row in landscape_rows)
    assert all(str(row["point_hash"]).startswith("sha256:") for row in landscape_rows)

    selected_rows = _jsonl(result.selected_candidates_path)
    assert selected_rows
    assert all(row["evidence_bundle_id"] for row in selected_rows)
    assert all(Path(str(row["promotion_packet_path"])).exists() for row in selected_rows)

    proposal = json.loads(result.next_generation_proposal_path.read_text(encoding="utf-8"))
    assert proposal["proposal_id"] == "gc_si_autonomous_v1:generation-002"
    assert proposal["mutations"]

    assert ResearchAuditLog(result.audit_log_path).verify_hash_chain() == ()


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
    path.write_text(_multi_month_fixture_csv(base=base), encoding="utf-8")
    return path
