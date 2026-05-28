from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from scripts import run_research


def test_gc_si_autonomous_production_acceptance(
    tmp_path: Path,
    capsys: Any,
) -> None:
    campaign_path = Path("configs/research/campaigns/gc_si_autonomous_production_v1.yaml")
    data_paths = _production_data_paths()

    config = yaml.safe_load(campaign_path.read_text(encoding="utf-8"))
    assert config["execution"]["data_mode"] == "full"
    assert "max_rows" not in config["execution"]
    assert config["execution"]["start"] == "2010-06-07T12:02:00+00:00"
    assert config["execution"]["end"] == "2010-06-07T18:05:00+00:00"
    assert config["budget"]["max_generations"] >= 2
    assert config["budget"]["max_total_trials"] >= 30

    output_root = tmp_path / "gc_si_autonomous_production_v1"
    run_exit = run_research.main(
        [
            "campaign",
            "run",
            "--campaign",
            str(campaign_path),
            "--output-root",
            str(output_root),
            "--data-path",
            f"GC={data_paths['GC']}",
            "--data-path",
            f"SI={data_paths['SI']}",
        ]
    )
    assert run_exit == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pending_human_approval"

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
            "production campaign evidence reviewed",
        ]
    )
    assert approve_exit == 0
    capsys.readouterr()

    resume_exit = run_research.main(["campaign", "resume", "--output-root", str(output_root)])
    assert resume_exit == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "accepted"
    assert payload["paper_live_launches"] == []

    verify_exit = run_research.main(["campaign", "verify", "--output-root", str(output_root)])
    assert verify_exit == 0
    verify_payload = json.loads(capsys.readouterr().out)
    assert verify_payload["accepted"] is True
    assert verify_payload["criteria"]["fitness_landscape"]["generated_candidate_count"] >= 30


def _production_data_paths() -> dict[str, Path]:
    production_paths = {
        "GC": Path("historical/data/gc.csv"),
        "SI": Path("historical/data/si.csv"),
    }
    missing = [str(path) for path in production_paths.values() if not path.exists()]
    if missing:
        raise AssertionError(f"GC/SI historical CSV files are required: {missing}")
    return production_paths
