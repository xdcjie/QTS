"""Integration tests for the research workflow CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from qts.research import ExperimentStore, FactorSpecDrafter, ResearchSession
from qts.research.factor_discovery import FactorIdea
from qts.research.factor_evaluation import (
    FactorEvaluationArtifactWriter,
    FactorEvaluationMetrics,
    FactorEvaluationResult,
)

from tests.integration.test_research_session_facade import _write_research_session_config


def _write_evaluation(
    writer: FactorEvaluationArtifactWriter,
    as_of: date,
    *,
    rank_ic: str,
    spread: str,
    coverage: str,
) -> Path:
    return writer.write(
        FactorEvaluationResult(
            as_of=as_of,
            factor_name="momentum",
            factor_version="1",
            metrics=FactorEvaluationMetrics(
                rank_ic=Decimal(rank_ic),
                long_short_spread=Decimal(spread),
                coverage=Decimal(coverage),
                turnover=None,
                scored_count=3,
                return_count=3,
                missing_symbols=(),
            ),
        )
    )


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/run_research.py", *args],
        capture_output=True,
        text=True,
        check=False,
        env={
            "PYTHONPATH": f"backend/src{os.pathsep}.",
            "QTS_API_DEV_TOKENS": "1",
            "PATH": os.environ.get("PATH", ""),
        },
    )


def _write_workflow(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "workflow.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def _accept_factor_spec(config_path: Path) -> None:
    session = ResearchSession.from_yaml(config_path)
    spec = FactorSpecDrafter().draft(
        FactorIdea(
            idea_id="fixture:momentum",
            source="fixture",
            external_id="momentum",
            title="Momentum factor in equity bars",
            abstract="A momentum signal for research review.",
            url="https://example.test/momentum",
            year=2026,
            authors=("Researcher",),
            citation_count=10,
        )
    )
    session.save_factor_spec(spec)
    session.review_factor_spec(
        spec.name,
        decision="accepted",
        reviewer="researcher@example.com",
    )


def _write_factor_snapshot_inputs(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path]:
    scores_day1 = tmp_path / "scores_2026_01_02.csv"
    scores_day1.write_text(
        "\n".join(
            [
                "symbol,value",
                "AAPL,0.9",
                "MSFT,0.7",
                "NFLX,0.1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    returns_day1 = tmp_path / "returns_2026_01_02.csv"
    returns_day1.write_text(
        "\n".join(
            [
                "symbol,forward_return",
                "AAPL,0.04",
                "MSFT,0.01",
                "NFLX,0.00",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    scores_day2 = tmp_path / "scores_2026_01_03.json"
    scores_day2.write_text(
        json.dumps({"AAPL": 0.4, "MSFT": 0.9, "NFLX": 0.6}, sort_keys=True),
        encoding="utf-8",
    )
    returns_day2 = tmp_path / "returns_2026_01_03.json"
    returns_day2.write_text(
        json.dumps({"AAPL": 0.01, "MSFT": -0.03, "NFLX": 0.05}, sort_keys=True),
        encoding="utf-8",
    )
    return scores_day1, returns_day1, scores_day2, returns_day2


def test_research_cli_records_factor_tearsheet_and_lists_runs(tmp_path: Path) -> None:
    config_path = _write_research_session_config(tmp_path)
    writer = FactorEvaluationArtifactWriter(tmp_path / "factor-evaluations")
    first = _write_evaluation(
        writer,
        date(2026, 1, 2),
        rank_ic="0.1",
        spread="0.01",
        coverage="0.8",
    )
    second = _write_evaluation(
        writer,
        date(2026, 1, 3),
        rank_ic="0.3",
        spread="0.03",
        coverage="0.9",
    )

    result = _run_cli(
        "--config",
        str(config_path),
        "factor-tearsheet",
        str(second),
        str(first),
        "--experiment-id",
        "momentum-tearsheet",
        "--dataset-id",
        "fixture-bars",
    )

    assert result.returncode == 0, result.stderr
    assert "tearsheet_path=" in result.stdout
    assert "manifest_path=" in result.stdout
    assert "store_index=" in result.stdout
    output_lines = dict(line.split("=", maxsplit=1) for line in result.stdout.splitlines())
    manifest_payload = json.loads(Path(output_lines["manifest_path"]).read_text(encoding="utf-8"))
    manifest_artifact_path = next(iter(manifest_payload["artifact_paths_by_hash"].values()))
    assert output_lines["tearsheet_path"] == manifest_artifact_path
    store = ExperimentStore(tmp_path / "research-store")
    records = store.list_runs()
    assert [record.experiment_id for record in records] == ["momentum-tearsheet"]
    assert records[0].metrics["mean_rank_ic"] == "0.2"

    runs = _run_cli("--config", str(config_path), "runs", "--sort-by", "mean_rank_ic")

    assert runs.returncode == 0, runs.stderr
    assert "experiment_id" in runs.stdout
    assert "momentum-tearsheet" in runs.stdout
    assert "0.2" in runs.stdout


def test_research_cli_runs_command_lists_unsorted_store_records(tmp_path: Path) -> None:
    config_path = _write_research_session_config(tmp_path)
    store = ExperimentStore(tmp_path / "research-store")
    writer = FactorEvaluationArtifactWriter(tmp_path / "factor-evaluations")
    artifact = _write_evaluation(
        writer,
        date(2026, 1, 2),
        rank_ic="0.1",
        spread="0.01",
        coverage="0.8",
    )
    result = _run_cli(
        "--config",
        str(config_path),
        "factor-tearsheet",
        str(artifact),
        "--experiment-id",
        "single-snapshot",
    )
    assert result.returncode == 0, result.stderr
    assert store.list_runs()[0].experiment_id == "single-snapshot"

    listed = _run_cli("--config", str(config_path), "runs")

    assert listed.returncode == 0, listed.stderr
    assert "single-snapshot" in listed.stdout


def test_research_cli_workflow_blocks_when_review_gate_fails(tmp_path: Path) -> None:
    config_path = _write_research_session_config(tmp_path)
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: blocked-review
steps:
  - id: review
    kind: factor_review_gate
    status: accepted
    min_count: 1
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
""",
    )

    result = _run_cli("--config", str(config_path), "workflow", str(workflow_path))

    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["steps"][0]["status"] == "blocked"
    assert not (tmp_path / "research-runs" / "single-run").exists()


