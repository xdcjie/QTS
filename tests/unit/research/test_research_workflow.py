from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from qts.research.optimizer import WalkForwardPlan, WalkForwardSplit
from qts.research.workflow import (
    ResearchWorkflowConfig,
    ResearchWorkflowRunner,
)


def _write_workflow(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "workflow.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_workflow_config_loads_steps_and_rejects_trading_promotion_keys(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: momentum-review
steps:
  - id: discover
    kind: factor_candidates
    query: equity momentum
    max_results: 3
""",
    )

    config = ResearchWorkflowConfig.from_yaml(workflow_path)

    assert config.workflow_config_path == workflow_path
    assert config.workflow_id == "momentum-review"
    assert [(step.step_id, step.kind) for step in config.steps] == [
        ("discover", "factor_candidates")
    ]
    assert config.steps[0].payload["query"] == "equity momentum"

    forbidden_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: unsafe-review
steps:
  - id: unsafe
    kind: factor_candidates
    query: equity momentum
    generate_code: true
""",
    )

    with pytest.raises(ValueError, match="forbidden workflow key: generate_code"):
        ResearchWorkflowConfig.from_yaml(forbidden_path)


def test_workflow_config_rejects_unknown_step_kind(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: unknown-kind
steps:
  - id: live
    kind: live
""",
    )

    with pytest.raises(ValueError, match="unsupported workflow step kind: live"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_review_gate_blocks_later_steps_when_required_status_is_missing(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: blocked-review
steps:
  - id: accepted-review
    kind: factor_review_gate
    status: accepted
    min_count: 1
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
""",
    )
    session = _FakeSession(accepted_specs=())

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "blocked"
    assert [(step.step_id, step.status) for step in result.steps] == [
        ("accepted-review", "blocked")
    ]
    assert session.backtest_calls == []


