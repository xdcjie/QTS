from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from qts.research import ResearchSessionConfig
from qts.research.workflow import (
    ResearchWorkflowConfig,
    ResearchWorkflowRunner,
    ResearchWorkflowStepConfig,
)
from qts.runtime.config import BacktestRuntimeConfig

from strategies.research.vwap_factor_research import VwapFactorResearchConfig


def _write_workflow(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "workflow.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def _assert_margin_sized_quantities(
    *,
    quantities: tuple[str, ...],
    initial_cash: Decimal,
    margin_proxy: Decimal,
) -> None:
    for quantity in quantities:
        margin_ratio = Decimal(quantity) * margin_proxy / initial_cash
        assert Decimal("0.30") <= margin_ratio <= Decimal("0.50")


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


def test_workflow_rejects_holdout_in_optimizer_objective(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: holdout-objective
periods:
  selection_2020_2022:
    start: "2020-01-01"
    end: "2022-01-01"
    role: selection
  holdout_2024_2026:
    start: "2024-01-01"
    end: "2026-01-01"
    role: holdout_report_only
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      quantity: ["1", "2"]
    validation:
      failure_window_veto:
        top_n: 1
        constraints:
          - metric: pnl_usd
            operator: ">"
            threshold: "0"
        windows:
          - name: differently_named_2024_window
            start: "2024-01-01"
            end: "2025-01-01"
""",
    )

    with pytest.raises(ValueError, match="report-only period.*failure_window_veto.windows"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_true_oos_in_candidate_selection(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: true-oos-selection
periods:
  selection_2020_2022:
    start: "2020-01-01"
    end: "2022-01-01"
    role: selection
  true_oos_after_2026_01_01:
    start: "2026-01-01"
    end: "2027-01-01"
    role: true_oos_report_only
steps:
  - id: scan
    kind: portfolio_volatility_managed_scan
    periods: [selection_2020_2022, true_oos_after_2026_01_01]
    selection_periods: [true_oos_after_2026_01_01]
    parameter_grid:
      lookback_days: [1]
    candidates:
      - name: base
        period_manifests:
          selection_2020_2022: base-selection.manifest.json
          true_oos_after_2026_01_01: base-oos.manifest.json
""",
    )

    with pytest.raises(ValueError, match="true_oos_report_only.*selection_periods"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_period_sensitive_decisions_without_declared_periods(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: missing-period-policy
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      alpha: ["1"]
    validation:
      failure_window_veto:
        top_n: 1
        constraints:
          - metric: pnl_usd
            operator: ">"
            threshold: "0"
        windows:
          - name: failure-2024
            start: "2024-01-01"
            end: "2025-01-01"
""",
    )

    with pytest.raises(ValueError, match="declared periods.*failure_window_veto"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_config_direct_construction_enforces_period_roles(tmp_path: Path) -> None:
    step = ResearchWorkflowStepConfig(
        step_id="matrix",
        kind="backtest_matrix",
        payload={
            "candidates": [{"name": "base", "strategy_params": {}}],
            "output_root": "matrix-runs",
            "periods": [
                {
                    "end": "2022-01-01",
                    "name": "selection_2020_2022",
                    "role": "selection",
                    "start": "2020-01-01",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="declared periods are required.*backtest_matrix"):
        ResearchWorkflowConfig(
            workflow_config_path=tmp_path / "workflow.yaml",
            workflow_id="direct-period-bypass",
            periods=(),
            steps=(step,),
        )


def test_workflow_config_direct_construction_ignores_payload_kind_bypass(
    tmp_path: Path,
) -> None:
    step = ResearchWorkflowStepConfig(
        step_id="matrix",
        kind="backtest_matrix",
        payload={
            "candidates": [{"name": "base", "strategy_params": {}}],
            "kind": "research_report",
            "output_root": "matrix-runs",
            "periods": [
                {
                    "end": "2022-01-01",
                    "name": "selection_2020_2022",
                    "role": "selection",
                    "start": "2020-01-01",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="declared periods are required.*backtest_matrix"):
        ResearchWorkflowConfig(
            workflow_config_path=tmp_path / "workflow.yaml",
            workflow_id="direct-kind-bypass",
            periods=(),
            steps=(step,),
        )


def test_workflow_rejects_scoring_backtest_matrix_period_without_declaration(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: missing-matrix-period-policy
steps:
  - id: matrix
    kind: backtest_matrix
    output_root: matrix-runs
    periods:
      - name: selection_2020_2022
        start: "2020-01-01"
        end: "2022-01-01"
        role: selection
    candidates:
      - name: base
        strategy_params: {}
""",
    )

    with pytest.raises(ValueError, match="declared periods are required.*backtest_matrix"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_backtest_matrix_period_without_role_or_declaration(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: untyped-matrix-period
steps:
  - id: matrix
    kind: backtest_matrix
    output_root: matrix-runs
    periods:
      - name: report_2025_2026
        start: "2025-01-01"
        end: "2026-01-01"
    candidates:
      - name: base
        strategy_params: {}
""",
    )

    with pytest.raises(ValueError, match="declared periods are required.*backtest_matrix"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_unknown_portfolio_score_period(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: unknown-score-period
periods:
  anchor:
    start: "2020-01-01"
    end: "2021-01-01"
    role: anchor
  validation:
    start: "2021-01-01"
    end: "2022-01-01"
    role: validation
steps:
  - id: scan
    kind: portfolio_ensemble_scan
    scan_name: unit
    periods: [anchor, validation]
    baseline_period: anchor
    post_periods: [undeclared_holdout]
    candidates: []
""",
    )

    with pytest.raises(ValueError, match="post_periods period undeclared_holdout is not declared"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_overlapping_declared_periods(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: overlapping-periods
periods:
  holdout_2024_2026:
    start: "2024-01-01"
    end: "2026-04-10"
    role: holdout_report_only
  true_oos_after_2026_01_01:
    start: "2026-01-01"
    end: null
    role: true_oos_report_only
steps:
  - id: report
    kind: research_report
""",
    )

    with pytest.raises(ValueError, match="overlaps previous period"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_validation_period_overlapping_holdout(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: validation-overlap
periods:
  validation_2022_2024:
    start: "2022-01-01"
    end: "2024-01-01"
    role: validation
  holdout_2024_2026:
    start: "2024-01-01"
    end: "2026-01-01"
    role: holdout_report_only
steps:
  - id: matrix
    kind: backtest_matrix
    periods:
      - name: disguised_validation
        start: "2022-01-01"
        end: "2025-01-01"
        role: validation
""",
    )

    with pytest.raises(ValueError, match="declared periods are required.*disguised_validation"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_named_report_period_redefining_declared_bounds(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: report-period-boundary-drift
periods:
  holdout_2024_2026:
    start: "2024-01-01"
    end: "2026-01-01"
    role: holdout_report_only
  true_oos_after_2026_01_01:
    start: "2026-01-01"
    end: null
    role: true_oos_report_only
steps:
  - id: matrix
    kind: backtest_matrix
    periods:
      - name: holdout_2024_2026
        start: "2024-01-01"
        end: "2026-04-10"
""",
    )

    with pytest.raises(ValueError, match="holdout_2024_2026.*declared boundaries"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_named_scoring_period_redefining_declared_bounds(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: scoring-period-boundary-drift
periods:
  selection_2020_2022:
    start: "2020-01-01"
    end: "2022-01-01"
    role: selection
steps:
  - id: matrix
    kind: backtest_matrix
    periods:
      - name: selection_2020_2022
        start: "2020-01-01"
        end: "2023-01-01"
        role: selection
""",
    )

    with pytest.raises(ValueError, match="selection_2020_2022.*declared boundaries"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_named_report_period_reclassifying_declared_role(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: report-period-role-drift
periods:
  holdout_2024_2026:
    start: "2024-01-01"
    end: "2026-01-01"
    role: holdout_report_only
steps:
  - id: matrix
    kind: backtest_matrix
    periods:
      - name: holdout_2024_2026
        start: "2024-01-01"
        end: "2026-01-01"
        role: validation
""",
    )

    with pytest.raises(ValueError, match="holdout_2024_2026.*declared role"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_walk_forward_robustness_on_holdout(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: walk-forward-holdout
periods:
  validation_2022_2023:
    start: "2022-01-01"
    end: "2023-01-01"
    role: validation
  holdout_2023_2026:
    start: "2023-01-01"
    end: "2026-04-10"
    role: holdout_report_only
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      alpha: ["1"]
    validation:
      walk_forward:
        robustness:
          phases: [test]
          min_windows: 1
        splits:
          - name: oos-decision
            train_start: "2010-06-06"
            train_end: "2023-01-01"
            test_start: "2023-01-01"
            test_end: "2026-04-10"
""",
    )

    with pytest.raises(ValueError, match="holdout_report_only.*walk_forward.splits"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_walk_forward_split_on_holdout_without_robustness(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: walk-forward-holdout-summary
periods:
  validation_2022_2023:
    start: "2022-01-01"
    end: "2023-01-01"
    role: validation
  holdout_2023_2026:
    start: "2023-01-01"
    end: "2026-04-10"
    role: holdout_report_only
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      alpha: ["1"]
    validation:
      walk_forward:
        splits:
          - name: oos-summary
            train_start: "2010-06-06"
            train_end: "2023-01-01"
            test_start: "2023-01-01"
            test_end: "2026-04-10"
""",
    )

    with pytest.raises(ValueError, match="holdout_report_only.*walk_forward.splits"):
        ResearchWorkflowConfig.from_yaml(workflow_path)


def test_workflow_rejects_walk_forward_train_robustness_on_holdout(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: walk-forward-train-holdout
periods:
  selection_2020_2021:
    start: "2020-01-01"
    end: "2021-01-01"
    role: selection
  holdout_2021_2022:
    start: "2021-01-01"
    end: "2022-01-01"
    role: holdout_report_only
  validation_2022_2023:
    start: "2022-01-01"
    end: "2023-01-01"
    role: validation
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      alpha: ["1"]
    validation:
      walk_forward:
        robustness:
          phases: [train]
          min_windows: 1
        splits:
          - name: train-decision
            train_start: "2021-01-01"
            train_end: "2022-01-01"
            test_start: "2022-01-01"
            test_end: "2023-01-01"
""",
    )

    with pytest.raises(ValueError, match="holdout_report_only.*walk_forward.splits"):
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


def test_runner_executes_only_selected_workflow_step(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: selected-step
steps:
  - id: review
    kind: factor_review_gate
    status: accepted
    min_count: 1
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
  - id: optimize
    kind: optimize
    objective_metric: total_return
    parameters:
      entry_bar: [1, 2]
      quantity: ["1"]
""",
    )
    session = _FakeSession(accepted_specs=())

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
        step_id="optimize",
    )

    assert result.status == "completed"
    assert [(step.step_id, step.kind, step.status) for step in result.steps] == [
        ("optimize", "optimize", "passed")
    ]
    assert session.backtest_calls == []
    assert session.optimize_calls == [
        {
            "objective_metric": "total_return",
            "output_root": None,
            "parameters": {
                "entry_bar": [1, 2],
                "quantity": ["1"],
            },
        }
    ]


def test_runner_executes_selected_workflow_step_range_and_reports_only_that_range(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: selected-range
steps:
  - id: review
    kind: factor_review_gate
    status: accepted
    min_count: 1
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
  - id: optimize
    kind: optimize
    objective_metric: total_return
    parameters:
      entry_bar: [1]
      quantity: ["1"]
  - id: report
    kind: research_report
    output_root: reports
    output_path: selected.md
""",
    )
    session = _FakeSession(accepted_specs=())
    config = ResearchWorkflowConfig.from_yaml(workflow_path)

    result = ResearchWorkflowRunner().run(
        session,
        config,
        from_step_id="backtest",
        to_step_id="report",
    )

    assert result.status == "completed"
    assert [(step.step_id, step.status) for step in result.steps] == [
        ("backtest", "passed"),
        ("optimize", "passed"),
        ("report", "passed"),
    ]
    report_path = Path(result.steps[-1].outputs["report_path"])
    report_text = report_path.read_text(encoding="utf-8")
    assert "backtest" in report_text
    assert "optimize" in report_text
    assert "review" not in report_text


def test_runner_rejects_unknown_selected_workflow_step_before_executing(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: bad-selection
steps:
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
""",
    )
    session = _FakeSession(accepted_specs=())

    with pytest.raises(ValueError, match="workflow step not found: missing"):
        ResearchWorkflowRunner().run(
            session,
            ResearchWorkflowConfig.from_yaml(workflow_path),
            step_id="missing",
        )

    assert session.backtest_calls == []


def test_runner_passes_materialized_replay_cache_to_backtest_matrix_and_optimizer(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: materialized-cache
periods:
  is:
    start: "2026-01-01"
    end: "2026-02-01"
    role: validation
steps:
  - id: matrix
    kind: backtest_matrix
    output_root: matrix-runs
    materialized_replay_cache:
      enabled: true
      cache_dir: replay-cache
    periods:
      - name: is
        start: 2026-01-01
        end: 2026-02-01
    candidates:
      - name: q1
        strategy_params:
          quantity: "1"
  - id: optimize
    kind: optimize
    materialized_replay_cache: replay-cache
    objective_metric: total_return
    parameters:
      entry_bar: [1]
      quantity: ["1"]
""",
    )
    session = _FakeSession(
        accepted_specs=(),
        backtest_manifest_root=tmp_path / "manifests",
    )

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert session.backtest_matrix_calls[-1]["materialized_replay_cache_dir"] == (
        tmp_path / "replay-cache"
    )
    assert session.optimize_calls[-1]["materialized_replay_cache_dir"] == (
        tmp_path / "replay-cache"
    )


def test_runner_allows_backtest_step_to_override_session_backtest_config(
    tmp_path: Path,
) -> None:
    production_config = tmp_path / "production-baseline.yaml"
    production_config.write_text("mode: backtest\n", encoding="utf-8")
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: production-baseline
steps:
  - id: baseline
    kind: backtest
    backtest_config: production-baseline.yaml
    strategy_params:
      quantity: "4"
""",
    )
    session = _FakeSession(accepted_specs=())

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert session.backtest_calls == [{"quantity": "4"}]
    assert session.backtest_kwargs == [
        {
            "backtest_config_path": production_config,
            "output_dir": None,
            "strategy_params": {"quantity": "4"},
        }
    ]


def test_runner_runs_backtest_matrix_and_writes_summary(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: matrix-research
periods:
  failure_2022:
    start: "2022-01-01"
    end: "2023-01-01"
    role: validation
steps:
  - id: matrix
    kind: backtest_matrix
    backtest_config: research-backtest.yaml
    output_root: matrix-runs
    summary_output: matrix-summary.json
    base_strategy_params:
      symbol: GC
      time_window: asia_20_02
    metrics: [total_return, sharpe_ratio]
    periods:
      - name: failure_2022
        start: 2022-01-01
        end: 2023-01-01
    candidates:
      - name: base
        strategy_params:
          factor_filters: [session_sigma_range, mom120_aligned]
      - name: escape
        strategy_params:
          factor_filters: [session_sigma_range, mom120_aligned, vwap_acceptance_or_range_expansion]
          vwap_acceptance_min: "0.70"
          range_expansion_min: "1.10"
""",
    )
    session = _FakeSession(accepted_specs=(), backtest_manifest_root=tmp_path / "manifests")

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert result.steps[0].outputs == {
        "candidate_count": 2,
        "period_count": 1,
        "periods": [
            {
                "end": "2023-01-01T00:00:00+00:00",
                "name": "failure_2022",
                "role": "validation",
                "start": "2022-01-01T00:00:00+00:00",
            }
        ],
        "report_only_periods": [],
        "run_count": 2,
        "selection_basis": ["failure_2022"],
        "summary_path": str(tmp_path / "matrix-summary.json"),
    }
    assert session.backtest_kwargs == [
        {
            "backtest_config_path": tmp_path / "research-backtest.yaml",
            "end": datetime(2023, 1, 1, tzinfo=UTC),
            "output_dir": tmp_path / "matrix-runs" / "failure_2022" / "base",
            "start": datetime(2022, 1, 1, tzinfo=UTC),
            "strategy_params": {
                "factor_filters": ["session_sigma_range", "mom120_aligned"],
                "symbol": "GC",
                "time_window": "asia_20_02",
            },
        },
        {
            "backtest_config_path": tmp_path / "research-backtest.yaml",
            "end": datetime(2023, 1, 1, tzinfo=UTC),
            "output_dir": tmp_path / "matrix-runs" / "failure_2022" / "escape",
            "start": datetime(2022, 1, 1, tzinfo=UTC),
            "strategy_params": {
                "factor_filters": [
                    "session_sigma_range",
                    "mom120_aligned",
                    "vwap_acceptance_or_range_expansion",
                ],
                "range_expansion_min": "1.10",
                "symbol": "GC",
                "time_window": "asia_20_02",
                "vwap_acceptance_min": "0.70",
            },
        },
    ]
    summary = json.loads((tmp_path / "matrix-summary.json").read_text(encoding="utf-8"))
    assert summary["candidate_count"] == 2
    assert summary["period_count"] == 1
    assert summary["rows"][0]["candidate"] == "base"
    assert summary["rows"][0]["total_return"] == "0.1"
    assert summary["rows"][1]["candidate"] == "escape"
    assert summary["rows"][1]["sharpe_ratio"] == "0.7"
    assert summary["selection_basis"] == ["failure_2022"]
    assert summary["report_only_periods"] == []


def test_backtest_matrix_records_period_roles(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: matrix-period-roles
periods:
  selection_2020_2022:
    start: "2020-01-01"
    end: "2022-01-01"
    role: selection
  holdout_2024_2026:
    start: "2024-01-01"
    end: "2026-01-01"
    role: holdout_report_only
steps:
  - id: matrix
    kind: backtest_matrix
    output_root: matrix-runs
    summary_output: matrix-summary.json
    periods:
      - selection_2020_2022
      - holdout_2024_2026
    candidates:
      - name: base
        strategy_params: {}
""",
    )
    session = _FakeSession(accepted_specs=(), backtest_manifest_root=tmp_path / "manifests")

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert result.steps[0].outputs["periods"] == [
        {
            "end": "2022-01-01T00:00:00+00:00",
            "name": "selection_2020_2022",
            "role": "selection",
            "start": "2020-01-01T00:00:00+00:00",
        },
        {
            "end": "2026-01-01T00:00:00+00:00",
            "name": "holdout_2024_2026",
            "role": "holdout_report_only",
            "start": "2024-01-01T00:00:00+00:00",
        },
    ]
    summary = json.loads((tmp_path / "matrix-summary.json").read_text(encoding="utf-8"))
    assert summary["selection_basis"] == ["selection_2020_2022"]
    assert summary["report_only_periods"] == ["holdout_2024_2026"]
    assert summary["periods"] == result.steps[0].outputs["periods"]


def test_research_report_includes_declared_period_roles_without_period_steps(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: report-period-roles
periods:
  selection_2020_2022:
    start: "2020-01-01"
    end: "2022-01-01"
    role: selection
  holdout_2024_2026:
    start: "2024-01-01"
    end: "2026-01-01"
    role: holdout_report_only
steps:
  - id: report
    kind: research_report
    output_root: reports
    output_path: workflow.md
""",
    )

    result = ResearchWorkflowRunner().run(
        _FakeSession(accepted_specs=()),
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    report_path = tmp_path / "reports" / "workflow.md"
    report_text = report_path.read_text(encoding="utf-8")
    assert result.status == "completed"
    assert "## Period Roles" in report_text
    assert "selection_2020_2022" in report_text
    assert "holdout_2024_2026" in report_text


def test_runner_runs_portfolio_ensemble_and_writes_research_only_summary(
    tmp_path: Path,
) -> None:
    equity_a = tmp_path / "a.equity_curve.ndjson"
    equity_a.write_text(
        "\n".join(
            (
                json.dumps({"equity": "100", "time": "2020-01-01T00:00:00+00:00"}),
                json.dumps({"equity": "110", "time": "2020-01-02T00:00:00+00:00"}),
            )
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_a = tmp_path / "a.manifest.json"
    manifest_a.write_text(
        json.dumps(
            {
                "artifacts": {"equity_curve": {"path": equity_a.name}},
                "runtime_mode": "backtest",
                "run_id": "a",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    equity_b = tmp_path / "b.equity_curve.ndjson"
    equity_b.write_text(
        "\n".join(
            (
                json.dumps({"equity": "100", "time": "2020-01-01T00:00:00+00:00"}),
                json.dumps({"equity": "90", "time": "2020-01-02T00:00:00+00:00"}),
            )
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_b = tmp_path / "b.manifest.json"
    manifest_b.write_text(
        json.dumps(
            {
                "artifacts": {"equity_curve": {"path": equity_b.name}},
                "runtime_mode": "backtest",
                "run_id": "b",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: portfolio-evidence
steps:
  - id: ensemble
    kind: portfolio_ensemble
    allocation_name: equal
    summary_output: ensemble-summary.json
    legs:
      - name: a
        manifest_path: a.manifest.json
        weight: "1"
      - name: b
        manifest_path: b.manifest.json
        weight: "1"
""",
    )

    result = ResearchWorkflowRunner().run(
        _FakeSession(accepted_specs=()),
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert result.steps[0].outputs == {
        "allocation_name": "equal",
        "leg_count": 2,
        "point_count": 2,
        "research_only": True,
        "summary_path": str(tmp_path / "ensemble-summary.json"),
    }
    summary = json.loads((tmp_path / "ensemble-summary.json").read_text(encoding="utf-8"))
    assert summary["research_only"] is True
    assert summary["metrics"]["total_return"] == "0.0"
    assert summary["source_manifest_paths"] == [str(manifest_a), str(manifest_b)]


def test_runner_runs_portfolio_ensemble_scan_and_writes_summary(tmp_path: Path) -> None:
    def write_manifest(name: str, start: str, end: str) -> Path:
        equity_path = tmp_path / f"{name}.equity_curve.ndjson"
        equity_path.write_text(
            "\n".join(
                (
                    json.dumps({"equity": start, "time": "2020-01-01T00:00:00+00:00"}),
                    json.dumps({"equity": end, "time": "2021-01-01T00:00:00+00:00"}),
                )
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_path = tmp_path / f"{name}.manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "artifacts": {"equity_curve": {"path": equity_path.name}},
                    "runtime_mode": "backtest",
                    "run_id": name,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest_path

    steady_anchor = write_manifest("steady-anchor", "100", "110")
    steady_validation = write_manifest("steady-validation", "100", "105")
    burst_anchor = write_manifest("burst-anchor", "100", "90")
    burst_validation = write_manifest("burst-validation", "100", "130")
    workflow_path = _write_workflow(
        tmp_path,
        f"""
version: 1
workflow_id: allocation-scan
periods:
  anchor:
    start: "2020-01-01"
    end: "2021-01-01"
    role: anchor
  validation:
    start: "2021-01-01"
    end: "2022-01-01"
    role: validation
steps:
  - id: scan
    kind: portfolio_ensemble_scan
    scan_name: unit
    reporting_grid: daily_utc
    weight_step: "0.5"
    top_n: 2
    summary_output: scan-summary.json
    periods: [anchor, validation]
    baseline_period: anchor
    post_periods: [validation]
    constraints:
      min_baseline_annual_return: "0"
      min_post_annual_return: "0.10"
      max_full_drawdown: "0.20"
    candidates:
      - name: steady
        period_manifests:
          anchor: {steady_anchor}
          validation: {steady_validation}
      - name: burst
        period_manifests:
          anchor: {burst_anchor}
          validation: {burst_validation}
""",
    )

    result = ResearchWorkflowRunner().run(
        _FakeSession(accepted_specs=()),
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert result.steps[0].outputs == {
        "candidate_count": 2,
        "evaluated_allocation_count": 3,
        "periods": [
            {
                "end": "2021-01-01T00:00:00+00:00",
                "name": "anchor",
                "role": "anchor",
                "start": "2020-01-01T00:00:00+00:00",
            },
            {
                "end": "2022-01-01T00:00:00+00:00",
                "name": "validation",
                "role": "validation",
                "start": "2021-01-01T00:00:00+00:00",
            },
        ],
        "report_only_periods": [],
        "score_periods": ["anchor", "validation"],
        "satisfying_allocation_count": 1,
        "summary_path": str(tmp_path / "scan-summary.json"),
    }
    summary = json.loads((tmp_path / "scan-summary.json").read_text(encoding="utf-8"))
    assert summary["top_allocations"][0]["weights"] == {"burst": "0.5", "steady": "0.5"}
    assert summary["periods"] == [
        {
            "end": "2021-01-01T00:00:00+00:00",
            "name": "anchor",
            "role": "anchor",
            "start": "2020-01-01T00:00:00+00:00",
        },
        {
            "end": "2022-01-01T00:00:00+00:00",
            "name": "validation",
            "role": "validation",
            "start": "2021-01-01T00:00:00+00:00",
        },
    ]
    assert summary["report_only_periods"] == []
    assert summary["score_periods"] == ["anchor", "validation"]


def test_runner_runs_volatility_managed_allocation_scan_and_writes_summary(
    tmp_path: Path,
) -> None:
    def write_manifest(name: str, values: tuple[str, ...]) -> Path:
        equity_path = tmp_path / f"{name}.equity_curve.ndjson"
        rows = [
            json.dumps({"equity": value, "time": f"2021-01-0{index + 1}T00:00:00+00:00"})
            for index, value in enumerate(values)
        ]
        equity_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        manifest_path = tmp_path / f"{name}.manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "artifacts": {"equity_curve": {"path": equity_path.name}},
                    "runtime_mode": "backtest",
                    "run_id": name,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest_path

    steady = write_manifest("steady", ("100", "101", "102", "103"))
    burst = write_manifest("burst", ("100", "90", "130", "140"))
    workflow_path = _write_workflow(
        tmp_path,
        f"""
version: 1
workflow_id: dynamic-allocation-scan
periods:
  validation:
    start: "2021-01-01"
    end: "2021-01-05"
    role: validation
steps:
  - id: scan
    kind: portfolio_volatility_managed_scan
    scan_name: unit-dynamic
    reporting_grid: daily_utc
    summary_output: dynamic-summary.json
    periods: [validation]
    selection_periods: [validation]
    post_selection_periods: [validation]
    constraints:
      min_selection_post_annual_return: "-1"
      max_selection_drawdown: "1"
    parameter_grid:
      lookback_days: [1]
      min_history_days: [1]
      min_trailing_return: ["-1"]
      top_n_legs: [1]
      target_annual_vol: ["1"]
      max_gross_exposure: ["1"]
      max_leg_weight: ["1"]
    candidates:
      - name: steady
        period_manifests:
          validation: {steady}
      - name: burst
        period_manifests:
          validation: {burst}
""",
    )

    result = ResearchWorkflowRunner().run(
        _FakeSession(accepted_specs=()),
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert result.steps[0].outputs == {
        "candidate_count": 2,
        "evaluated_parameter_count": 1,
        "periods": [
            {
                "end": "2021-01-05T00:00:00+00:00",
                "name": "validation",
                "role": "validation",
                "start": "2021-01-01T00:00:00+00:00",
            },
        ],
        "report_only_periods": [],
        "selection_basis": ["validation"],
        "satisfying_allocation_count": 1,
        "summary_path": str(tmp_path / "dynamic-summary.json"),
    }
    summary = json.loads((tmp_path / "dynamic-summary.json").read_text(encoding="utf-8"))
    assert summary["top_allocations"][0]["parameters"]["lookback_days"] == 1


def test_runner_runs_walk_forward_validation_for_top_optimizer_candidates(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: walk-forward-evidence
periods:
  selection_2026_q1:
    start: "2026-01-01"
    end: "2026-03-01"
    role: selection
  validation_2026_q2:
    start: "2026-04-01"
    end: "2026-05-01"
    role: validation
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


def test_runner_runs_failure_window_veto_for_top_optimizer_candidates(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: failure-veto-evidence
periods:
  validation_2024_q1:
    start: "2024-01-01"
    end: "2024-03-01"
    role: validation
  holdout_2024_march:
    start: "2024-03-01"
    end: "2024-04-01"
    role: holdout_report_only
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      alpha: ["1", "2"]
    validation:
      failure_window_veto:
        top_n: 2
        output_root: failure-veto-output
        summary_output: failure-veto-summary.json
        constraints:
          - metric: pnl_usd
            operator: ">"
            threshold: "0"
        windows:
          - name: crash-2024
            start: 2024-01-01
            end: 2024-03-01
        report_only_windows:
          - name: thaw-2024
            start: 2024-03-01
            end: 2024-04-01
""",
    )
    session = _FakeSession(accepted_specs=())

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "completed"
    assert session.failure_veto_calls == [
        {
            "candidate_parameters": (
                {"entry_bar": 1, "quantity": "2"},
                {"entry_bar": 2, "quantity": "3"},
            ),
            "capital_metric_config": None,
            "constraint_count": 1,
            "objective_metric": "sharpe_ratio",
            "output_root": tmp_path / "failure-veto-output",
            "report_only_windows": (
                {
                    "end": "2024-04-01",
                    "name": "thaw-2024",
                    "report_only": True,
                    "start": "2024-03-01",
                },
            ),
            "windows": (
                {
                    "end": "2024-03-01",
                    "name": "crash-2024",
                    "report_only": False,
                    "start": "2024-01-01",
                },
            ),
        }
    ]
    outputs = result.steps[0].outputs
    assert outputs["failure_window_veto"]["decision"] == {
        "accepted": True,
        "reasons": (),
    }
    summary_output = tmp_path / "failure-veto-summary.json"
    assert outputs["failure_window_veto_output"] == str(summary_output)
    assert json.loads(summary_output.read_text(encoding="utf-8"))["decision"] == {
        "accepted": True,
        "reasons": [],
    }


def test_failure_window_veto_blocks_workflow_when_required_candidate_is_missing(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: failure-veto-block
periods:
  validation_2024_q1:
    start: "2024-01-01"
    end: "2024-03-01"
    role: validation
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      alpha: ["1", "2"]
    validation:
      failure_window_veto:
        require_passing_candidate: true
        constraints:
          - metric: pnl_usd
            operator: ">"
            threshold: "0"
        windows:
          - name: crash-2024
            start: 2024-01-01
            end: 2024-03-01
  - id: report
    kind: research_report
    output_root: reports
    output_path: blocked.md
""",
    )
    session = _FakeSession(accepted_specs=())
    session.failure_veto_accepted = False

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "blocked"
    assert [(step.step_id, step.status, step.message) for step in result.steps] == [
        ("optimize", "blocked", "failure-window veto blocked workflow")
    ]
    assert session.failure_veto_calls
    assert not (tmp_path / "reports" / "blocked.md").exists()


@pytest.mark.parametrize("constraints", ("", "        constraints: []\n"))
def test_failure_window_veto_requires_non_empty_constraints(
    tmp_path: Path,
    constraints: str,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        f"""
version: 1
workflow_id: failure-veto-constraints
periods:
  validation_2024_q1:
    start: "2024-01-01"
    end: "2024-03-01"
    role: validation
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      alpha: ["1"]
    validation:
      failure_window_veto:
{constraints}        windows:
          - name: crash-2024
            start: 2024-01-01
            end: 2024-03-01
""",
    )

    session = _FakeSession(accepted_specs=())

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "failed"
    assert result.steps[0].status == "failed"
    assert (
        result.steps[0].message
        == "validation.failure_window_veto.constraints must be a non-empty list"
    )
    assert session.failure_veto_calls == []


def test_failure_window_veto_rejects_non_boolean_require_passing_candidate(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: failure-veto-boolean
periods:
  validation_2024_q1:
    start: "2024-01-01"
    end: "2024-03-01"
    role: validation
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      alpha: ["1"]
    validation:
      failure_window_veto:
        require_passing_candidate: "false"
        constraints:
          - metric: pnl_usd
            operator: ">"
            threshold: "0"
        windows:
          - name: crash-2024
            start: 2024-01-01
            end: 2024-03-01
""",
    )

    session = _FakeSession(accepted_specs=())

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "failed"
    assert result.steps[0].status == "failed"
    assert (
        result.steps[0].message
        == "validation.failure_window_veto.require_passing_candidate must be a boolean"
    )
    assert session.failure_veto_calls == []


def test_vwap_workflow_defines_true_oos_after_2026_01_01_as_report_only() -> None:
    config = ResearchWorkflowConfig.from_yaml(
        Path("configs/research/workflows/vwap_factor_search.yaml")
    )
    structural = next(step for step in config.steps if step.step_id == "structural-candidates")

    veto = structural.payload["validation"]["failure_window_veto"]
    report_only = veto["report_only_windows"]

    assert {
        "name": str(report_only[-1]["name"]),
        "start": report_only[-1]["start"].isoformat(),
        "end": report_only[-1]["end"].isoformat(),
    } == {
        "name": "true-oos-after-2026-01-01",
        "start": "2026-01-01",
        "end": "2027-01-01",
    }


def test_vwap_structural_workflow_uses_risk_budget_quality_and_partial_runner() -> None:
    config = ResearchWorkflowConfig.from_yaml(
        Path("configs/research/workflows/vwap_factor_search.yaml")
    )
    structural = next(step for step in config.steps if step.step_id == "structural-candidates")
    parameters = structural.payload["parameters"]

    assert parameters["time_window"] == ["full_session"]
    assert parameters["timeframe"] == ["1m", "2m", "3m", "5m", "15m"]
    assert parameters["entry_size_rule"] == ["risk_budget"]
    assert "target_quantity" not in parameters
    assert parameters["risk_budget"] == ["600"]
    assert parameters["risk_budget_point_value"] == ["100"]
    assert parameters["risk_budget_max_quantity"] == ["4"]
    assert parameters["exit_style"] == ["partial_runner"]
    assert parameters["factor_filters"] == [
        ["vwap_acceptance", "trend_efficiency", "trend_age", "session_sigma_range"],
        [
            "vwap_slope_strength",
            "vwap_acceptance",
            "trend_efficiency",
            "trend_age",
            "session_sigma_range",
        ],
    ]


def test_canonical_vwap_workflow_declares_gc_stable_annualized_target_matrix() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}

    matrix = step_by_id["gc-15m-stable-annualized-scale"]
    report_index = next(
        index for index, step in enumerate(payload["steps"]) if step["id"] == "report"
    )
    matrix_index = next(
        index
        for index, step in enumerate(payload["steps"])
        if step["id"] == "gc-15m-stable-annualized-scale"
    )

    assert matrix_index < report_index
    assert matrix["kind"] == "backtest_matrix"
    assert matrix["backtest_config"] == "../../backtest.vwap_factor_research_gc_15m_long_is.yaml"
    assert matrix["summary_output"] == (
        "../../../runs/research/vwap/gc-15m-long/validation/stable-annualized-scale.json"
    )
    assert matrix["metrics"] == [
        "compounding_annual_return",
        "total_return",
        "sharpe_ratio",
        "max_drawdown",
        "total_trades",
        "profit_factor",
    ]
    assert matrix["periods"] == [
        {
            "name": "validation_2022_2024",
            "start": "2022-01-01",
            "end": "2024-01-01",
            "role": "validation",
        },
        {
            "name": "holdout_2024_2026",
            "start": "2024-01-01",
            "end": "2026-01-01",
            "role": "holdout_report_only",
        },
        {
            "name": "true_oos_after_2026_01_01",
            "start": "2026-01-01",
            "end": "2027-01-01",
            "role": "true_oos_report_only",
        },
    ]
    assert matrix["base_strategy_params"] == {
        "bad_regime_rule": "hard14",
        "bad_regime_target_r_multiple": "1.5",
        "bad_regime_unready_policy": "allow",
        "early_no_progress_adverse_r": "0.50",
        "early_no_progress_exit_bars": 4,
        "early_no_progress_favorable_r": "0.25",
        "entry_size_momentum_min_abs": "2.00",
        "entry_size_reduced_quantity": "1",
        "entry_size_rule": "sigma_momentum_reduce",
        "entry_size_session_sigma_min_atr": "1.00",
        "factor_filters": [
            "session_sigma_range",
            "mom120_aligned",
            "mom120_min",
            "vwap_acceptance_if_bad_regime",
            "range_expansion",
        ],
        "max_pullback_break_atr": "1.0",
        "min_volume_ratio": "1.3",
        "pullback_touch_atr_below": "0.15",
        "range_expansion_max": "1.50",
        "range_expansion_min": "0",
        "stop_atr_multiple": "1.0",
        "symbol": "GC",
        "target_r_multiple": "1.5",
        "time_window": "asia_20_02",
        "timeframe": "15m",
        "ts_momentum_min_abs": "1.00",
        "vwap_acceptance_min": "0.75",
    }
    assert [candidate["name"] for candidate in matrix["candidates"]] == [
        "q1_np4_range150_mom100_q4",
        "q1_np4_range150_mom100_q6",
        "q1_np4_range150_mom100_q8",
        "q1_np4_range150_mom100_q10",
        "q1_np4_range150_mom100_q12",
    ]
    assert [
        candidate["strategy_params"]["target_quantity"] for candidate in matrix["candidates"]
    ] == ["4", "6", "8", "10", "12"]


def test_vwap_research_backtest_warmup_covers_workflow_factor_filters() -> None:
    runtime_config = BacktestRuntimeConfig.from_yaml(
        Path("configs/backtest.vwap_factor_research.yaml")
    )
    workflow_config = ResearchWorkflowConfig.from_yaml(
        Path("configs/research/workflows/vwap_factor_search.yaml")
    )
    required_warmup = 0

    for step in workflow_config.steps:
        if step.kind != "optimize":
            continue
        parameters = step.payload["parameters"]
        for factor_filters in parameters.get("factor_filters", ()):
            strategy_params = {
                **runtime_config.strategy_params,
                **{
                    name: values[0]
                    for name, values in parameters.items()
                    if name != "factor_filters" and isinstance(values, list) and values
                },
                "factor_filters": tuple(factor_filters),
            }
            required_warmup = max(
                required_warmup,
                VwapFactorResearchConfig(**strategy_params).required_warmup_bars,
            )

    assert runtime_config.warmup_bars >= required_warmup


def test_vwap_research_config_includes_gc_and_si_for_route_b() -> None:
    payload = yaml.safe_load(Path("configs/research/vwap.yaml").read_text(encoding="utf-8"))

    assert payload["data"]["roots"] == ["GC", "SI"]


def test_canonical_vwap_workflow_declares_route_b_lanes_and_windows() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}

    required_steps = {
        "route-b-implementation",
        "route-b-vwap-gc-rolling",
        "route-b-vwap-si-rolling",
        "route-b-dual-supertrend-gc",
        "route-b-dual-supertrend-si",
    }
    assert required_steps.issubset(step_by_id)
    assert "route-b-gc-si-momentum" not in step_by_id
    assert step_by_id["route-b-implementation"] == {
        "id": "route-b-implementation",
        "kind": "implementation_gate",
        "required_strategy": "examples.strategies.dual_supertrend:DualSupertrendStrategy",
    }

    for step_id in (
        "route-b-vwap-gc-rolling",
        "route-b-vwap-si-rolling",
        "route-b-dual-supertrend-gc",
        "route-b-dual-supertrend-si",
    ):
        periods = {period["name"]: period for period in step_by_id[step_id]["periods"]}
        assert periods["is_2020_2022"] == {
            "name": "is_2020_2022",
            "start": "2020-01-01",
            "end": "2022-01-01",
        }
        assert periods["validation_2022_2024"] == {
            "name": "validation_2022_2024",
            "start": "2022-01-01",
            "end": "2024-01-01",
        }
        assert periods["holdout_2024_2026"] == {
            "name": "holdout_2024_2026",
            "start": "2024-01-01",
            "end": "2026-01-01",
        }
        assert periods["anchor_2010_2020"] == {
            "name": "anchor_2010_2020",
            "start": "2010-06-06",
            "end": "2020-01-01",
        }


def test_route_b_workflow_records_holdout_as_report_only_policy() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    route_b_report = next(step for step in payload["steps"] if step["id"] == "route-b-report")

    assert route_b_report["kind"] == "research_report"
    assert "route-b" in route_b_report["output_root"]
    assert route_b_report["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune candidate selection"
    )


def test_canonical_vwap_workflow_declares_route_j_research_only_ensembles() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}

    required_steps = {
        "route-j-si-vwap-pair-anchor",
        "route-j-si-vwap-pair-is",
        "route-j-si-vwap-pair-validation",
        "route-j-si-vwap-pair-holdout",
        "route-j-i50-si-vwap-anchor",
        "route-j-i50-si-vwap-is",
        "route-j-i50-si-vwap-validation",
        "route-j-i50-si-vwap-holdout",
        "route-j-g50-si-vwap-anchor",
        "route-j-g50-si-vwap-is",
        "route-j-g50-si-vwap-validation",
        "route-j-g50-si-vwap-holdout",
        "route-j-report",
    }
    assert required_steps.issubset(step_by_id)
    for step_id in required_steps - {"route-j-report"}:
        step = step_by_id[step_id]
        assert step["kind"] == "portfolio_ensemble"
        assert step["reporting_grid"] == "daily_utc"
        assert "route-j" in step["summary_output"]
        assert len(step["legs"]) >= 2

    route_j_report = step_by_id["route-j-report"]
    assert route_j_report["kind"] == "research_report"
    assert route_j_report["metadata"]["research_only"] == (
        "portfolio_ensemble consumes completed equity curves and is not a production execution path"
    )


def test_canonical_vwap_workflow_declares_route_k_allocation_scan() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}

    scan = step_by_id["route-k-allocation-scan"]
    assert scan["kind"] == "portfolio_ensemble_scan"
    assert scan["reporting_grid"] == "daily_utc"
    assert scan["weight_step"] == "0.05"
    assert scan["constraints"] == {
        "max_full_drawdown": "0.25",
        "min_baseline_annual_return": "0",
        "min_post_annual_return": "0.10",
    }
    assert scan["periods"] == [
        "anchor_2010_2020",
        "is_2020_2022",
        "validation_2022_2024",
        "holdout_2024_2026",
    ]
    assert scan["post_periods"] == ["is_2020_2022", "validation_2022_2024"]
    assert scan["score_periods"] == [
        "anchor_2010_2020",
        "is_2020_2022",
        "validation_2022_2024",
    ]
    assert {candidate["name"] for candidate in scan["candidates"]} == {
        "vwap_si_trend_sigma_vol15",
        "vwap_si_trend_sigma_slope_accept",
        "risk_mom_84_vol40_max25_confirm2",
        "abs0_no_confirmation",
    }

    report = step_by_id["route-k-report"]
    assert report["kind"] == "research_report"
    assert report["metadata"]["research_only"] == (
        "portfolio_ensemble_scan consumes completed equity curves and is not a production "
        "execution path"
    )


def test_canonical_vwap_workflow_declares_route_l_volatility_managed_scan() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}

    scan = step_by_id["route-l-vol-managed-allocation-scan"]
    assert scan["kind"] == "portfolio_volatility_managed_scan"
    assert scan["reporting_grid"] == "daily_utc"
    assert scan["selection_periods"] == [
        "anchor_2010_2020",
        "is_2020_2022",
        "validation_2022_2024",
    ]
    assert scan["constraints"] == {
        "max_selection_drawdown": "0.25",
        "min_baseline_annual_return": "0",
        "min_selection_post_annual_return": "0.10",
    }
    assert set(scan["parameter_grid"]) == {
        "lookback_days",
        "max_gross_exposure",
        "max_leg_weight",
        "min_history_days",
        "min_trailing_return",
        "target_annual_vol",
        "top_n_legs",
    }
    assert {candidate["name"] for candidate in scan["candidates"]} == {
        "vwap_si_trend_sigma_vol15",
        "vwap_si_trend_sigma_slope_accept",
        "risk_mom_84_vol40_max25_confirm2",
        "abs0_no_confirmation",
    }

    report = step_by_id["route-l-report"]
    assert report["kind"] == "research_report"
    assert report["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune allocation parameter selection"
    )


def test_canonical_vwap_workflow_declares_route_m_multi_horizon_dual_momentum() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}
    strategy = "examples.strategies.dual_momentum_rotation:DualMomentumRotationStrategy"

    assert step_by_id["route-m-implementation"] == {
        "id": "route-m-implementation",
        "kind": "implementation_gate",
        "required_strategy": strategy,
    }
    matrix = step_by_id["route-m-multi-horizon-dual-momentum"]
    assert matrix["kind"] == "backtest_matrix"
    assert matrix["backtest_config"] == "../../backtest.route_m_multi_horizon_dual_momentum.yaml"
    assert matrix["base_strategy_params"]["lookback_bars"] == [21, 63, 126]
    assert [period["name"] for period in matrix["periods"]] == [
        "is_2020_2022",
        "validation_2022_2024",
        "holdout_2024_2026",
    ]
    assert matrix["materialized_replay_cache"] == {
        "cache_dir": "../../../runs/research/vwap/replay-cache/route-m",
        "enabled": True,
    }
    assert {candidate["name"] for candidate in matrix["candidates"]} == {
        "mh_21_63_126_abs0_rel03",
        "mh_42_84_168_abs0_rel03",
        "mh_63_126_252_abs0_rel02",
        "mh_21_84_252_abs2_rel03_confirm2",
    }
    assert step_by_id["route-m-report"]["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune candidate selection"
    )


def test_canonical_vwap_workflow_declares_route_n_carry_momentum_rotation() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}
    strategy = "examples.strategies.carry_momentum_rotation:CarryMomentumRotationStrategy"

    assert step_by_id["route-n-implementation"] == {
        "id": "route-n-implementation",
        "kind": "implementation_gate",
        "required_strategy": strategy,
    }
    matrix = step_by_id["route-n-carry-momentum-rotation"]
    assert matrix["kind"] == "backtest_matrix"
    assert matrix["backtest_config"] == "../../backtest.route_n_carry_momentum_rotation.yaml"
    assert matrix["base_strategy_params"]["momentum_lookback_bars"] == [21, 63, 126]
    assert matrix["base_strategy_params"]["carry_zscore_weight"] == "0.02"
    assert matrix["base_strategy_params"]["min_relative_score"] == "0.02"
    assert [period["name"] for period in matrix["periods"]] == [
        "is_2020_2022",
        "validation_2022_2024",
        "holdout_2024_2026",
    ]
    assert matrix["materialized_replay_cache"] == {
        "cache_dir": "../../../runs/research/vwap/replay-cache/route-n",
        "enabled": True,
    }
    candidate_names = [candidate["name"] for candidate in matrix["candidates"]]
    assert candidate_names == [
        "cmr_21_63_126_cz20_w02_rel02_tv20",
        "cmr_21_63_126_cz20_w02_rel00_tv20",
        "cmr_21_63_126_cz20_w02_rel02_tv15",
        "cmr_21_63_126_cz20_w02_rel02_tv25",
        "cmr_21_63_126_cz20_w02_rel02_score04_tv20",
        "cmr_21_63_126_cz20_w02_rel04_tv20",
        "cmr_21_63_126_cz20_w00_rel04_score02_tv20",
        "cmr_21_63_126_cz20_w01_rel04_tv20",
        "cmr_42_84_168_cz60_w02_rel02_tv20",
    ]
    assert step_by_id["route-n-report"]["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune candidate selection"
    )


def test_canonical_vwap_workflow_declares_route_o_opening_range_breakout() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}
    strategy = "examples.strategies.opening_range_breakout:OpeningRangeBreakoutStrategy"

    assert step_by_id["route-o-implementation"] == {
        "id": "route-o-implementation",
        "kind": "implementation_gate",
        "required_strategy": strategy,
    }
    matrix = step_by_id["route-o-opening-range-breakout"]
    assert matrix["kind"] == "backtest_matrix"
    assert matrix["backtest_config"] == "../../backtest.route_o_opening_range_breakout.yaml"
    assert matrix["base_strategy_params"]["timeframe"] == "15m"
    assert matrix["base_strategy_params"]["opening_range_minutes"] == 60
    assert matrix["base_strategy_params"]["range_width_min_history_sessions"] == 10
    assert [period["name"] for period in matrix["periods"]] == [
        "is_2020_2022",
        "validation_2022_2024",
        "holdout_2024_2026",
    ]
    assert matrix["materialized_replay_cache"] == {
        "cache_dir": "../../../runs/research/vwap/replay-cache/route-o",
        "enabled": True,
    }
    candidate_names = [candidate["name"] for candidate in matrix["candidates"]]
    assert candidate_names == [
        "orb_gc_0830_60_breakout_q1",
        "orb_si_0830_60_breakout_q1",
        "orf_gc_0830_60_failure_q1",
        "orf_si_0830_60_failure_q1",
        "orb_gc_1800_60_breakout_q1",
        "orb_si_1800_60_breakout_q1",
        "orf_gc_1800_60_failure_q1",
        "orf_si_1800_60_failure_q1",
    ]
    assert step_by_id["route-o-report"]["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune candidate selection"
    )


def test_canonical_vwap_workflow_declares_route_p_intraday_ratio_mean_reversion() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}
    strategy = "examples.strategies.gc_si_ratio_mean_reversion:GcSiRatioMeanReversionStrategy"

    assert step_by_id["route-p-implementation"] == {
        "id": "route-p-implementation",
        "kind": "implementation_gate",
        "required_strategy": strategy,
    }
    matrix = step_by_id["route-p-intraday-ratio-mean-reversion"]
    assert matrix["kind"] == "backtest_matrix"
    assert matrix["backtest_config"] == "../../backtest.route_p_intraday_ratio_mean_reversion.yaml"
    assert matrix["base_strategy_params"]["timeframe"] == "15m"
    assert matrix["base_strategy_params"]["gc_contracts"] == "1"
    assert matrix["base_strategy_params"]["si_contracts"] == "2"
    assert [period["name"] for period in matrix["periods"]] == [
        "is_2020_2022",
        "validation_2022_2024",
        "holdout_2024_2026",
    ]
    assert matrix["materialized_replay_cache"] == {
        "cache_dir": "../../../runs/research/vwap/replay-cache/route-p",
        "enabled": True,
    }
    candidate_names = [candidate["name"] for candidate in matrix["candidates"]]
    assert candidate_names == [
        "ratio15m_64_entry15_exit025_1x2",
        "ratio15m_96_entry15_exit025_1x2",
        "ratio15m_192_entry20_exit050_1x2",
        "ratio15m_384_entry20_exit050_1x2",
        "ratio15m_192_entry25_exit075_1x2",
        "ratio15m_96_entry20_exit050_1x1",
    ]
    assert step_by_id["route-p-report"]["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune candidate selection"
    )


def test_canonical_vwap_workflow_declares_route_q_opening_range_risk_refinement() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}
    strategy = "examples.strategies.opening_range_breakout:OpeningRangeBreakoutStrategy"

    assert step_by_id["route-q-implementation"] == {
        "id": "route-q-implementation",
        "kind": "implementation_gate",
        "required_strategy": strategy,
    }
    matrix = step_by_id["route-q-opening-range-risk-refinement"]
    assert matrix["kind"] == "backtest_matrix"
    assert matrix["backtest_config"] == "../../backtest.route_o_opening_range_breakout.yaml"
    assert matrix["base_strategy_params"]["symbol"] == "SI"
    assert matrix["base_strategy_params"]["range_start_et"] == "08:30"
    assert matrix["base_strategy_params"]["mode"] == "breakout"
    assert [period["name"] for period in matrix["periods"]] == [
        "is_2020_2022",
        "validation_2022_2024",
        "holdout_2024_2026",
    ]
    assert matrix["materialized_replay_cache"] == {
        "cache_dir": "../../../runs/research/vwap/replay-cache/route-o",
        "enabled": True,
    }
    candidate_names = [candidate["name"] for candidate in matrix["candidates"]]
    assert candidate_names == [
        "si0830_base",
        "si0830_buffer005",
        "si0830_buffer010",
        "si0830_stop050_target100",
        "si0830_stop050_target150",
        "si0830_hold8",
        "si0830_range_width_cap200",
        "si0830_range_width_050_200",
    ]
    assert step_by_id["route-q-report"]["metadata"]["selection_policy"] == (
        "select only with IS and validation evidence; holdout is report-only"
    )


def test_canonical_vwap_workflow_declares_route_r_vol_managed_allocation() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}

    scan = step_by_id["route-r-vol-managed-allocation-scan"]
    assert scan["kind"] == "portfolio_volatility_managed_scan"
    assert scan["periods"] == [
        "is_2020_2022",
        "validation_2022_2024",
        "holdout_2024_2026",
    ]
    assert scan["baseline_period"] == "is_2020_2022"
    assert scan["selection_periods"] == ["is_2020_2022", "validation_2022_2024"]
    assert scan["post_selection_periods"] == ["validation_2022_2024"]
    assert scan["constraints"] == {
        "max_selection_drawdown": "0.20",
        "min_baseline_annual_return": "0.10",
        "min_selection_post_annual_return": "0.10",
    }
    assert scan["parameter_grid"]["target_annual_vol"] == ["0.20", "0.30", "0.40"]
    assert scan["parameter_grid"]["max_gross_exposure"] == ["1.5", "2.0", "3.0"]
    assert [candidate["name"] for candidate in scan["candidates"]] == [
        "abs0_no_confirmation",
        "risk_mom_84_vol40_max25_confirm2",
        "vwap_si_trend_sigma_slope_accept",
        "si0830_buffer010",
        "si0830_hold8",
    ]
    assert step_by_id["route-r-report"]["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune allocation parameter selection"
    )


def test_canonical_vwap_workflow_declares_route_c_lanes_and_windows() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}

    required_steps = {
        "route-c-implementation",
        "route-c-vol-target-trend-gc",
        "route-c-vol-target-trend-si",
    }
    assert required_steps.issubset(step_by_id)
    assert step_by_id["route-c-implementation"] == {
        "id": "route-c-implementation",
        "kind": "implementation_gate",
        "required_strategy": "examples.strategies.vol_target_trend:VolTargetTrendStrategy",
    }

    for step_id in ("route-c-vol-target-trend-gc", "route-c-vol-target-trend-si"):
        periods = {period["name"]: period for period in step_by_id[step_id]["periods"]}
        assert periods["is_2020_2022"] == {
            "name": "is_2020_2022",
            "start": "2020-01-01",
            "end": "2022-01-01",
        }
        assert periods["validation_2022_2024"] == {
            "name": "validation_2022_2024",
            "start": "2022-01-01",
            "end": "2024-01-01",
        }
        assert periods["holdout_2024_2026"] == {
            "name": "holdout_2024_2026",
            "start": "2024-01-01",
            "end": "2026-01-01",
        }
        assert periods["anchor_2010_2020"] == {
            "name": "anchor_2010_2020",
            "start": "2010-06-06",
            "end": "2020-01-01",
        }
        assert {candidate["name"] for candidate in step_by_id[step_id]["candidates"]} == {
            "tsm_63_vol20_target20",
            "tsm_126_vol40_target20",
            "tsm_252_vol60_target15",
        }


def test_route_c_workflow_records_holdout_as_report_only_policy() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    route_c_report = next(step for step in payload["steps"] if step["id"] == "route-c-report")

    assert route_c_report["kind"] == "research_report"
    assert "route-c" in route_c_report["output_root"]
    assert route_c_report["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune candidate selection"
    )


def test_canonical_vwap_workflow_declares_route_d_relative_value_lane() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}

    required_steps = {
        "route-d-implementation",
        "route-d-gc-si-ratio-mean-reversion",
    }
    assert required_steps.issubset(step_by_id)
    assert step_by_id["route-d-implementation"] == {
        "id": "route-d-implementation",
        "kind": "implementation_gate",
        "required_strategy": (
            "examples.strategies.gc_si_ratio_mean_reversion:GcSiRatioMeanReversionStrategy"
        ),
    }

    matrix = step_by_id["route-d-gc-si-ratio-mean-reversion"]
    periods = {period["name"]: period for period in matrix["periods"]}
    assert periods["is_2020_2022"] == {
        "name": "is_2020_2022",
        "start": "2020-01-01",
        "end": "2022-01-01",
    }
    assert periods["validation_2022_2024"] == {
        "name": "validation_2022_2024",
        "start": "2022-01-01",
        "end": "2024-01-01",
    }
    assert periods["holdout_2024_2026"] == {
        "name": "holdout_2024_2026",
        "start": "2024-01-01",
        "end": "2026-01-01",
    }
    assert periods["anchor_2010_2020"] == {
        "name": "anchor_2010_2020",
        "start": "2010-06-06",
        "end": "2020-01-01",
    }
    assert {candidate["name"] for candidate in matrix["candidates"]} == {
        "ratio_20_entry15_exit025_1x2",
        "ratio_60_entry15_exit025_1x2",
        "ratio_60_entry20_exit050_1x2",
        "ratio_120_entry20_exit050_1x2",
    }


def test_route_d_workflow_records_holdout_as_report_only_policy() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    route_d_report = next(step for step in payload["steps"] if step["id"] == "route-d-report")

    assert route_d_report["kind"] == "research_report"
    assert "route-d" in route_d_report["output_root"]
    assert route_d_report["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune candidate selection"
    )


def test_canonical_vwap_workflow_declares_route_e_carry_trend_lane() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    step_by_id = {step["id"]: step for step in payload["steps"]}

    required_steps = {
        "route-e-implementation",
        "route-e-carry-trend-overlay",
    }
    assert required_steps.issubset(step_by_id)
    assert step_by_id["route-e-implementation"] == {
        "id": "route-e-implementation",
        "kind": "implementation_gate",
        "required_strategy": ("examples.strategies.carry_trend_overlay:CarryTrendOverlayStrategy"),
    }

    matrix = step_by_id["route-e-carry-trend-overlay"]
    assert matrix["backtest_config"] == "../../backtest.route_e_carry_trend.yaml"
    assert matrix["base_strategy_params"]["carry_symbols"] == {
        "GC": "GC_CARRY",
        "SI": "SI_CARRY",
    }
    periods = {period["name"]: period for period in matrix["periods"]}
    assert periods["is_2020_2022"] == {
        "name": "is_2020_2022",
        "start": "2020-01-01",
        "end": "2022-01-01",
    }
    assert periods["validation_2022_2024"] == {
        "name": "validation_2022_2024",
        "start": "2022-01-01",
        "end": "2024-01-01",
    }
    assert periods["holdout_2024_2026"] == {
        "name": "holdout_2024_2026",
        "start": "2024-01-01",
        "end": "2026-01-01",
    }
    assert periods["anchor_2010_2020"] == {
        "name": "anchor_2010_2020",
        "start": "2010-06-06",
        "end": "2020-01-01",
    }
    assert {candidate["name"] for candidate in matrix["candidates"]} == {
        "carry_trend_63_5_min0_target10",
        "carry_trend_126_20_min0_target15",
        "carry_trend_252_20_min0_target15",
        "carry_trend_126_60_min025_target15",
    }


def test_route_e_workflow_records_holdout_as_report_only_policy() -> None:
    workflow_path = Path("configs/research/workflows/vwap_factor_search.yaml")
    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    route_e_report = next(step for step in payload["steps"] if step["id"] == "route-e-report")

    assert route_e_report["kind"] == "research_report"
    assert "route-e" in route_e_report["output_root"]
    assert route_e_report["metadata"]["holdout_policy"] == (
        "2024-2026 is report-only and must not tune candidate selection"
    )


@pytest.mark.parametrize(
    (
        "backtest_path",
        "symbol",
        "margin_proxy",
        "baseline_quantity",
    ),
    [
        (
            Path("configs/backtest.vwap_factor_research.yaml"),
            "GC",
            Decimal("12000"),
            "3",
        ),
        (
            Path("configs/backtest.vwap_factor_research_gc_long_is.yaml"),
            "GC",
            Decimal("12000"),
            "3",
        ),
        (
            Path("configs/backtest.vwap_factor_research_si_long_is.yaml"),
            "SI",
            Decimal("15000"),
            "2",
        ),
        (
            Path("configs/backtest.vwap_factor_research_gc_5m_long_is.yaml"),
            "GC",
            Decimal("12000"),
            "3",
        ),
        (
            Path("configs/backtest.vwap_factor_research_si_5m_long_is.yaml"),
            "SI",
            Decimal("15000"),
            "2",
        ),
        (
            Path("configs/backtest.vwap_factor_research_gc_15m_long_is.yaml"),
            "GC",
            Decimal("12000"),
            "3",
        ),
        (
            Path("configs/backtest.vwap_factor_research_si_15m_long_is.yaml"),
            "SI",
            Decimal("15000"),
            "2",
        ),
    ],
)
def test_vwap_research_backtests_use_costed_100k_margin_sized_capital(
    backtest_path: Path,
    symbol: str,
    margin_proxy: Decimal,
    baseline_quantity: str,
) -> None:
    runtime_config = BacktestRuntimeConfig.from_yaml(backtest_path)

    assert runtime_config.initial_cash == Decimal("100000")
    assert runtime_config.cost_model.fixed_commission_per_contract == Decimal("2.50")
    assert runtime_config.cost_model.slippage_bps == Decimal("0.25")
    assert runtime_config.strategy_params["symbol"] == symbol
    assert runtime_config.strategy_params["target_quantity"] == baseline_quantity
    _assert_margin_sized_quantities(
        quantities=(baseline_quantity,),
        initial_cash=runtime_config.initial_cash,
        margin_proxy=margin_proxy,
    )


@pytest.mark.parametrize(
    ("workflow_path", "expected_quantities"),
    [
        (
            Path("configs/research/workflows/vwap_factor_gc_long_search.yaml"),
            ("3", "4"),
        ),
        (
            Path("configs/research/workflows/vwap_factor_si_long_search.yaml"),
            ("2", "3"),
        ),
        (
            Path("configs/research/workflows/vwap_factor_gc_5m_long_search.yaml"),
            ("3", "4"),
        ),
        (
            Path("configs/research/workflows/vwap_factor_si_5m_long_search.yaml"),
            ("2", "3"),
        ),
        (
            Path("configs/research/workflows/vwap_factor_gc_15m_long_search.yaml"),
            ("3", "4"),
        ),
        (
            Path("configs/research/workflows/vwap_factor_si_15m_long_search.yaml"),
            ("2", "3"),
        ),
    ],
)
def test_vwap_research_workflows_search_margin_sized_quantities(
    workflow_path: Path,
    expected_quantities: tuple[str, ...],
) -> None:
    workflow_config = ResearchWorkflowConfig.from_yaml(workflow_path)

    optimize_steps = [step for step in workflow_config.steps if step.kind == "optimize"]

    assert optimize_steps
    for step in optimize_steps:
        assert step.payload["parameters"]["target_quantity"] == list(expected_quantities)


def test_vwap_canonical_workflow_uses_risk_budget_sizing_not_fixed_quantity() -> None:
    workflow_config = ResearchWorkflowConfig.from_yaml(
        Path("configs/research/workflows/vwap_factor_search.yaml")
    )
    optimize_steps = [step for step in workflow_config.steps if step.kind == "optimize"]

    assert optimize_steps
    for step in optimize_steps:
        parameters = step.payload["parameters"]
        assert "target_quantity" not in parameters
        assert parameters["entry_size_rule"] == ["risk_budget"]
        assert parameters["risk_budget"] == ["600"]
        assert parameters["risk_budget_max_quantity"] == ["4"]


def test_no_legacy_vwap_optimizer_configs_remain() -> None:
    assert sorted(path.name for path in Path("configs/optimizer").glob("vwap*.yaml")) == []


def test_period_sensitive_research_workflow_configs_declare_period_roles() -> None:
    for workflow_path in sorted(Path("configs/research/workflows").glob("*.yaml")):
        payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        sensitive_steps = [
            str(step.get("id", ""))
            for step in payload.get("steps", ())
            if isinstance(step, dict) and _step_requires_period_roles(step)
        ]
        assert not sensitive_steps or payload.get("periods"), workflow_path
        ResearchWorkflowConfig.from_yaml(workflow_path)


@pytest.mark.parametrize(
    (
        "symbol",
        "timeframe",
        "session_path",
        "backtest_path",
        "workflow_path",
        "output_fragment",
    ),
    [
        (
            "GC",
            "1m",
            Path("configs/research/vwap_gc_long.yaml"),
            Path("configs/backtest.vwap_factor_research_gc_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_gc_long_search.yaml"),
            "gc-long",
        ),
        (
            "SI",
            "1m",
            Path("configs/research/vwap_si_long.yaml"),
            Path("configs/backtest.vwap_factor_research_si_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_si_long_search.yaml"),
            "si-long",
        ),
        (
            "GC",
            "5m",
            Path("configs/research/vwap_gc_5m_long.yaml"),
            Path("configs/backtest.vwap_factor_research_gc_5m_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_gc_5m_long_search.yaml"),
            "gc-5m-long",
        ),
        (
            "SI",
            "5m",
            Path("configs/research/vwap_si_5m_long.yaml"),
            Path("configs/backtest.vwap_factor_research_si_5m_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_si_5m_long_search.yaml"),
            "si-5m-long",
        ),
        (
            "GC",
            "15m",
            Path("configs/research/vwap_gc_15m_long.yaml"),
            Path("configs/backtest.vwap_factor_research_gc_15m_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_gc_15m_long_search.yaml"),
            "gc-15m-long",
        ),
        (
            "SI",
            "15m",
            Path("configs/research/vwap_si_15m_long.yaml"),
            Path("configs/backtest.vwap_factor_research_si_15m_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_si_15m_long_search.yaml"),
            "si-15m-long",
        ),
    ],
)
def test_vwap_long_research_configs_are_symbol_isolated_and_hold_out_oos(
    symbol: str,
    timeframe: str,
    session_path: Path,
    backtest_path: Path,
    workflow_path: Path,
    output_fragment: str,
) -> None:
    session_config = ResearchSessionConfig.from_yaml(session_path)
    runtime_config = BacktestRuntimeConfig.from_yaml(backtest_path)
    workflow_config = ResearchWorkflowConfig.from_yaml(workflow_path)

    assert session_config.roots == (symbol,)
    assert session_config.timeframe == timeframe
    assert session_config.backtest_config_path.resolve() == backtest_path.resolve()
    assert output_fragment in str(session_config.output_root)
    assert runtime_config.roots == (symbol,)
    assert runtime_config.symbols == (symbol,)
    assert runtime_config.timeframe == timeframe
    assert runtime_config.strategy_params["symbol"] == symbol
    assert runtime_config.start.isoformat() == "2010-06-06T00:00:00+00:00"
    assert runtime_config.end.isoformat() == "2023-01-01T00:00:00+00:00"

    output_paths = {
        str(step.payload.get("output_root") or step.payload.get("output_dir"))
        for step in workflow_config.steps
        if step.kind in {"backtest", "optimize"}
    }
    assert output_paths
    assert all(output_fragment in output_path for output_path in output_paths)

    assert all(
        "walk_forward" not in step.payload.get("validation", {})
        for step in workflow_config.steps
        if step.kind == "optimize"
    )


@pytest.mark.parametrize(
    ("workflow_path", "fragment"),
    [
        (Path("configs/research/workflows/vwap_factor_gc_long_search.yaml"), "gc-long"),
        (Path("configs/research/workflows/vwap_factor_si_long_search.yaml"), "si-long"),
        (
            Path("configs/research/workflows/vwap_factor_gc_5m_long_search.yaml"),
            "gc-5m-long",
        ),
        (
            Path("configs/research/workflows/vwap_factor_si_5m_long_search.yaml"),
            "si-5m-long",
        ),
        (
            Path("configs/research/workflows/vwap_factor_gc_15m_long_search.yaml"),
            "gc-15m-long",
        ),
        (
            Path("configs/research/workflows/vwap_factor_si_15m_long_search.yaml"),
            "si-15m-long",
        ),
    ],
)
def test_vwap_long_research_workflows_declare_oos_as_report_only_periods(
    workflow_path: Path,
    fragment: str,
) -> None:
    workflow_config = ResearchWorkflowConfig.from_yaml(workflow_path)
    optimize_steps = [step for step in workflow_config.steps if step.kind == "optimize"]

    assert workflow_config.periods == (
        {
            "name": "selection_2010_2022",
            "start": datetime(2010, 6, 6, tzinfo=UTC),
            "end": datetime(2022, 1, 1, tzinfo=UTC),
            "role": "selection",
        },
        {
            "name": "validation_2022_2023",
            "start": datetime(2022, 1, 1, tzinfo=UTC),
            "end": datetime(2023, 1, 1, tzinfo=UTC),
            "role": "validation",
        },
        {
            "name": "holdout_2023_2026",
            "start": datetime(2023, 1, 1, tzinfo=UTC),
            "end": datetime(2026, 4, 10, tzinfo=UTC),
            "role": "holdout_report_only",
        },
    )

    assert optimize_steps
    for step in optimize_steps:
        veto = step.payload["validation"]["failure_window_veto"]
        report_only_periods = [
            period
            for period in workflow_config.periods
            if period["role"] in {"holdout_report_only", "true_oos_report_only"}
        ]
        for window in veto["windows"]:
            for period in report_only_periods:
                assert not _intervals_overlap(
                    window["start"],
                    window["end"],
                    period["start"],
                    period["end"],
                )
        assert veto["top_n"] == 3
        assert veto["require_passing_candidate"] is True
        assert veto["output_root"] == f"../../../runs/research/vwap/{fragment}/failure-veto/primary"
        assert (
            veto["summary_output"]
            == f"../../../runs/research/vwap/{fragment}/validation/failure-veto.json"
        )
        assert [
            {
                "name": str(window["name"]),
                "start": window["start"].isoformat(),
                "end": window["end"].isoformat(),
            }
            for window in veto["windows"]
        ] == [
            {"name": "failure-2022", "start": "2022-01-01", "end": "2023-01-01"},
        ]
        assert [
            {
                "name": str(window["name"]),
                "start": window["start"].isoformat(),
                "end": window["end"].isoformat(),
            }
            for window in veto["report_only_windows"]
        ] == [
            {"name": "report-2023", "start": "2023-01-01", "end": "2024-01-01"},
            {"name": "report-2024", "start": "2024-01-01", "end": "2025-01-01"},
            {"name": "report-2025-2026", "start": "2025-01-01", "end": "2026-04-10"},
        ]
        assert veto["constraints"] == [
            {"metric": "pnl_usd", "operator": ">", "threshold": "0"},
            {"metric": "max_drawdown", "operator": "<=", "threshold": "0.05"},
        ]


@pytest.mark.parametrize(
    ("workflow_path", "margin_proxy", "expected_quantity"),
    [
        (
            Path("configs/research/workflows/vwap_factor_gc_15m_feature_ablation.yaml"),
            "12000",
            ["4"],
        ),
        (
            Path("configs/research/workflows/vwap_factor_si_15m_feature_ablation.yaml"),
            "15000",
            ["3"],
        ),
    ],
)
def test_vwap_feature_ablation_workflows_keep_oos_report_only(
    workflow_path: Path,
    margin_proxy: str,
    expected_quantity: list[str],
) -> None:
    workflow_config = ResearchWorkflowConfig.from_yaml(workflow_path)
    optimize_step = next(step for step in workflow_config.steps if step.kind == "optimize")
    veto = optimize_step.payload["validation"]["failure_window_veto"]

    assert workflow_config.periods == (
        {
            "name": "selection_2010_2022",
            "start": datetime(2010, 6, 6, tzinfo=UTC),
            "end": datetime(2022, 1, 1, tzinfo=UTC),
            "role": "selection",
        },
        {
            "name": "validation_2022_2023",
            "start": datetime(2022, 1, 1, tzinfo=UTC),
            "end": datetime(2023, 1, 1, tzinfo=UTC),
            "role": "validation",
        },
        {
            "name": "holdout_2023_2026",
            "start": datetime(2023, 1, 1, tzinfo=UTC),
            "end": datetime(2026, 4, 10, tzinfo=UTC),
            "role": "holdout_report_only",
        },
    )
    assert optimize_step.payload["capital_metrics"] == {"margin_proxy": margin_proxy}
    assert optimize_step.payload["parameters"]["target_quantity"] == expected_quantity
    assert "walk_forward" not in optimize_step.payload["validation"]
    assert [
        {
            "name": str(window["name"]),
            "start": window["start"].isoformat(),
            "end": window["end"].isoformat(),
        }
        for window in veto["windows"]
    ] == [{"name": "failure-2022", "start": "2022-01-01", "end": "2023-01-01"}]
    assert [
        {
            "name": str(window["name"]),
            "start": window["start"].isoformat(),
            "end": window["end"].isoformat(),
        }
        for window in veto["report_only_windows"]
    ] == [
        {"name": "report-2023", "start": "2023-01-01", "end": "2024-01-01"},
        {"name": "report-2024", "start": "2024-01-01", "end": "2025-01-01"},
        {"name": "report-2025-2026", "start": "2025-01-01", "end": "2026-04-10"},
    ]


@pytest.mark.parametrize(
    ("backtest_path", "workflow_path"),
    [
        (
            Path("configs/backtest.vwap_factor_research_gc_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_gc_long_search.yaml"),
        ),
        (
            Path("configs/backtest.vwap_factor_research_si_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_si_long_search.yaml"),
        ),
        (
            Path("configs/backtest.vwap_factor_research_gc_5m_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_gc_5m_long_search.yaml"),
        ),
        (
            Path("configs/backtest.vwap_factor_research_si_5m_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_si_5m_long_search.yaml"),
        ),
        (
            Path("configs/backtest.vwap_factor_research_gc_15m_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_gc_15m_long_search.yaml"),
        ),
        (
            Path("configs/backtest.vwap_factor_research_si_15m_long_is.yaml"),
            Path("configs/research/workflows/vwap_factor_si_15m_long_search.yaml"),
        ),
    ],
)
def test_vwap_long_research_backtest_warmup_covers_workflow_factor_filters(
    backtest_path: Path,
    workflow_path: Path,
) -> None:
    runtime_config = BacktestRuntimeConfig.from_yaml(backtest_path)
    workflow_config = ResearchWorkflowConfig.from_yaml(workflow_path)

    assert runtime_config.warmup_bars >= _required_warmup_for_workflow(
        runtime_config,
        workflow_config,
    )


@pytest.mark.parametrize(
    "workflow_path",
    [
        Path("configs/research/workflows/vwap_factor_gc_long_search.yaml"),
        Path("configs/research/workflows/vwap_factor_si_long_search.yaml"),
        Path("configs/research/workflows/vwap_factor_gc_5m_long_search.yaml"),
        Path("configs/research/workflows/vwap_factor_si_5m_long_search.yaml"),
        Path("configs/research/workflows/vwap_factor_gc_15m_long_search.yaml"),
        Path("configs/research/workflows/vwap_factor_si_15m_long_search.yaml"),
    ],
)
def test_vwap_long_research_includes_unfiltered_asia_candidate(
    workflow_path: Path,
) -> None:
    workflow_config = ResearchWorkflowConfig.from_yaml(workflow_path)
    optimize_step = next(step for step in workflow_config.steps if step.kind == "optimize")
    parameters = optimize_step.payload["parameters"]

    assert "asia_20_02" in parameters["time_window"]
    assert [] in parameters["factor_filters"]
    assert "1.2" in parameters["min_volume_ratio"]


@pytest.mark.parametrize(
    ("workflow_path", "expected_volume_ratio"),
    [
        (
            Path("configs/research/workflows/vwap_factor_gc_long_search.yaml"),
            "1.3",
        ),
        (
            Path("configs/research/workflows/vwap_factor_gc_5m_long_search.yaml"),
            "1.3",
        ),
        (
            Path("configs/research/workflows/vwap_factor_gc_15m_long_search.yaml"),
            "1.3",
        ),
        (
            Path("configs/research/workflows/vwap_factor_si_long_search.yaml"),
            "1.5",
        ),
        (
            Path("configs/research/workflows/vwap_factor_si_5m_long_search.yaml"),
            "1.5",
        ),
        (
            Path("configs/research/workflows/vwap_factor_si_15m_long_search.yaml"),
            "1.5",
        ),
    ],
)
def test_vwap_long_research_includes_costed_oos_volume_candidates(
    workflow_path: Path,
    expected_volume_ratio: str,
) -> None:
    workflow_config = ResearchWorkflowConfig.from_yaml(workflow_path)
    optimize_step = next(step for step in workflow_config.steps if step.kind == "optimize")
    parameters = optimize_step.payload["parameters"]

    assert expected_volume_ratio in parameters["min_volume_ratio"]


def test_vwap_gc_research_workflow_includes_volume_13_candidate() -> None:
    workflow_config = ResearchWorkflowConfig.from_yaml(
        Path("configs/research/workflows/vwap_factor_search.yaml")
    )
    for step in workflow_config.steps:
        if step.kind == "optimize":
            assert "1.3" in step.payload["parameters"]["min_volume_ratio"]


def test_vwap_canonical_workflow_has_expected_optimize_steps() -> None:
    workflow_config = ResearchWorkflowConfig.from_yaml(
        Path("configs/research/workflows/vwap_factor_search.yaml")
    )
    baseline = next(step for step in workflow_config.steps if step.step_id == "baseline")
    optimize_steps = [step for step in workflow_config.steps if step.kind == "optimize"]

    assert baseline.kind == "backtest"
    assert baseline.payload["backtest_config"] == "../../backtest.vwap_production_pullback_gc.yaml"

    assert [(step.step_id, step.payload["objective_metric"]) for step in optimize_steps] == [
        ("structural-candidates", "sharpe_ratio"),
    ]

    factor_search = optimize_steps[0].payload
    assert factor_search["output_root"] == "../../../runs/research/vwap/structural-candidates"
    assert (
        factor_search["validation_output"]
        == "../../../runs/research/vwap/validation/structural-candidates.json"
    )
    assert factor_search["capital_metrics"] == {"margin_proxy": "12000"}
    assert factor_search["parameters"]["time_window"] == ["full_session"]
    assert factor_search["validation"]["failure_window_veto"]["top_n"] == 2


def _required_warmup_for_workflow(
    runtime_config: BacktestRuntimeConfig,
    workflow_config: ResearchWorkflowConfig,
) -> int:
    required_warmup = 0
    for step in workflow_config.steps:
        if step.kind != "optimize":
            continue
        parameters = step.payload["parameters"]
        for factor_filters in parameters.get("factor_filters", ()):
            strategy_params = {
                **runtime_config.strategy_params,
                **{
                    name: values[0]
                    for name, values in parameters.items()
                    if name != "factor_filters" and isinstance(values, list) and values
                },
                "factor_filters": tuple(factor_filters),
            }
            required_warmup = max(
                required_warmup,
                VwapFactorResearchConfig(**strategy_params).required_warmup_bars,
            )
    return required_warmup


def _step_requires_period_roles(step: dict[str, Any]) -> bool:
    if step.get("kind") in {"portfolio_ensemble_scan", "portfolio_volatility_managed_scan"}:
        return True
    if step.get("kind") == "backtest_matrix":
        return bool(step.get("periods"))
    validation = step.get("validation")
    if not isinstance(validation, dict):
        return False
    return "failure_window_veto" in validation or "walk_forward" in validation


def _intervals_overlap(
    left_start: object,
    left_end: object,
    right_start: object,
    right_end: object,
) -> bool:
    left_start_at = _as_utc_midnight(left_start)
    left_end_at = _as_utc_midnight(left_end)
    right_start_at = _as_utc_midnight(right_start)
    right_end_at = None if right_end is None else _as_utc_midnight(right_end)
    if right_end_at is None:
        return left_end_at > right_start_at
    return left_start_at < right_end_at and right_start_at < left_end_at


def _as_utc_midnight(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=UTC)
    raise AssertionError(f"expected date-like value, got {type(value).__name__}")


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
        backtest_manifest_root: Path | None = None,
        evaluation_output_dir: Path | None = None,
    ) -> None:
        self._accepted_specs = accepted_specs
        self._backtest_manifest_root = backtest_manifest_root
        self.backtest_calls: list[dict[str, object]] = []
        self.backtest_kwargs: list[dict[str, object]] = []
        self.backtest_matrix_calls: list[dict[str, object]] = []
        self.optimize_calls: list[dict[str, object]] = []
        self.walk_forward_calls: list[dict[str, object]] = []
        self.failure_veto_calls: list[dict[str, object]] = []
        self.failure_veto_accepted = True
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

    def run_backtest(
        self,
        *,
        end: datetime | None = None,
        start: datetime | None = None,
        strategy_params: dict[str, object] | None = None,
        output_dir: Path | None = None,
        backtest_config_path: Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> SimpleNamespace:
        self.backtest_calls.append(dict(strategy_params or {}))
        kwargs: dict[str, object] = {
            "backtest_config_path": backtest_config_path,
            "output_dir": output_dir,
            "strategy_params": dict(strategy_params or {}),
        }
        if materialized_replay_cache_dir is not None:
            kwargs["materialized_replay_cache_dir"] = materialized_replay_cache_dir
        if start is not None or end is not None:
            kwargs = {
                "end": end,
                "output_dir": output_dir,
                "start": start,
                "strategy_params": dict(strategy_params or {}),
            }
            if materialized_replay_cache_dir is not None:
                kwargs["materialized_replay_cache_dir"] = materialized_replay_cache_dir
            if backtest_config_path is not None:
                kwargs["backtest_config_path"] = backtest_config_path
        self.backtest_kwargs.append(kwargs)
        manifest_path = Path("runs/backtest/manifest.json")
        if self._backtest_manifest_root is not None:
            self._backtest_manifest_root.mkdir(parents=True, exist_ok=True)
            manifest_path = (
                self._backtest_manifest_root / f"bt-{len(self.backtest_calls):04d}.manifest.json"
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "metrics": {
                            "sharpe_ratio": str(
                                Decimal("0.5") + Decimal(len(self.backtest_calls)) / 10
                            ),
                            "total_return": str(Decimal(len(self.backtest_calls)) / 10),
                        }
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
        return SimpleNamespace(
            manifest_path=manifest_path,
            processed_bars=5,
            trading_bars=5,
        )

    def run_backtest_matrix(
        self,
        *,
        base_strategy_params: dict[str, object],
        backtest_config_path: Path | None = None,
        candidates: tuple[dict[str, object], ...],
        metrics: tuple[str, ...],
        output_root: Path,
        periods: tuple[dict[str, Any], ...],
        materialized_replay_cache_dir: Path | None = None,
    ) -> tuple[dict[str, object], ...]:
        self.backtest_matrix_calls.append(
            {
                "backtest_config_path": backtest_config_path,
                "materialized_replay_cache_dir": materialized_replay_cache_dir,
                "output_root": output_root,
            }
        )
        rows: list[dict[str, object]] = []
        for period in periods:
            for candidate in candidates:
                candidate_params = candidate["strategy_params"]
                assert isinstance(candidate_params, dict)
                strategy_params = {
                    **base_strategy_params,
                    **candidate_params,
                }
                result = self.run_backtest(
                    start=period["start"],
                    end=period["end"],
                    strategy_params=strategy_params,
                    output_dir=output_root / str(period["name"]) / str(candidate["name"]),
                    backtest_config_path=backtest_config_path,
                )
                payload = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
                manifest_metrics = payload["metrics"]
                row = {
                    "candidate": candidate["name"],
                    "manifest_path": str(result.manifest_path),
                    "period": period["name"],
                    "processed_bars": result.processed_bars,
                    "strategy_params": strategy_params,
                    "trading_bars": result.trading_bars,
                }
                row.update({metric: manifest_metrics.get(metric) for metric in metrics})
                rows.append(row)
        return tuple(rows)

    def optimize(
        self,
        *,
        parameters: dict[str, list[object]],
        objective_metric: str | None = None,
        output_root: Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> tuple[object, ...]:
        self.optimize_calls.append(
            {
                "parameters": parameters,
                "objective_metric": objective_metric,
                "output_root": output_root,
            }
        )
        if materialized_replay_cache_dir is not None:
            self.optimize_calls[-1]["materialized_replay_cache_dir"] = materialized_replay_cache_dir
        return (
            SimpleNamespace(
                parameters={"entry_bar": 1, "quantity": "2"},
                manifest_path=Path("runs/optimizer/run-0000/manifest.json"),
                manifest_hash="abc123",
                objective_value=Decimal("1.2"),
            ),
            SimpleNamespace(
                parameters={"entry_bar": 2, "quantity": "3"},
                manifest_path=Path("runs/optimizer/run-0001/manifest.json"),
                manifest_hash="def456",
                objective_value=Decimal("0.9"),
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
        materialized_replay_cache_dir: Path | None = None,
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
        if materialized_replay_cache_dir is not None:
            self.walk_forward_calls[-1]["materialized_replay_cache_dir"] = (
                materialized_replay_cache_dir
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

    def validate_optimizer_failure_window_veto(
        self,
        *,
        candidate_parameters: tuple[dict[str, object], ...],
        windows: tuple[Any, ...],
        report_only_windows: tuple[Any, ...] = (),
        constraints: tuple[Any, ...] = (),
        capital_metric_config: dict[str, object] | None = None,
        objective_metric: str | None = None,
        output_root: Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> object:
        window_metadata = tuple(window.to_metadata() for window in windows)
        report_only_metadata = tuple(window.to_metadata() for window in report_only_windows)
        self.failure_veto_calls.append(
            {
                "candidate_parameters": candidate_parameters,
                "capital_metric_config": capital_metric_config,
                "constraint_count": len(constraints),
                "objective_metric": objective_metric,
                "output_root": output_root,
                "windows": window_metadata,
                "report_only_windows": report_only_metadata,
            }
        )
        if materialized_replay_cache_dir is not None:
            self.failure_veto_calls[-1]["materialized_replay_cache_dir"] = (
                materialized_replay_cache_dir
            )
        accepted_candidates = (
            (
                {
                    "candidate_index": 0,
                    "parameters": dict(candidate_parameters[0]),
                    "windows": window_metadata,
                },
            )
            if self.failure_veto_accepted
            else ()
        )
        rejected_candidates = (
            ()
            if self.failure_veto_accepted
            else (
                {
                    "candidate_index": 0,
                    "failed_veto_windows": tuple(window["name"] for window in window_metadata),
                    "parameters": dict(candidate_parameters[0]),
                    "windows": window_metadata,
                },
            )
        )
        payload = {
            "accepted_candidates": accepted_candidates,
            "candidate_count": len(candidate_parameters),
            "decision": {
                "accepted": self.failure_veto_accepted,
                "reasons": (
                    ()
                    if self.failure_veto_accepted
                    else ("no selected candidate survived failure-window veto",)
                ),
            },
            "rejected_candidates": rejected_candidates,
            "report_only_windows": report_only_metadata,
            "veto_windows": window_metadata,
        }
        return SimpleNamespace(to_payload=lambda: payload)

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