def test_research_cli_workflow_runs_only_selected_step(tmp_path: Path) -> None:
    config_path = _write_research_session_config(tmp_path)
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: selected-cli-step
steps:
  - id: implementation
    kind: implementation_gate
    required_modules:
      - examples.strategies.gc_si_momentum
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
      entry_bar: 1
""",
    )

    result = _run_cli(
        "--config",
        str(config_path),
        "workflow",
        str(workflow_path),
        "--step",
        "implementation",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "completed"
    assert [(step["id"], step["status"]) for step in payload["steps"]] == [
        ("implementation", "passed")
    ]
    assert not (tmp_path / "research-runs" / "single-run").exists()


def test_research_cli_workflow_rejects_conflicting_step_selection(tmp_path: Path) -> None:
    config_path = _write_research_session_config(tmp_path)
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: conflicting-selection
steps:
  - id: implementation
    kind: implementation_gate
    required_modules:
      - examples.strategies.gc_si_momentum
""",
    )

    result = _run_cli(
        "--config",
        str(config_path),
        "workflow",
        str(workflow_path),
        "--step",
        "implementation",
        "--from-step",
        "implementation",
    )

    assert result.returncode == 2
    assert "--step cannot be combined with --from-step or --to-step" in result.stderr


def test_research_cli_workflow_runs_backtest_and_optimize_after_gates_pass(
    tmp_path: Path,
) -> None:
    config_path = _write_research_session_config(tmp_path)
    _accept_factor_spec(config_path)
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: passing-review
steps:
  - id: review
    kind: factor_review_gate
    status: accepted
    min_count: 1
  - id: implementation
    kind: implementation_gate
    required_modules:
      - examples.strategies.gc_si_momentum
    required_strategy: examples.strategies.gc_si_momentum:GcSiMomentumStrategy
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
      entry_bar: 1
  - id: optimize
    kind: optimize
    objective_metric: total_return
    capital_metrics:
      margin_proxy: "1000"
    validation:
      constraints:
        - metric: pnl_usd
          operator: ">="
          threshold: "1"
    parameters:
      entry_bar: [1, 2]
      quantity: ["1", "2"]
