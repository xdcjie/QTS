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
    data_paths = _historical_data_paths(tmp_path)

    config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config_payload["execution"]["default_mode"] == "backtest_pipeline"
    assert config_payload["selection"]["selector"] == "CandidateSelector"
    assert config_payload["selection"]["gauntlet"] == "ValidationGauntlet"
    assert config_payload["execution"]["data_mode"] == "fixture"
    assert config_payload["execution"]["max_rows"] == 50
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
    assert any(
        row.get("rejection_stage") == "selector" and row.get("selector_reasons")
        for row in rejected_rows
    )
    assert any(
        row.get("rejection_stage") == "gauntlet" and row.get("gauntlet_reasons")
        for row in rejected_rows
    )
    assert all(
        not row.get("gauntlet_reasons")
        for row in rejected_rows
        if row.get("rejection_stage") != "gauntlet"
    )

    validation_summary = json.loads((output_root / "validation_summary.json").read_text())
    assert validation_summary["real_path_markers"]["metrics_source"] == "backtest_artifacts"
    assert validation_summary["paper_live_launches"] == []
    campaign_config = json.loads((output_root / "campaign_config.json").read_text())
    assert campaign_config["data_paths"] == {
        "GC": str(data_paths["GC"]),
        "SI": str(data_paths["SI"]),
    }

    graph = ResearchArtifactGraph.from_payload(
        json.loads((output_root / "artifact_graph" / "artifact_graph.json").read_text())
    )
    graph.validate_full_chain()
    assert ResearchAuditLog(output_root / "audit" / "audit_log.jsonl").verify_hash_chain() == ()
    selected_rows = _jsonl(output_root / "selected_candidates.jsonl")
    rejected_rows = _jsonl(output_root / "rejected_candidates.jsonl")
    landscape_rows = _jsonl(output_root / "fitness_landscape.jsonl")
    assert len(landscape_rows) == len(selected_rows) + len(rejected_rows)
    assert selected_rows
    for row in selected_rows:
        packet = json.loads(Path(row["promotion_packet_path"]).read_text())
        assert packet["validation"]["status"] == "human_pending"
        assert packet["review"] == {"status": "human_pending"}
    gauntlet = json.loads((output_root / "generation-001" / "validation_gauntlet.json").read_text())
    for result in gauntlet["results"]:
        for decision in result["gate_decisions"]:
            assert decision["evidence"]["artifact_path"]
            assert str(decision["evidence"]["payload_hash"]).startswith("sha256:")

    verify_exit = run_research.main(["campaign", "verify", "--output-root", str(output_root)])
    assert verify_exit == 0
    verify_payload = json.loads(capsys.readouterr().out)
    assert verify_payload["accepted"] is True
    assert (output_root / "release_verification.json").exists()


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _historical_data_paths(tmp_path: Path) -> dict[str, Path]:
    source_paths = {
        "GC": Path("tests/fixtures/research/gc_si_real_history/gc.csv"),
        "SI": Path("tests/fixtures/research/gc_si_real_history/si.csv"),
    }
    missing = [str(path) for path in source_paths.values() if not path.exists()]
    if missing:
        raise AssertionError(f"GC/SI historical fixture CSV files are required: {missing}")
    slice_dir = tmp_path / "real_historical_slice"
    slice_dir.mkdir()
    return {
        root: _copy_real_historical_slice(
            source_path,
            slice_dir / f"{root.lower()}.csv",
        )
        for root, source_path in source_paths.items()
    }


def _copy_real_historical_slice(source_path: Path, target_path: Path) -> Path:
    expected = {f"2010-11-12T05:{minute:02d}:00.000000000Z" for minute in range(15, 60)} | {
        f"2010-11-12T06:{minute:02d}:00.000000000Z" for minute in range(5)
    }
    with (
        source_path.open("r", encoding="utf-8", newline="") as source,
        target_path.open("w", encoding="utf-8", newline="") as target,
    ):
        header = source.readline()
        target.write(header)
        columns = header.strip().split(",")
        timestamp_index = columns.index("ts_event")
        close_index = columns.index("close")
        emitted: set[str] = set()
        for line in source:
            values = line.strip().split(",")
            timestamp = values[timestamp_index]
            if (
                timestamp not in expected
                or timestamp in emitted
                or values[close_index].startswith("-")
            ):
                continue
            target.write(line)
            emitted.add(timestamp)
            if len(emitted) == len(expected):
                break
    if len(emitted) != len(expected):
        missing = sorted(expected - emitted)
        raise AssertionError(f"historical slice missing real source rows: {missing[:5]}")
    return target_path