def test_review_gate_cannot_continue_into_backtest_when_blocked(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: hard-stop-review
steps:
  - id: accepted-review
    kind: factor_review_gate
    status: accepted
    min_count: 1
    on_fail: continue
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
""",
    )
    session = _FakeSession(accepted_specs=())

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "blocked"
    assert [(step.step_id, step.status) for step in result.steps] == [
        ("accepted-review", "blocked")
    ]
    assert session.backtest_calls == []


def test_workflow_config_rejects_internal_implementation_gate_modules(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: forbidden-implementation
steps:
  - id: implementation
    kind: implementation_gate
    required_modules:
      - qts.runtime.session
    required_strategy: qts.backtest.pipeline:BacktestPipeline
""",
    )

    with pytest.raises(ValueError, match="implementation_gate cannot require internal module"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_module_delegates_backtest_without_importing_pipeline_directly() -> None:
    source = Path("backend/src/qts/research/workflow.py").read_text(encoding="utf-8")

    assert "qts.backtest" not in source
    assert "BacktestPipeline" not in source
    assert "BacktestPipelineRunner" not in source


def test_runner_delegates_backtest_and_optimize_to_research_session(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: executable-evidence
steps:
  - id: accepted-review
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
  - id: optimize
    kind: optimize
    objective_metric: total_return
    parameters:
      entry_bar: [1, 2]
      quantity: ["1", "2"]
""",
    )
    session = _FakeSession(accepted_specs=("momentum",))

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert [step.status for step in result.steps] == ["passed", "passed", "passed", "passed"]
    assert session.backtest_calls == [{"quantity": "2"}]
    assert session.optimize_calls == [
        {
            "objective_metric": "total_return",
            "output_root": None,
            "parameters": {
                "entry_bar": [1, 2],
                "quantity": ["1", "2"],
            },
        }
    ]
    assert result.steps[2].outputs["manifest_path"] == "runs/backtest/manifest.json"
    assert result.steps[3].outputs["ranked_results"][0]["objective_value"] == "1.2"


def test_runner_runs_walk_forward_validation_for_top_optimizer_candidates(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: walk-forward-evidence
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    output_root: optimizer-output
    parameters:
      alpha: ["1", "2"]
    validation:
      walk_forward:
        top_n: 1
        output_root: walk-forward-output
        summary_output: walk-forward-summary.json
        robustness:
          phases: [test]
          min_windows: 1
          max_losing_windows: 0
          min_window_pnl_usd: "0"
          min_total_pnl_usd: "10"
        splits:
          - name: split-001
            train_start: 2026-01-01
            train_end: 2026-03-01
            test_start: 2026-04-01
            test_end: 2026-05-01
""",
    )
    session = _FakeSession(accepted_specs=())

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert session.walk_forward_calls == [
        {
            "capital_metric_config": None,
            "candidate_parameters": ({"entry_bar": 1, "quantity": "2"},),
            "constraint_count": 0,
            "objective_metric": "sharpe_ratio",
            "output_root": tmp_path / "walk-forward-output",
            "splits": (
                {
                    "name": "split-001",
                    "test_end": "2026-05-01",
                    "test_start": "2026-04-01",
                    "train_end": "2026-03-01",
                    "train_start": "2026-01-01",
                },
            ),
        }
    ]
    outputs = result.steps[0].outputs
    assert outputs["walk_forward_validation"] == {
        "run_count": 2,
        "window_count": 2,
        "windows": [
            {
                "accepted_count": 1,
                "accepted_runs": (
                    {
                        "capital_metrics": {"pnl_usd": "25"},
                        "objective_value": "1.2",
                    },
                ),
                "end": "2026-05-01",
                "phase": "test",
                "rejected_count": 0,
                "rejections": (),
                "run_count": 1,
                "split_name": "split-001",
                "start": "2026-04-01",
            }
        ],
    }
    assert outputs["walk_forward_robustness"] == {
        "accepted": True,
        "metrics": {
            "losing_window_count": 0,
            "min_window_best_objective": "1.2",
            "min_window_pnl_usd": "25",
            "total_pnl_usd": "25",
            "window_count": 1,
        },
        "reasons": (),
    }
    summary_output = tmp_path / "walk-forward-summary.json"
    assert outputs["walk_forward_validation_output"] == str(summary_output)
    assert summary_output.exists()
    assert "robustness" in summary_output.read_text(encoding="utf-8")


def test_vwap_workflow_uses_multi_window_top_n_walk_forward_validation() -> None:
    config = ResearchWorkflowConfig.from_yaml(
        Path("configs/research/workflows/vwap_factor_search.yaml")
    )
    risk_reward = next(step for step in config.steps if step.step_id == "risk-reward")

    walk_forward = risk_reward.payload["validation"]["walk_forward"]

    assert walk_forward["top_n"] == 3
    assert [split["name"] for split in walk_forward["splits"]] == [
        "regime-2024-summer-to-q4",
        "regime-2025-q1-to-summer",
        "regime-2025-late-summer-to-winter",
    ]
    assert walk_forward["robustness"] == {
        "phases": ["test"],
        "min_windows": 3,
        "max_losing_windows": 0,
        "min_window_pnl_usd": "0",
        "min_window_best_objective": "0",
        "min_total_pnl_usd": "1",
    }
    plan = WalkForwardPlan(
        tuple(
            WalkForwardSplit(
                name=str(split["name"]),
                train_start=split["train_start"],
                train_end=split["train_end"],
                test_start=split["test_start"],
                test_end=split["test_end"],
            )
            for split in walk_forward["splits"]
        )
    )
    assert len(plan.splits) == 3


def test_workflow_runs_factor_evaluation_step(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: evaluation-only
steps:
  - id: evaluate
    kind: factor_evaluation
    factor_name: momentum
    factor_version: "1"
    snapshots:
      - as_of: 2026-01-02
        factor_scores: scores-2026-01-02.csv
        forward_returns: returns-2026-01-02.csv
      - as_of: 2026-01-03
        factor_scores: scores-2026-01-03.csv
        forward_returns: returns-2026-01-03.csv
    output_dir: evaluation-output
""",
    )

    session = _FakeSession(
        accepted_specs=(),
        evaluation_output_dir=tmp_path / "evaluation-output",
    )

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert [step.status for step in result.steps] == ["passed"]
    outputs = result.steps[0].outputs
    assert outputs["factor_name"] == "momentum"
    assert outputs["factor_version"] == "1"
    assert outputs["snapshot_count"] == 2
    assert outputs["artifact_paths"] == [
        str(session._evaluation_output_dir / "2026-01-02.json"),
        str(session._evaluation_output_dir / "2026-01-03.json"),
    ]
    assert "factor_evaluation" in result.steps[0].kind
    assert session.evaluate_factor_calls == [
        {
            "factor_name": "momentum",
            "factor_version": "1",
            "bucket_count": 5,
            "output_dir": session._evaluation_output_dir,
            "snapshot_count": 2,
        }
    ]


def test_runner_generates_research_report_after_execution_steps(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: reported-run
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
  - id: report
    kind: research_report
    output_root: run-reports
    output_path: workflow-run.md
""",
    )

    session = _FakeSession(
        accepted_specs=("momentum",),
        evaluation_output_dir=tmp_path / "evaluation-output",
    )
    config = ResearchWorkflowConfig.from_yaml(workflow_path)

    result = ResearchWorkflowRunner().run(session, config)

    assert result.status == "completed"
    assert [step.kind for step in result.steps] == [
        "factor_review_gate",
        "implementation_gate",
        "research_report",
    ]
    assert result.steps[2].status == "passed"
    report_path = result.steps[2].outputs["report_path"]
    assert report_path == str(config.resolve_path("run-reports") / "workflow-run.md")
    assert Path(report_path).exists()
    assert "Research Workflow Report" in Path(report_path).read_text(encoding="utf-8")


def test_implementation_gate_blocks_missing_modules_without_generating_code(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: missing-implementation
steps:
  - id: implementation
    kind: implementation_gate
    required_modules:
      - qts.factors.not_a_real_factor_module
""",
    )

    result = ResearchWorkflowRunner().run(
        _FakeSession(accepted_specs=()),
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "blocked"
    assert result.steps[0].outputs["missing_modules"] == ["qts.factors.not_a_real_factor_module"]


class _FakeSession:
    def __init__(
        self,
        *,
        accepted_specs: tuple[str, ...],
        evaluation_output_dir: Path | None = None,
    ) -> None:
        self._accepted_specs = accepted_specs
        self.backtest_calls: list[dict[str, object]] = []
        self.optimize_calls: list[dict[str, object]] = []
        self.walk_forward_calls: list[dict[str, object]] = []
        self.evaluate_factor_calls: list[dict[str, object]] = []
        self._evaluation_output_dir: Path = (
            evaluation_output_dir
            if evaluation_output_dir is not None
            else Path("evaluation-output")
        )

    def list_factor_specs_by_status(self, status: str) -> tuple[SimpleNamespace, ...]:
        if status != "accepted":
            return ()
        return tuple(SimpleNamespace(name=name) for name in self._accepted_specs)

    def run_backtest(self, *, strategy_params: dict[str, object] | None = None) -> object:
        self.backtest_calls.append(dict(strategy_params or {}))
        return SimpleNamespace(
            manifest_path=Path("runs/backtest/manifest.json"),
            processed_bars=5,
            trading_bars=5,
        )

    def optimize(
        self,
        *,
        parameters: dict[str, list[object]],
        objective_metric: str | None = None,
        output_root: Path | None = None,
    ) -> tuple[object, ...]:
        self.optimize_calls.append(
            {
                "parameters": parameters,
                "objective_metric": objective_metric,
                "output_root": output_root,
            }
        )
        return (
            SimpleNamespace(
                parameters={"entry_bar": 1, "quantity": "2"},
                manifest_path=Path("runs/optimizer/run-0000/manifest.json"),
                manifest_hash="abc123",
                objective_value=Decimal("1.2"),
            ),
        )

    def validate_optimizer_walk_forward(
        self,
        *,
        candidate_parameters: tuple[dict[str, object], ...],
        constraints: tuple[object, ...] = (),
        capital_metric_config: dict[str, object] | None = None,
        objective_metric: str | None = None,
        output_root: Path | None = None,
        plan: Any,
    ) -> object:
        self.walk_forward_calls.append(
            {
                "candidate_parameters": candidate_parameters,
                "capital_metric_config": capital_metric_config,
                "constraint_count": len(constraints),
                "objective_metric": objective_metric,
                "output_root": output_root,
                "splits": plan.to_metadata(),
            }
        )
        windows = [
            {
                "accepted_count": 1,
                "accepted_runs": (
                    {
                        "capital_metrics": {"pnl_usd": "25"},
                        "objective_value": "1.2",
                    },
                ),
                "end": "2026-05-01",
                "phase": "test",
                "rejected_count": 0,
                "rejections": (),
                "run_count": 1,
                "split_name": "split-001",
                "start": "2026-04-01",
            }
        ]
        return SimpleNamespace(
            windows=tuple(windows),
            to_payload=lambda: {
                "run_count": 2,
                "window_count": 2,
                "windows": windows,
            },
        )

    def evaluate_factor(
        self,
        *,
        factor_name: str,
        factor_version: str,
        snapshots: tuple[dict[str, object], ...] | list[dict[str, object]],
        bucket_count: int = 5,
        output_dir: Path | None = None,
    ) -> tuple[SimpleNamespace, ...]:
        output_dir = output_dir or self._evaluation_output_dir
        output_dir = Path(output_dir)
        self._evaluation_output_dir = output_dir
        self.evaluate_factor_calls.append(
            {
                "factor_name": factor_name,
                "factor_version": factor_version,
                "bucket_count": bucket_count,
                "output_dir": output_dir,
                "snapshot_count": len(snapshots),
            }
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[SimpleNamespace] = []
        for index, snapshot in enumerate(snapshots, start=1):
            artifact_path = output_dir / f"{snapshot['as_of']}.json"
            artifact_path.write_text(f'{{"snapshot": {index}}}\\n', encoding="utf-8")
            latest = index == len(snapshots)
            metrics = SimpleNamespace(
                rank_ic="0.2",
                long_short_spread="0.1",
                coverage="0.75",
                turnover="0.25" if latest else None,
                scored_count=2,
                return_count=2,
            )
            results.append(
                SimpleNamespace(
                    artifact_path=artifact_path,
                    result=SimpleNamespace(metrics=metrics),
                )
            )
        return tuple(results)