""",
    )

    result = _run_cli("--config", str(config_path), "workflow", str(workflow_path))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "completed"
    assert [step["status"] for step in payload["steps"]] == [
        "passed",
        "passed",
        "passed",
        "passed",
    ]
    backtest_outputs = payload["steps"][2]["outputs"]
    optimize_outputs = payload["steps"][3]["outputs"]
    assert Path(backtest_outputs["manifest_path"]).exists()
    assert optimize_outputs["run_count"] == 4
    assert Path(optimize_outputs["ranked_results"][0]["manifest_path"]).exists()
    assert optimize_outputs["ranked_results"][0]["capital_metrics"]["pnl_usd"] != "0"
    assert optimize_outputs["validation_summary"]["accepted_count"] >= 1
    assert (
        optimize_outputs["validation_summary"]["accepted_runs"][0]["capital_metrics"][
            "return_on_margin_proxy"
        ]
        != "0"
    )


def test_research_cli_workflow_optimize_matches_direct_research_session_results(
    tmp_path: Path,
) -> None:
    config_path = _write_research_session_config(tmp_path)
    workflow_path = _write_workflow(
        tmp_path,
        f"""
version: 1
workflow_id: optimize-consistency
steps:
  - id: optimize
    kind: optimize
    objective_metric: total_return
    output_root: {tmp_path / "workflow-optimizer"}
    parameters:
      entry_bar: [1, 2]
      quantity: ["1", "2"]
""",
    )

    result = _run_cli("--config", str(config_path), "workflow", str(workflow_path))
    direct_results = ResearchSession.from_yaml(config_path).optimize(
        parameters={
            "entry_bar": [1, 2],
            "quantity": ["1", "2"],
        },
        objective_metric="total_return",
        output_root=tmp_path / "direct-optimizer",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    workflow_ranked = payload["steps"][0]["outputs"]["ranked_results"]

    assert [
        (
            item["parameters"],
            item["objective_value"],
            _research_result_metrics(Path(item["manifest_path"])),
        )
        for item in workflow_ranked
    ] == [
        (
            dict(item.parameters),
            str(item.objective_value),
            _research_result_metrics(item.manifest_path),
        )
        for item in direct_results
    ]


def test_canonical_vwap_workflow_optimize_matches_direct_research_session_metrics(
    tmp_path: Path,
) -> None:
    if (
        not Path("historical/data/gc.csv").exists()
        or not Path("historical/chains/GC.json").exists()
    ):
        pytest.skip("canonical VWAP research data is not available")
    workflow_path = _write_workflow(
        tmp_path,
        f"""
version: 1
workflow_id: vwap-path-equivalence
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    output_root: {tmp_path / "workflow-optimizer"}
    parameters:
      time_window: [evening_18_22]
      target_quantity: ["3"]
      min_volume_ratio: ["1.2"]
      pullback_touch_atr_below: ["0.15"]
      max_pullback_break_atr: ["1.0"]
      stop_atr_multiple: ["1.0"]
      target_r_multiple: ["2.0"]
      factor_filters:
        - []
""",
    )

    result = _run_cli(
        "--config",
        "configs/research/vwap.yaml",
        "workflow",
        str(workflow_path),
    )
    direct_results = ResearchSession.from_yaml(Path("configs/research/vwap.yaml")).optimize(
        parameters={
            "time_window": ["evening_18_22"],
            "target_quantity": ["3"],
            "min_volume_ratio": ["1.2"],
            "pullback_touch_atr_below": ["0.15"],
            "max_pullback_break_atr": ["1.0"],
            "stop_atr_multiple": ["1.0"],
            "target_r_multiple": ["2.0"],
            "factor_filters": [[]],
        },
        objective_metric="sharpe_ratio",
        output_root=tmp_path / "direct-optimizer",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    workflow_ranked = payload["steps"][0]["outputs"]["ranked_results"]

    assert [
        (
            item["parameters"],
            item["objective_value"],
            _research_result_metrics(Path(item["manifest_path"])),
        )
        for item in workflow_ranked
    ] == [
        (
            dict(item.parameters),
            str(item.objective_value),
            _research_result_metrics(item.manifest_path),
        )
        for item in direct_results
    ]


def _research_result_metrics(manifest_path: Path) -> dict[str, str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    return {
        "max_drawdown": str(metrics["max_drawdown"]),
        "sharpe_ratio": str(metrics["sharpe_ratio"]),
        "total_return": str(metrics["total_return"]),
        "total_trades": str(metrics["total_trades"]),
    }


def test_research_cli_workflow_runs_full_evidence_pipeline(
    tmp_path: Path,
) -> None:
    config_path = _write_research_session_config(tmp_path)
    _accept_factor_spec(config_path)
    scores_1, returns_1, scores_2, returns_2 = _write_factor_snapshot_inputs(tmp_path)
    evaluation_root = tmp_path / "factor-evaluations"
    report_root = tmp_path / "workflow-reports"
    workflow_path = _write_workflow(
        tmp_path,
        f"""
