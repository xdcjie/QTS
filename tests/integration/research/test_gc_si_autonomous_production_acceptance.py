from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from scripts import run_research


def test_gc_vwap_trend_robust_production_acceptance(
    tmp_path: Path,
    capsys: Any,
) -> None:
    campaign_path = Path("configs/research/campaigns/gc_vwap_trend_robust_scan_v1.yaml")
    data_paths = _production_data_paths()

    config = yaml.safe_load(campaign_path.read_text(encoding="utf-8"))
    assert config["execution"]["data_mode"] == "full"
    assert "max_rows" not in config["execution"]
    assert "start" not in config["execution"]
    assert "end" not in config["execution"]
    assert len(config["execution"]["windows"]) == 25
    assert config["families"] == [
        {
            "id": "gc_vwap_trend_robust_scan",
            "template": "vwap_trend",
            "manifest_template": "configs/research/manifests/templates/gc_si_vwap_trend.yaml",
            "search_space": "configs/research/search/gc_vwap_trend_robust_space.yaml",
        }
    ]
    assert config["budget"]["max_generations"] == 1
    assert config["budget"]["max_total_trials"] == 16

    output_root = tmp_path / "gc_vwap_trend_robust_scan_v1"
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
    # WIRING: the full production grid (16 candidates) runs end-to-end over the
    # full real GC history (34500 materialized rows) with no paper/live launch.
    # HONESTY: under the multiplicity / deflated-Sharpe gate no candidate clears
    # the promotion bar even on real data, so the campaign honestly rejects
    # (exit 1, status=rejected, selected_count=0). Promotion is not faked.
    assert run_exit == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "rejected"
    assert payload["paper_live_launches"] == []
    gc_data_path = output_root / "backtest_data" / "full" / "GC" / "data" / "GC.csv"
    assert _csv_row_count(gc_data_path) == 34500

    selected_rows = _jsonl(output_root / "selected_candidates.jsonl")
    rejected_rows = _jsonl(output_root / "rejected_candidates.jsonl")
    landscape_rows = _jsonl(output_root / "fitness_landscape.jsonl")
    assert selected_rows == []
    assert len(rejected_rows) == 16
    assert all(row["reasons"] for row in rejected_rows)
    assert len(landscape_rows) == 16

    # HONESTY: a rejected campaign is not release-verifiable; verify fails because
    # there is no promotion artifact chain to release.
    verify_exit = run_research.main(["campaign", "verify", "--output-root", str(output_root)])
    assert verify_exit == 1
    verify_payload = json.loads(capsys.readouterr().out)
    assert verify_payload["accepted"] is False
    assert verify_payload["criteria"]["fitness_landscape"]["generated_candidate_count"] == 16


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _production_data_paths() -> dict[str, Path]:
    production_paths = {
        "GC": Path("historical/data/gc.csv"),
        "SI": Path("historical/data/si.csv"),
    }
    missing = [str(path) for path in production_paths.values() if not path.exists()]
    if missing:
        raise AssertionError(f"GC/SI historical CSV files are required: {missing}")
    return production_paths


def _csv_row_count(path: Path) -> int:
    return max(len(path.read_text(encoding="utf-8").splitlines()) - 1, 0)
