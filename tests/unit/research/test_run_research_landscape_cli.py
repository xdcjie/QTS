from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.research.landscape import FitnessLandscapePoint, FitnessLandscapeStore

from scripts import run_research


def test_landscape_summarize_reports_family_success_and_rejections(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    landscape_path = _write_landscape(tmp_path)

    exit_code = run_research.main(["landscape", "--landscape", str(landscape_path), "summarize"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["analytics"]["best_family"]["strategy_family"] == "momentum"
    assert payload["analytics"]["best_family"]["family_success_rate"] == 1.0
    assert payload["family_success_rate"] == {"momentum/momentum": 1.0, "breakout/breakout": 0.0}
    assert payload["rejection_distribution"] == {"max_drawdown": 1}
    assert payload["rejection_reason_counts"] == {"max_drawdown": 1}


def test_landscape_query_filters_by_root_regime_and_session(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    landscape_path = _write_landscape(tmp_path)

    exit_code = run_research.main(
        [
            "landscape",
            "--landscape",
            str(landscape_path),
            "query",
            "--root",
            "SI",
            "--regime",
            "risk_off",
            "--session",
            "rth",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["query_count"] == 1
    assert payload["points"][0]["trial_id"] == "trial-si"


def test_landscape_export_writes_deterministic_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    landscape_path = _write_landscape(tmp_path)
    output = tmp_path / "export.json"

    exit_code = run_research.main(
        [
            "landscape",
            "--landscape",
            str(landscape_path),
            "export",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert file_payload["analytics"]["best_family"]["strategy_family"] == "momentum"
    assert file_payload["trial_count"] == 2


def _write_landscape(tmp_path: Path) -> Path:
    store = FitnessLandscapeStore(tmp_path / "fitness_landscape.jsonl")
    store.append(
        FitnessLandscapePoint(
            trial_id="trial-gc",
            retry_id=None,
            campaign_id="campaign-1",
            generation_id="generation-000",
            strategy_family="momentum",
            factor_family="momentum",
            universe=("GC", "SI"),
            root="GC",
            timeframe="1m",
            regime="risk_on",
            session="globex",
            parameter_hash="sha256:param-gc",
            metrics=_metrics(1.4, 0.12),
            constraints={"max_drawdown": 0.25},
            accepted=True,
            rejected_reasons=(),
            evidence_bundle_id="evb-gc",
            promotion_packet_id="pc-gc",
            artifact_graph_hash="sha256:graph-gc",
        )
    )
    store.append(
        FitnessLandscapePoint(
            trial_id="trial-si",
            retry_id=None,
            campaign_id="campaign-1",
            generation_id="generation-000",
            strategy_family="breakout",
            factor_family="breakout",
            universe=("GC", "SI"),
            root="SI",
            timeframe="1m",
            regime="risk_off",
            session="rth",
            parameter_hash="sha256:param-si",
            metrics=_metrics(0.6, 0.31),
            constraints={"max_drawdown": 0.25},
            accepted=False,
            rejected_reasons=("max_drawdown",),
            evidence_bundle_id="evb-si",
            promotion_packet_id=None,
            artifact_graph_hash="sha256:graph-si",
        )
    )
    return store.path


def _metrics(oos_sharpe: float, max_drawdown: float) -> dict[str, object]:
    return {
        "costs": {"cost_sensitivity": 0.02},
        "performance": {
            "max_drawdown": max_drawdown,
            "oos_sharpe": oos_sharpe,
            "total_return": 0.1,
            "train_sharpe": oos_sharpe + 0.1,
        },
    }
