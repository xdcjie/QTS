from __future__ import annotations

import json
from pathlib import Path

from qts.research.audit_log import ResearchAuditLog
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)


def test_autonomous_engine_runs_two_bounded_generations_without_runtime_launch(
    tmp_path: Path,
) -> None:
    run = AutonomousResearchRun(
        campaign_id="gc-si-autonomous-fixture",
        data_paths=_write_data_paths(tmp_path),
        output_root=tmp_path / "autonomous",
        universe=("GC", "SI"),
        families=("momentum", "spread", "breakout"),
        max_generations=2,
        trials_per_generation=3,
        approval_policy="auto_fixture",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    assert result.status == "accepted"
    assert result.paper_live_launches == ()
    assert [generation.generation_id for generation in result.generations] == [
        "generation-000",
        "generation-001",
    ]
    assert all(generation.trial_count == 3 for generation in result.generations)
    assert all(generation.audit_record_count > 0 for generation in result.generations)
    assert all(generation.landscape_path.exists() for generation in result.generations)
    assert all(
        generation.next_generation_proposal_path.exists() for generation in result.generations
    )

    landscape_rows = _jsonl(result.fitness_landscape_path)
    assert len(landscape_rows) == 6
    assert {row["generation_id"] for row in landscape_rows} == {
        "generation-000",
        "generation-001",
    }
    assert all(str(row["manifest_hash"]).startswith("sha256:") for row in landscape_rows)

    selected_rows = _jsonl(result.selected_candidates_path)
    assert selected_rows
    assert all(row["evidence_bundle_id"] for row in selected_rows)
    assert all(Path(str(row["promotion_packet_path"])).exists() for row in selected_rows)

    proposal = json.loads(result.next_generation_proposal_path.read_text(encoding="utf-8"))
    assert proposal["proposal_id"].startswith("proposal-")
    assert proposal["evidence_refs"]

    assert ResearchAuditLog(result.audit_log_path).verify_hash_chain() == ()


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
