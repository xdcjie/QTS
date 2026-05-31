"""Characterization tests pinning the validation-artifact writer payloads.

These tests pin the *observable output* of the promotion-grade validation
artifacts that the experiment runner produces for a succeeded trial: the
payload dictionaries (which are content-addressed via ``stable_json_hash``)
and the source-artifact hash map. The ``payload_hash`` values are what the
evidence bundle and promotion packet later verify against, so pinning them
guards the extraction of the validation-artifact writer against any silent
change to hash-determining content.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import qts.research.orchestrator.experiment_runner as experiment_runner
import qts.research.orchestrator.trial_helpers as trial_helpers
from qts.research.optimizer.result import OptimizationResult
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentRunner,
)

# Payload hashes for the artifacts whose payloads contain no absolute paths.
# These are byte-stable and form the strongest behavior anchor.
_EXPECTED_PAYLOAD_HASHES = {
    "capacity_report": ("sha256:a8b5f38e214789961f7043e9e07b87985251ae5648296fedbecd4a2e0f0424b9"),
    "correlation_report": (
        "sha256:f5575fbfa35604753c626b87a363f2d8cac689edeba63550a2235ec537c5bf14"
    ),
    "deterministic_replay": (
        "sha256:7fa115c887e435572b53ce7c78b3c3a8bb0114ac1d750e3ecf78ccacd9d4c86a"
    ),
    "no_lookahead": ("sha256:c9d70e7b546ad2073d084a8206471745ca269aed6701fdea642b97243626593b"),
}

# Source-artifact hashes that are stable across output directories. The
# ``metrics`` source hash is intentionally excluded: the metrics payload
# embeds absolute artifact paths, so its hash varies per output root (this is
# pre-existing runner behavior, faithfully preserved by the extraction).
_EXPECTED_STABLE_SOURCE_ARTIFACTS = {
    "backtest_manifest": "sha256:research-backtest-manifest",
    "equity_curve": "sha256:equity",
    "failure_window_manifest": "sha256:research-backtest-manifest",
    "fills": "sha256:fills",
    "replay_manifest": "sha256:research-backtest-manifest",
    "statistics": "sha256:statistics",
    "stress_manifest": "sha256:research-backtest-manifest",
    "test_manifest": "sha256:research-backtest-manifest",
    "trade_ledger": "sha256:trade-ledger",
    "train_manifest": "sha256:research-backtest-manifest",
}


def test_validation_artifact_payloads_are_pinned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_backtest_pipeline_runner(monkeypatch)
    data_path = _write_bars(tmp_path)
    job = _job(tmp_path, data_path)
    runner = ResearchExperimentRunner(repo_root=Path.cwd())

    result = runner.run(job)
    accepted = result.trials[0]
    assert accepted.status == "succeeded"

    paths = runner.write_validation_artifacts_for_trial(
        trial=job.trials[0],
        trial_result=accepted,
    )

    assert set(paths) == {
        "capacity_report",
        "correlation_report",
        "cost_stress",
        "deterministic_replay",
        "failure_window_veto",
        "no_lookahead",
        "walk_forward_validation",
    }

    wrappers = {
        name: json.loads(Path(path).read_text(encoding="utf-8")) for name, path in paths.items()
    }

    # Every artifact wrapper records the same source-artifact hash map and
    # evidence source.
    for name, wrapper in wrappers.items():
        assert wrapper["evidence_source"] == "backtest_pipeline_artifact", name
        source_artifacts = wrapper["source_artifacts"]
        for key, expected in _EXPECTED_STABLE_SOURCE_ARTIFACTS.items():
            assert source_artifacts[key] == expected, (name, key)
        assert source_artifacts["metrics"].startswith("sha256:"), name
        assert wrapper["payload_hash"].startswith("sha256:"), name

    # Path-free payloads: pin the exact content hash. These are what the
    # promotion packet and evidence bundle verify against downstream.
    for name, expected_hash in _EXPECTED_PAYLOAD_HASHES.items():
        assert wrappers[name]["payload_hash"] == expected_hash, name

    # Path-bearing payloads: pin the structurally significant fields that do
    # not embed the per-run absolute output path.
    walk_forward = wrappers["walk_forward_validation"]["payload"]
    assert walk_forward["consistent"] is True
    assert walk_forward["manifest_statistics_hash"] == "sha256:statistics"
    assert walk_forward["max_train_test_gap"] == 0.0
    assert walk_forward["test_windows"][0]["score"] == 1.25
    assert walk_forward["test_windows"][0]["train_score"] == 1.25
    assert walk_forward["test_windows"][0]["accepted"] is True

    cost_stress = wrappers["cost_stress"]["payload"]
    assert cost_stress["degradation"] == 0.0
    assert cost_stress["slippage_sensitivity"] == 0.0
    assert cost_stress["stressed_score"] == 1.25
    assert cost_stress["baseline_statistics_hash"] == "sha256:statistics"

    failure = wrappers["failure_window_veto"]["payload"]["failure_windows"][0]
    assert failure["breached"] is False
    assert failure["max_drawdown"] == 0.1
    assert failure["equity_curve_hash"] == "sha256:equity"
    assert failure["report_only"] is False


def test_path_free_validation_artifacts_are_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Path-free validation payloads hash identically across output roots.

    The capacity, correlation, deterministic-replay, and no-lookahead payloads
    embed no absolute output paths, so their content hashes must be stable
    regardless of where the trial ran. (The walk-forward, cost-stress, and
    failure-window payloads embed per-run manifest paths and so are not pinned
    here.)
    """
    _patch_backtest_pipeline_runner(monkeypatch)
    data_path = _write_bars(tmp_path)
    runner = ResearchExperimentRunner(repo_root=Path.cwd())
    pinned = set(_EXPECTED_PAYLOAD_HASHES)

    job_first = _job(tmp_path / "first", data_path)
    first = runner.run(job_first)
    first_paths = runner.write_validation_artifacts_for_trial(
        trial=job_first.trials[0],
        trial_result=first.trials[0],
    )
    first_hashes = {
        name: json.loads(Path(path).read_text(encoding="utf-8"))["payload_hash"]
        for name, path in first_paths.items()
        if name in pinned
    }

    job_second = _job(tmp_path / "second", data_path)
    second = runner.run(job_second)
    second_paths = runner.write_validation_artifacts_for_trial(
        trial=job_second.trials[0],
        trial_result=second.trials[0],
    )
    second_hashes = {
        name: json.loads(Path(path).read_text(encoding="utf-8"))["payload_hash"]
        for name, path in second_paths.items()
        if name in pinned
    }

    assert first_hashes == second_hashes == _EXPECTED_PAYLOAD_HASHES


