"""Unit tests for deterministic optimizer walk-forward split definitions."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from qts.research.optimizer import (
    BacktestWalkForwardValidationJob,
    BacktestWalkForwardValidationRunner,
    MetricConstraint,
    OptimizationResult,
    WalkForwardPlan,
    WalkForwardRobustnessPolicy,
    WalkForwardSplit,
    WalkForwardValidationResult,
    WalkForwardValidationSummary,
)


def test_walk_forward_plan_records_ordered_train_test_windows() -> None:
    split = WalkForwardSplit(
        name="split-001",
        train_start=date(2026, 1, 1),
        train_end=date(2026, 3, 31),
        test_start=date(2026, 4, 1),
        test_end=date(2026, 4, 30),
    )

    plan = WalkForwardPlan((split,))

    assert plan.splits == (split,)
    assert plan.to_metadata() == (
        {
            "name": "split-001",
            "train_start": "2026-01-01",
            "train_end": "2026-03-31",
            "test_start": "2026-04-01",
            "test_end": "2026-04-30",
        },
    )


def test_walk_forward_split_rejects_overlapping_train_and_test_windows() -> None:
    with pytest.raises(ValueError, match="non-overlapping"):
        WalkForwardSplit(
            name="split-001",
            train_start=date(2026, 1, 1),
            train_end=date(2026, 4, 15),
            test_start=date(2026, 4, 1),
            test_end=date(2026, 4, 30),
        )


def test_walk_forward_split_rejects_empty_train_window() -> None:
    with pytest.raises(ValueError, match="train_start must be before train_end"):
        WalkForwardSplit(
            name="split-001",
            train_start=date(2026, 1, 1),
            train_end=date(2026, 1, 1),
            test_start=date(2026, 2, 1),
            test_end=date(2026, 2, 28),
        )


def test_walk_forward_plan_requires_at_least_one_split() -> None:
    with pytest.raises(ValueError, match="requires at least one split"):
        WalkForwardPlan(())


def test_walk_forward_plan_rejects_duplicate_split_names() -> None:
    split = WalkForwardSplit(
        name="split-001",
        train_start=date(2026, 1, 1),
        train_end=date(2026, 1, 31),
        test_start=date(2026, 2, 1),
        test_end=date(2026, 2, 28),
    )

    with pytest.raises(ValueError, match="split names must be unique"):
        WalkForwardPlan((split, split))


def test_walk_forward_plan_rejects_cross_split_overlap() -> None:
    first = WalkForwardSplit(
        name="split-001",
        train_start=date(2026, 1, 1),
        train_end=date(2026, 1, 31),
        test_start=date(2026, 2, 1),
        test_end=date(2026, 2, 28),
    )
    overlapping = WalkForwardSplit(
        name="split-002",
        train_start=date(2026, 2, 15),
        train_end=date(2026, 3, 15),
        test_start=date(2026, 3, 16),
        test_end=date(2026, 3, 31),
    )

    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        WalkForwardPlan((first, overlapping))


def test_walk_forward_plan_rejects_out_of_order_splits() -> None:
    first = WalkForwardSplit(
        name="split-001",
        train_start=date(2026, 3, 1),
        train_end=date(2026, 3, 31),
        test_start=date(2026, 4, 1),
        test_end=date(2026, 4, 30),
    )
    earlier = WalkForwardSplit(
        name="split-002",
        train_start=date(2026, 1, 1),
        train_end=date(2026, 1, 31),
        test_start=date(2026, 2, 1),
        test_end=date(2026, 2, 28),
    )

    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        WalkForwardPlan((first, earlier))


def test_backtest_walk_forward_validation_runner_reruns_candidates_per_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runs: list[dict[str, Any]] = []

    class FakeEngine:
        def __init__(self, pipeline: FakeBacktestPipeline) -> None:
            self._pipeline = pipeline

        def run_streaming(
            self,
            output_dir: Path,
            *,
            compact_events: bool,
            equity_curve_sample_interval: int = 1,
        ) -> SimpleNamespace:
            output_dir.mkdir(parents=True)
            manifest_path = output_dir / "manifest.json"
            objective = Decimal(str(self._pipeline.params["alpha"])) + Decimal(
                "0.1" if self._pipeline.phase == "test" else "0"
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "manifest_hash": f"{self._pipeline.phase}-{self._pipeline.params['alpha']}",
                        "metrics": {
                            "sharpe_ratio": str(objective),
                            "total_trades": "10",
                        },
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            runs.append(
                {
                    "compact_events": compact_events,
                    "end": self._pipeline.end,
                    "output_dir": output_dir,
                    "params": self._pipeline.params,
                    "phase": self._pipeline.phase,
                    "start": self._pipeline.start,
                }
            )
            return SimpleNamespace(
                manifest_path=manifest_path,
                processed_bars=5,
                trading_bars=5,
            )

    class FakeBacktestPipeline:
        def __init__(
            self,
            *,
            start: Any | None = None,
            end: Any | None = None,
            params: dict[str, Any] | None = None,
            phase: str = "",
        ) -> None:
            self.start = start
            self.end = end
            self.params = params or {}
            self.phase = phase

        @classmethod
        def from_yaml(cls, path: Path) -> FakeBacktestPipeline:
            assert path == tmp_path / "backtest.yaml"
            return cls()

        def catalog(self) -> object:
            return object()

        def with_date_range(self, *, start: Any, end: Any) -> FakeBacktestPipeline:
            phase = "test" if start.isoformat().startswith("2026-04") else "train"
            return FakeBacktestPipeline(start=start, end=end, params=self.params, phase=phase)

        def with_strategy_params(self, params: dict[str, Any]) -> FakeBacktestPipeline:
            return FakeBacktestPipeline(
                start=self.start,
                end=self.end,
                params=dict(params),
                phase=self.phase,
            )

        def build_engine(self) -> tuple[FakeEngine, object]:
            return FakeEngine(self), object()

    monkeypatch.setattr(
        "qts.research.optimizer.walk_forward.BacktestPipeline",
        FakeBacktestPipeline,
    )

    plan = WalkForwardPlan(
        (
            WalkForwardSplit(
                name="split-001",
                train_start=date(2026, 1, 1),
                train_end=date(2026, 3, 31),
                test_start=date(2026, 4, 1),
                test_end=date(2026, 4, 30),
            ),
        )
    )

    results = BacktestWalkForwardValidationRunner().run(
        BacktestWalkForwardValidationJob(
            base_config_path=tmp_path / "backtest.yaml",
            candidate_parameters=({"alpha": "1"}, {"alpha": "2"}),
            objective_metric="sharpe_ratio",
            output_root=tmp_path / "walk-forward",
            plan=plan,
        )
    )

    assert [(item.split_name, item.phase, item.result.parameters) for item in results] == [
        ("split-001", "train", {"alpha": "1"}),
        ("split-001", "train", {"alpha": "2"}),
        ("split-001", "test", {"alpha": "1"}),
        ("split-001", "test", {"alpha": "2"}),
    ]
    assert [item.result.objective_value for item in results] == [
        Decimal("1"),
        Decimal("2"),
        Decimal("1.1"),
        Decimal("2.1"),
    ]
    assert [run["compact_events"] for run in runs] == [True, True, True, True]
    assert str(runs[0]["output_dir"]).endswith("split-001/train/run-0000")
    assert str(runs[2]["output_dir"]).endswith("split-001/test/run-0000")


def test_walk_forward_validation_summary_groups_window_constraint_evidence(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "manifest_hash": "abc",
                "metrics": {
                    "sharpe_ratio": "1.5",
                    "total_trades": "3",
                },
            }
        ),
        encoding="utf-8",
    )
    split = WalkForwardSplit(
        name="split-001",
        train_start=date(2026, 1, 1),
        train_end=date(2026, 3, 31),
        test_start=date(2026, 4, 1),
        test_end=date(2026, 4, 30),
    )
    result = WalkForwardValidationResult(
        split_name="split-001",
        phase="test",
        start=split.test_start,
        end=split.test_end,
        result=OptimizationResult(
            parameters={"alpha": "1"},
            manifest_path=manifest_path,
            manifest_hash="abc",
            objective_value=Decimal("1.5"),
        ),
    )

    summary = WalkForwardValidationSummary.from_results(
        (result,),
        constraints=(
            MetricConstraint(
                metric_name="total_trades",
                operator=">=",
                threshold=Decimal("5"),
            ),
        ),
    )

    assert summary.to_payload() == {
        "run_count": 1,
        "window_count": 1,
        "windows": [
            {
                "accepted_count": 0,
                "accepted_runs": (),
                "end": "2026-04-30",
                "phase": "test",
                "rejected_count": 1,
                "rejections": (
                    {
                        "manifest_hash": "abc",
                        "manifest_path": str(manifest_path),
                        "objective_value": "1.5",
                        "parameters": {"alpha": "1"},
                        "raw_rank": 1,
                        "accepted_rank": None,
                        "reasons": ("total_trades=3 failed >= 5",),
                        "rejection_reasons": ("total_trades=3 failed >= 5",),
                    },
                ),
                "run_count": 1,
                "split_name": "split-001",
                "start": "2026-04-01",
            }
        ],
    }


def test_walk_forward_robustness_policy_rejects_losing_oos_windows() -> None:
    summary = WalkForwardValidationSummary(
        windows=(
            {
                "accepted_count": 1,
                "accepted_runs": (
                    {
                        "capital_metrics": {"pnl_usd": "200"},
                        "objective_value": "1.5",
                    },
                ),
                "end": "2026-02-01",
                "phase": "test",
                "rejected_count": 0,
                "rejections": (),
                "run_count": 1,
                "split_name": "split-001",
                "start": "2026-01-01",
            },
            {
                "accepted_count": 1,
                "accepted_runs": (
                    {
                        "capital_metrics": {"pnl_usd": "-50"},
                        "objective_value": "0.4",
                    },
                ),
                "end": "2026-04-01",
                "phase": "test",
                "rejected_count": 0,
                "rejections": (),
                "run_count": 1,
                "split_name": "split-002",
                "start": "2026-03-01",
            },
            {
                "accepted_count": 1,
                "accepted_runs": (
                    {
                        "capital_metrics": {"pnl_usd": "-100"},
                        "objective_value": "-1.0",
                    },
                ),
                "end": "2026-06-01",
                "phase": "train",
                "rejected_count": 0,
                "rejections": (),
                "run_count": 1,
                "split_name": "split-003",
                "start": "2026-05-01",
            },
        )
    )

    decision = WalkForwardRobustnessPolicy(
        phases=("test",),
        min_windows=2,
        max_losing_windows=0,
        min_window_pnl_usd=Decimal("0"),
        min_total_pnl_usd=Decimal("200"),
    ).evaluate(summary)

    assert decision.accepted is False
    assert decision.to_payload() == {
        "accepted": False,
        "metrics": {
            "losing_window_count": 1,
            "min_window_best_objective": "0.4",
            "min_window_pnl_usd": "-50",
            "total_pnl_usd": "150",
            "window_count": 2,
        },
        "reasons": (
            "losing_window_count=1 failed <= 0",
            "min_window_pnl_usd=-50 failed >= 0",
            "total_pnl_usd=150 failed >= 200",
        ),
    }