version: 1
workflow_id: full-evidence
steps:
  - id: review
    kind: factor_review_gate
    status: accepted
    min_count: 1
  - id: implementation
    kind: implementation_gate
    required_modules:
      - examples.strategies.gc_si_momentum
    required_strategy: examples.strategies.gc_si_momentum:GcSiMomentumStrategy
  - id: evaluate
    kind: factor_evaluation
    factor_name: momentum
    factor_version: "1"
    output_dir: {evaluation_root}
    snapshots:
      - as_of: 2026-01-02
        factor_scores: {scores_1}
        forward_returns: {returns_1}
      - as_of: 2026-01-03
        factor_scores: {scores_2}
        forward_returns: {returns_2}
  - id: tearsheet
    kind: factor_tearsheet
    experiment_id: momentum-full
    artifact_paths:
      - {evaluation_root}/2026-01-02-momentum-1.json
      - {evaluation_root}/2026-01-03-momentum-1.json
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
      entry_bar: 1
  - id: optimize
    kind: optimize
    objective_metric: total_return
    parameters:
      entry_bar: [1, 2]
      quantity: ["1", "2"]
  - id: report
    kind: research_report
    output_root: {report_root}
    output_path: workflow-report.md
""",
    )

    result = _run_cli("--config", str(config_path), "workflow", str(workflow_path))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "completed"
    assert [step["status"] for step in payload["steps"]] == [
        "passed",
        "passed",
        "passed",
        "passed",
        "passed",
        "passed",
        "passed",
    ]
    factor_eval_outputs = payload["steps"][2]["outputs"]
    assert factor_eval_outputs["snapshot_count"] == 2
    assert len(factor_eval_outputs["artifact_paths"]) == 2
    report_path = payload["steps"][-1]["outputs"]["report_path"]
    report_text = Path(report_path).read_text(encoding="utf-8")
    assert "Research Workflow Report" in report_text
    assert "factor_evaluation" in report_text
    assert "factor_tearsheet" in report_text


def test_research_cli_workflow_blocks_evidence_steps_after_failed_implementation_gate(
    tmp_path: Path,
) -> None:
    config_path = _write_research_session_config(tmp_path)
    _accept_factor_spec(config_path)
    scores_1, returns_1, scores_2, returns_2 = _write_factor_snapshot_inputs(tmp_path)
    workflow_path = _write_workflow(
        tmp_path,
        f"""
version: 1
workflow_id: blocked-after-implementation
steps:
  - id: review
    kind: factor_review_gate
    status: accepted
    min_count: 1
  - id: implementation
    kind: implementation_gate
    required_modules:
      - qts.factors.not_a_real_factor_module
  - id: evaluate
    kind: factor_evaluation
    factor_name: momentum
    factor_version: "1"
    snapshots:
      - as_of: 2026-01-02
        factor_scores: {scores_1}
        forward_returns: {returns_1}
      - as_of: 2026-01-03
        factor_scores: {scores_2}
        forward_returns: {returns_2}
  - id: report
    kind: research_report
    output_path: blocked-report.md
""",
    )

    result = _run_cli("--config", str(config_path), "workflow", str(workflow_path))

    assert result.returncode == 1, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["steps"][1]["kind"] == "implementation_gate"
    assert payload["steps"][1]["status"] == "blocked"
    assert len(payload["steps"]) == 2
