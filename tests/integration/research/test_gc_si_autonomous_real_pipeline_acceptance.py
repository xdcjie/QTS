from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from qts.research.artifact_graph import ResearchArtifactGraph
from qts.research.audit_log import ResearchAuditLog

from scripts import run_research


def test_gc_si_autonomous_real_pipeline_acceptance_cli(
    tmp_path: Path,
    capsys: Any,
) -> None:
    config_path = Path("configs/research/campaigns/gc_si_autonomous_v1.yaml")
    output_root = tmp_path / "gc_si_autonomous_v1"
    data_paths = _write_data_paths(tmp_path)

    config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config_payload["execution"]["default_mode"] == "backtest_pipeline"
    assert config_payload["selection"]["selector"] == "CandidateSelector"
    assert config_payload["selection"]["gauntlet"] == "ValidationGauntlet"
    assert config_payload["launch_controls"]["paper_live_launches"] == "disabled"

    run_exit = run_research.main(
        [
            "campaign",
            "run",
            "--campaign",
            str(config_path),
            "--output-root",
            str(output_root),
            "--data-path",
            f"GC={data_paths['GC']}",
            "--data-path",
            f"SI={data_paths['SI']}",
        ]
    )
    assert run_exit == 0
    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["status"] == "pending_human_approval"
    assert run_payload["acceptance_markers"]["execution_mode"] == "backtest_pipeline"
    assert run_payload["acceptance_markers"]["paper_live_launches"] == []

    proposal = json.loads((output_root / "next_generation_proposal.json").read_text())
    approve_exit = run_research.main(
        [
            "campaign",
            "approve-next-generation",
            "--proposal",
            str(output_root / "next_generation_proposal.json"),
            "--expected-proposal-hash",
            proposal["proposal_hash"],
            "--output-root",
            str(output_root),
            "--decision",
            "approved",
            "--reviewer",
            "research-lead",
            "--reason",
            "real path markers reviewed",
        ]
    )
    assert approve_exit == 0
    capsys.readouterr()

    resume_exit = run_research.main(["campaign", "resume", "--output-root", str(output_root)])
    assert resume_exit == 0
    resume_payload = json.loads(capsys.readouterr().out)
    assert resume_payload["status"] == "accepted"
    assert resume_payload["paper_live_launches"] == []
    assert resume_payload["acceptance_markers"]["execution_mode"] == "backtest_pipeline"
    assert resume_payload["acceptance_markers"]["selector"] == "CandidateSelector"
    assert resume_payload["acceptance_markers"]["gauntlet"] == "ValidationGauntlet"

    rejected_rows = _jsonl(output_root / "rejected_candidates.jsonl")
    assert any(row.get("selector_reasons") for row in rejected_rows)
    assert any(row.get("gauntlet_reasons") for row in rejected_rows)

    validation_summary = json.loads((output_root / "validation_summary.json").read_text())
    assert validation_summary["real_path_markers"]["metrics_source"] == "backtest_artifacts"
    assert validation_summary["paper_live_launches"] == []

    graph = ResearchArtifactGraph.from_payload(
        json.loads((output_root / "artifact_graph" / "artifact_graph.json").read_text())
    )
    graph.validate_full_chain()
    assert ResearchAuditLog(output_root / "audit" / "audit_log.jsonl").verify_hash_chain() == ()


def _jsonl(path: Path) -> list[dict[str, Any]]:
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
            ["timestamp,close"]
            + [
                f"2026-01-02T00:{minute:02d}:00+00:00,{base + (minute * 0.5):.1f}"
                for minute in range(20)
            ]
            + [""]
        ),
        encoding="utf-8",
    )
    return path