def _job(output_parent: Path, data_path: Path) -> ResearchExperimentJob:
    output_parent.mkdir(parents=True, exist_ok=True)
    return ResearchExperimentJob(
        job_id="experiment-job",
        generation_id="generation-000",
        manifest_payload={
            "campaign_id": "campaign-real",
            "data": {
                "calendar": "research-calendar",
                "checked_paths": [str(data_path)],
                "dataset_id": "research-metals-1m",
                "end": "2026-01-02T00:03:00+00:00",
                "start": "2026-01-02T00:00:00+00:00",
                "timeframe": "1m",
            },
            "run": {
                "created_at": "2026-05-26T00:00:00+00:00",
                "id": "experiment-job",
                "owner": "research",
                "question": "research experiment acceptance",
            },
            "strategy": {
                "id": "metals_research_momentum",
                "source_module": "strategies.research.metals_research_momentum",
                "target_module": "strategies.production.metals_research_momentum",
            },
            "backtest_pipeline": {"backtest_config_path": str(data_path.with_suffix(".yaml"))},
        },
        output_root=output_parent / "runner-output",
        trials=(
            {
                "family": "momentum",
                "parameters": {"lookback": 4, "threshold": 0.1},
                "trial_id": "trial-accepted",
            },
        ),
    )


def _write_bars(tmp_path: Path) -> Path:
    path = tmp_path / "research-bars.csv"
    path.write_text(
        "\n".join(
            [
                "timestamp,close",
                "2026-01-02T00:00:00+00:00,100.0",
                "2026-01-02T00:01:00+00:00,100.5",
                "2026-01-02T00:02:00+00:00,101.0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.with_suffix(".yaml").write_text(
        "\n".join(
            [
                "mode: backtest",
                "start: '2026-01-02T00:00:00+00:00'",
                "end: '2026-01-02T00:03:00+00:00'",
                "cost_model:",
                "  fixed_commission_per_contract: '0'",
                "  slippage_bps: '0'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _patch_backtest_pipeline_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeBacktestPipelineRunner:
        def run(self, job: Any) -> tuple[OptimizationResult, ...]:
            run_dir = job.output_root / "run-0000"
            run_dir.mkdir(parents=True)
            manifest_path = run_dir / "manifest.json"
            artifacts = {
                "equity_curve": {"rows": 3, "sha256": "sha256:equity"},
                "fills": {"rows": 42, "sha256": "sha256:fills"},
                "statistics": {"rows": 1, "sha256": "sha256:statistics"},
                "trade_ledger": {"rows": 42, "sha256": "sha256:trade-ledger"},
            }
            manifest_path.write_text(
                json.dumps(
                    {
                        "artifacts": artifacts,
                        "dataset_metadata": [{"dataset_id": "test"}],
                        "initial_cash": "1000000",
                        "manifest_hash": "sha256:research-backtest-manifest",
                        "metrics": {},
                        "statistics": {
                            "avg_gross_exposure": "0.5",
                            "max_drawdown": "0.10",
                            "profit_factor": "1.40",
                            "sharpe_ratio": "1.25",
                            "total_commission": "0",
                            "total_return": "0.12",
                            "total_slippage": "0",
                        },
                        "statistics_hash": "sha256:statistics",
                    }
                ),
                encoding="utf-8",
            )
            return (
                OptimizationResult(
                    parameters=dict(next(iter(job.parameter_grid))),
                    manifest_path=manifest_path,
                    manifest_hash="sha256:research-backtest-manifest",
                    objective_value=Decimal("1.25"),
                ),
            )

    monkeypatch.setattr(experiment_runner, "BacktestPipelineRunner", FakeBacktestPipelineRunner)
    # QTS-FINAL-011 moved the validation-rerun invocation into trial_helpers
    monkeypatch.setattr(trial_helpers, "BacktestPipelineRunner", FakeBacktestPipelineRunner)
