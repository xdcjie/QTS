"""Unit tests for optimizer failure-window veto validation."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from qts.research.optimizer import (
    FailureWindow,
    FailureWindowVetoJob,
    FailureWindowVetoResult,
    FailureWindowVetoRunner,
    FailureWindowVetoSummary,
    MetricConstraint,
    OptimizationResult,
)


def test_failure_window_rejects_empty_names_and_inverted_dates() -> None:
    with pytest.raises(ValueError, match="failure window name must not be empty"):
        FailureWindow(name=" ", start=date(2026, 1, 1), end=date(2026, 1, 2))

    with pytest.raises(ValueError, match="start must be before end"):
        FailureWindow(name="crash", start=date(2026, 1, 2), end=date(2026, 1, 1))

    window = FailureWindow(name="crash", start=date(2026, 1, 1), end=date(2026, 1, 2))

    assert window.to_metadata() == {
        "end": "2026-01-02",
        "name": "crash",
        "report_only": False,
        "start": "2026-01-01",
    }


@pytest.mark.parametrize("name", ("../escape", "crash/2024", "crash\\2024", ".", ".."))
def test_failure_window_rejects_unsafe_path_segment_names(name: str) -> None:
    with pytest.raises(ValueError, match="failure window name must be a safe path segment"):
        FailureWindow(name=name, start=date(2026, 1, 1), end=date(2026, 1, 2))


def test_failure_window_veto_job_rejects_duplicate_window_names(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate window names"):
        FailureWindowVetoJob(
            base_config_path=tmp_path / "backtest.yaml",
            candidate_parameters=({"alpha": "1"},),
            objective_metric="sharpe_ratio",
            output_root=tmp_path / "failure-veto",
            windows=(
                FailureWindow(
                    name="crash",
                    start=date(2026, 1, 1),
                    end=date(2026, 1, 31),
                ),
                FailureWindow(
                    name="crash",
                    start=date(2026, 2, 1),
                    end=date(2026, 2, 28),
                ),
            ),
        )

    with pytest.raises(ValueError, match="duplicate window names"):
        FailureWindowVetoJob(
            base_config_path=tmp_path / "backtest.yaml",
            candidate_parameters=({"alpha": "1"},),
            objective_metric="sharpe_ratio",
            output_root=tmp_path / "failure-veto",
            windows=(
                FailureWindow(
                    name="crash",
                    start=date(2026, 1, 1),
                    end=date(2026, 1, 31),
                ),
            ),
            report_only_windows=(
                FailureWindow(
                    name="crash",
                    start=date(2026, 2, 1),
                    end=date(2026, 2, 28),
                ),
            ),
        )


def test_failure_window_veto_runner_reruns_candidates_for_veto_and_report_only_windows(
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
                "0.5" if self._pipeline.window_name == "rebound" else "0"
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "manifest_hash": (
                            f"{self._pipeline.window_name}-{self._pipeline.params['alpha']}"
                        ),
                        "metrics": {
                            "sharpe_ratio": str(objective),
                            "total_return": "0.01",
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
                    "start": self._pipeline.start,
                    "window_name": self._pipeline.window_name,
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
            window_name: str = "",
        ) -> None:
            self.start = start
            self.end = end
            self.params = params or {}
            self.window_name = window_name

        @classmethod
        def from_yaml(cls, path: Path) -> FakeBacktestPipeline:
            assert path == tmp_path / "backtest.yaml"
            return cls()

        def catalog(self) -> object:
            return object()

        def with_date_range(self, *, start: Any, end: Any) -> FakeBacktestPipeline:
            window_name = "crash" if start.date() == date(2026, 1, 1) else "rebound"
            return FakeBacktestPipeline(
                start=start,
                end=end,
                params=self.params,
                window_name=window_name,
            )

        def with_strategy_params(self, params: dict[str, Any]) -> FakeBacktestPipeline:
            return FakeBacktestPipeline(
                start=self.start,
                end=self.end,
                params=dict(params),
                window_name=self.window_name,
            )

        def build_engine(self) -> tuple[FakeEngine, object]:
            return FakeEngine(self), object()

    monkeypatch.setattr(
        "qts.research.optimizer.failure_veto.BacktestPipeline",
        FakeBacktestPipeline,
    )

    results = FailureWindowVetoRunner().run(
        FailureWindowVetoJob(
            base_config_path=tmp_path / "backtest.yaml",
            candidate_parameters=({"alpha": "1"}, {"alpha": "2"}),
            objective_metric="sharpe_ratio",
            output_root=tmp_path / "failure-veto",
            windows=(
                FailureWindow(
                    name="crash",
                    start=date(2026, 1, 1),
                    end=date(2026, 1, 31),
                ),
            ),
            report_only_windows=(
                FailureWindow(
                    name="rebound",
                    start=date(2026, 2, 1),
                    end=date(2026, 2, 28),
                ),
            ),
        )
    )

    assert [(item.candidate_index, item.window_name, item.report_only) for item in results] == [
        (0, "crash", False),
        (1, "crash", False),
        (0, "rebound", True),
        (1, "rebound", True),
    ]
    assert [item.result.objective_value for item in results] == [
        Decimal("1"),
        Decimal("2"),
        Decimal("1.5"),
        Decimal("2.5"),
    ]
    assert results[0].candidate_id.startswith("candidate-0000-")
    assert results[0].candidate_id == results[2].candidate_id
    assert [run["compact_events"] for run in runs] == [True, True, True, True]
    assert str(runs[0]["output_dir"]).endswith("crash/veto/run-0000")
    assert str(runs[2]["output_dir"]).endswith("rebound/report-only/run-0000")


def test_failure_window_veto_summary_rejects_candidate_when_any_veto_window_fails(
    tmp_path: Path,
) -> None:
    candidate_id = "candidate-0000-deadbeef0000"
    passing = _veto_result(
        tmp_path / "passing",
        candidate_id=candidate_id,
        window_name="stress-a",
        total_return="0.02",
        report_only=False,
    )
    failing = _veto_result(
        tmp_path / "failing",
        candidate_id=candidate_id,
        window_name="stress-b",
        total_return="-0.01",
        report_only=False,
    )

    summary = FailureWindowVetoSummary.from_results(
        (passing, failing),
        constraints=(MetricConstraint("pnl_usd", ">=", Decimal("0")),),
    )

    payload = summary.to_payload()
    assert payload["candidate_count"] == 1
    assert payload["accepted_candidates"] == ()
    assert payload["decision"] == {
        "accepted": False,
        "reasons": ("no selected candidate survived failure-window veto",),
    }
    assert payload["rejected_candidates"][0]["candidate_id"] == candidate_id
    assert payload["rejected_candidates"][0]["parameters"] == {"alpha": "1"}
    assert payload["rejected_candidates"][0]["failed_veto_windows"] == ("stress-b",)
    assert [window["window_name"] for window in payload["veto_windows"]] == [
        "stress-a",
        "stress-b",
    ]


def test_report_only_windows_are_evidence_but_do_not_rescue_rejected_candidates(
    tmp_path: Path,
) -> None:
    candidate_id = "candidate-0000-deadbeef0000"
    failing_veto = _veto_result(
        tmp_path / "failing-veto",
        candidate_id=candidate_id,
        window_name="crash",
        total_return="-0.01",
        report_only=False,
    )
    passing_report_only = _veto_result(
        tmp_path / "passing-report-only",
        candidate_id=candidate_id,
        window_name="rebound",
        total_return="0.10",
        report_only=True,
    )

    summary = FailureWindowVetoSummary.from_results(
        (failing_veto, passing_report_only),
        constraints=(MetricConstraint("pnl_usd", ">=", Decimal("0")),),
    )

    payload = summary.to_payload()
    assert payload["accepted_candidates"] == ()
    assert payload["rejected_candidates"][0]["failed_veto_windows"] == ("crash",)
    assert payload["report_only_windows"][0]["window_name"] == "rebound"
    assert payload["report_only_windows"][0]["accepted_count"] == 1
    assert payload["report_only_windows"][0]["rejected_count"] == 0


def test_failure_window_veto_summary_includes_accepted_candidate_parameters(
    tmp_path: Path,
) -> None:
    candidate_id = "candidate-0000-deadbeef0000"
    result = _veto_result(
        tmp_path / "passing-veto",
        candidate_id=candidate_id,
        window_name="crash",
        total_return="0.01",
        report_only=False,
        parameters={"alpha": Decimal("1.25"), "lags": (1, 2), "enabled": True},
    )

    summary = FailureWindowVetoSummary.from_results(
        (result,),
        constraints=(MetricConstraint("pnl_usd", ">=", Decimal("0")),),
    )

    payload = summary.to_payload()
    assert payload["rejected_candidates"] == ()
    assert payload["accepted_candidates"][0]["candidate_id"] == candidate_id
    assert payload["accepted_candidates"][0]["parameters"] == {
        "alpha": "1.25",
        "enabled": True,
        "lags": [1, 2],
    }


def _veto_result(
    path: Path,
    *,
    candidate_id: str,
    window_name: str,
    total_return: str,
    report_only: bool,
    parameters: dict[str, Any] | None = None,
) -> FailureWindowVetoResult:
    path.mkdir(parents=True)
    manifest_path = path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "manifest_hash": f"{window_name}-{total_return}",
                "metrics": {"total_return": total_return},
                "runtime_topology": {
                    "accounts": [
                        {
                            "account_id": "acct-backtest",
                            "initial_cash": "100000",
                        }
                    ]
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return FailureWindowVetoResult(
        candidate_index=0,
        candidate_id=candidate_id,
        window_name=window_name,
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
        report_only=report_only,
        result=OptimizationResult(
            parameters={"alpha": "1"} if parameters is None else parameters,
            manifest_path=manifest_path,
            manifest_hash=f"{window_name}-{total_return}",
            objective_value=Decimal(total_return),
        ),
    )
