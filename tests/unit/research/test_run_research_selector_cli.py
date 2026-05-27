from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from qts.research.campaign import ResearchCampaignConfig
from qts.research.selector import CandidateSelector

from scripts import run_research


def test_selector_replay_reproduces_selection_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    campaign_path = Path("configs/research/campaigns/gc_si_autonomous_v1.yaml")
    candidates_path = _write_candidates(tmp_path, _candidates())
    selection_path = _write_selection(tmp_path, campaign_path, _candidates())
    selected_rows_path = selection_path.with_name("selected_candidates.jsonl")

    exit_code = run_research.main(
        [
            "selector",
            "replay",
            "--selection-result",
            str(selected_rows_path),
            "--campaign",
            str(campaign_path),
            "--candidate-results",
            str(candidates_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is True
    assert payload["reasons"] == []


def test_selector_replay_detects_changed_metrics(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    campaign_path = Path("configs/research/campaigns/gc_si_autonomous_v1.yaml")
    selection_path = _write_selection(tmp_path, campaign_path, _candidates())
    changed_candidates = _candidates()
    changed_candidates[0]["metrics"]["trading"]["oos_trade_count"] = 3
    candidates_path = _write_candidates(tmp_path, changed_candidates)

    exit_code = run_research.main(
        [
            "selector",
            "replay",
            "--selection-result",
            str(selection_path),
            "--campaign",
            str(campaign_path),
            "--candidate-results",
            str(candidates_path),
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert "selector replay mismatch: selection_hash changed" in payload["reasons"]
    assert "selector replay mismatch: selected candidates changed" in payload["reasons"]


def test_selector_replay_detects_changed_constraints(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    base_campaign = Path("configs/research/campaigns/gc_si_autonomous_v1.yaml")
    selection_path = _write_selection(tmp_path, base_campaign, _candidates())
    stricter_campaign = _write_campaign_with_constraint(tmp_path, "min_oos_trade_count", 60)
    candidates_path = _write_candidates(tmp_path, _candidates())

    exit_code = run_research.main(
        [
            "selector",
            "replay",
            "--selection-result",
            str(selection_path),
            "--campaign",
            str(stricter_campaign),
            "--candidate-results",
            str(candidates_path),
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert "selector replay mismatch: constraints changed" in payload["reasons"]


def _write_selection(
    tmp_path: Path,
    campaign_path: Path,
    candidates: list[dict[str, Any]],
) -> Path:
    selection = CandidateSelector(
        run_research._selection_policy_from_campaign(
            ResearchCampaignConfig.from_yaml(campaign_path)
        )
    ).select(candidates)
    path = tmp_path / "selection_result.json"
    payload = selection.to_payload()
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    path.with_name("selected_candidates.jsonl").write_text(
        "\n".join(
            json.dumps(candidate, sort_keys=True) for candidate in payload["selected_candidates"]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_candidates(tmp_path: Path, candidates: list[dict[str, Any]]) -> Path:
    path = tmp_path / "candidate_results.jsonl"
    path.write_text(
        "\n".join(json.dumps(candidate, sort_keys=True) for candidate in candidates) + "\n",
        encoding="utf-8",
    )
    return path


def _write_campaign_with_constraint(tmp_path: Path, name: str, value: object) -> Path:
    payload = yaml.safe_load(
        Path("configs/research/campaigns/gc_si_autonomous_v1.yaml").read_text(encoding="utf-8")
    )
    payload["constraints"][name] = value
    path = tmp_path / "campaign.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def _candidates() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "good",
            "data_quality": {"accepted": True, "blockers": []},
            "evidence": {"evidence_bundle_id": "evb-good"},
            "metrics": {
                "costs": {"cost_sensitivity": 0.01},
                "performance": {
                    "max_drawdown": 0.12,
                    "oos_sharpe": 1.5,
                    "total_return": 0.24,
                },
                "trading": {"oos_trade_count": 50},
            },
            "reproducibility": {"blockers": []},
        },
        {
            "candidate_id": "drawdown",
            "data_quality": {"accepted": True, "blockers": []},
            "evidence": {"evidence_bundle_id": "evb-drawdown"},
            "metrics": {
                "costs": {"cost_sensitivity": 0.01},
                "performance": {
                    "max_drawdown": 0.31,
                    "oos_sharpe": 1.9,
                    "total_return": 0.4,
                },
                "trading": {"oos_trade_count": 70},
            },
            "reproducibility": {"blockers": []},
        },
    ]
