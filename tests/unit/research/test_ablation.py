from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.research import (
    AblationPlan,
    AblationReport,
    AblationReportWriter,
    AblationRun,
)


def test_ablation_plan_requires_baseline() -> None:
    with pytest.raises(ValueError, match="baseline run"):
        AblationPlan(
            baseline="baseline",
            modules=("cost_filter",),
            runs=(
                AblationRun(
                    name="cost_filter",
                    modules=("cost_filter",),
                    metrics={"sharpe": 1.2},
                ),
            ),
        )


def test_ablation_report_shows_metric_deltas(tmp_path: Path) -> None:
    report = AblationReport.from_plan(
        AblationPlan(
            baseline="baseline",
            modules=("cost_filter",),
            runs=(
                AblationRun(
                    name="baseline",
                    modules=(),
                    metrics={"sharpe": 1.0},
                    split_metrics={"IS": {"sharpe": 1.0}, "OOS": {"sharpe": 0.8}},
                ),
                AblationRun(
                    name="cost_filter",
                    modules=("cost_filter",),
                    metrics={"sharpe": 1.25},
                    split_metrics={"IS": {"sharpe": 1.3}, "OOS": {"sharpe": 1.0}},
                ),
            ),
        ),
        primary_metric="sharpe",
    )

    variant = report.variant("cost_filter")
    assert variant.metric_deltas["sharpe"] == pytest.approx(0.25)
    assert variant.is_delta == pytest.approx(0.3)
    assert variant.oos_delta == pytest.approx(0.2)

    paths = AblationReportWriter(tmp_path).write(report)
    assert "sharpe_delta: 0.25" in paths.markdown_path.read_text(encoding="utf-8")
    payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    assert payload["variants"][1]["metric_deltas"]["sharpe"] == pytest.approx(0.25)


def test_ablation_plan_requires_each_declared_module_contribution() -> None:
    with pytest.raises(ValueError, match="missing single-module ablation runs"):
        AblationPlan(
            baseline="baseline",
            modules=("entry_filter", "exit_rule"),
            runs=(
                AblationRun(
                    name="baseline",
                    modules=(),
                    metrics={"sharpe": 1.0},
                ),
                AblationRun(
                    name="entry_filter",
                    modules=("entry_filter",),
                    metrics={"sharpe": 1.1},
                ),
            ),
        )


def test_ablation_loads_runs_from_backtest_matrix_summary() -> None:
    plan = AblationPlan.from_backtest_matrix_summary(
        {
            "metrics": ["sharpe_ratio", "total_trades"],
            "rows": [
                {
                    "candidate": "baseline",
                    "period": "IS",
                    "sharpe_ratio": 1.0,
                    "total_trades": 10,
                },
                {
                    "candidate": "candidate_a",
                    "period": "IS",
                    "sharpe_ratio": 1.25,
                    "total_trades": 8,
                },
            ],
        },
        baseline="baseline",
        module_map={"candidate_a": ["mom_filter"]},
    )

    assert plan.modules == ("mom_filter",)
    assert plan.runs[0].name == "baseline"
    assert plan.runs[1].metrics["sharpe_ratio"] == pytest.approx(1.25)
    assert plan.runs[1].trade_count == 8


def test_ablation_rejects_missing_baseline_in_summary() -> None:
    with pytest.raises(ValueError, match="baseline"):
        AblationPlan.from_backtest_matrix_summary(
            {
                "metrics": ["sharpe_ratio"],
                "rows": [{"candidate": "candidate_a", "sharpe_ratio": 1.1}],
            },
            baseline="baseline",
            module_map={"candidate_a": ["mom_filter"]},
        )


def test_ablation_maps_candidate_modules() -> None:
    plan = AblationPlan.from_backtest_matrix_summary(
        {
            "metrics": ["sharpe_ratio"],
            "rows": [
                {"candidate": "baseline", "period": "IS", "sharpe_ratio": 1.0},
                {"candidate": "candidate_a", "period": "IS", "sharpe_ratio": 1.1},
            ],
        },
        baseline="baseline",
        module_map={"candidate_a": ["mom_filter"]},
    )

    assert plan.runs[1].modules == ("mom_filter",)


def test_ablation_flags_is_only_improvement() -> None:
    report = AblationReport.from_plan(
        AblationPlan(
            baseline="baseline",
            modules=("entry_filter",),
            runs=(
                AblationRun(
                    name="baseline",
                    modules=(),
                    metrics={"sharpe": 1.0},
                    split_metrics={"IS": {"sharpe": 1.0}, "OOS": {"sharpe": 1.0}},
                ),
                AblationRun(
                    name="entry_filter",
                    modules=("entry_filter",),
                    metrics={"sharpe": 1.1},
                    split_metrics={"IS": {"sharpe": 1.3}, "OOS": {"sharpe": 0.9}},
                ),
            ),
        ),
        primary_metric="sharpe",
    )

    assert report.variant("entry_filter").unstable is True


def test_ablation_summary_records_trade_count_delta() -> None:
    report = AblationReport.from_plan(
        AblationPlan(
            baseline="baseline",
            modules=("exit_rule",),
            runs=(
                AblationRun(
                    name="baseline",
                    modules=(),
                    metrics={"sharpe": 1.0},
                    trade_count=10,
                ),
                AblationRun(
                    name="exit_rule",
                    modules=("exit_rule",),
                    metrics={"sharpe": 1.1},
                    trade_count=7,
                    cost_stress_metrics={"high_cost": {"sharpe": 0.8}},
                ),
            ),
        ),
        primary_metric="sharpe",
    )

    variant = report.variant("exit_rule")
    assert variant.trade_count_delta == -3
    assert variant.cost_stress_deltas["high_cost"]["sharpe"] == pytest.approx(-0.2)
