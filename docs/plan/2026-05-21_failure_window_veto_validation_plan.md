# Failure-Window Veto Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a research-only failure-window veto gate that rejects optimizer candidates that fail predeclared 2022-2024 adverse windows and prevents 2025-2026 report-only performance from rescuing them.

**Architecture:** `qts.research.optimizer` owns the failure-window domain model, runner, summary, and decision evidence. `ResearchSession` exposes a public delegation method, and `ResearchWorkflowRunner` parses workflow YAML, writes deterministic evidence, and blocks optimize steps when configured. Strategy code, runtime actors, risk, order management, execution, and account state remain unchanged.

**Tech Stack:** Python dataclasses, existing `BacktestPipeline`, existing `MetricConstraint` / `OptimizerValidationSummary` evidence path, YAML workflow configs, pytest, ruff, mypy, guardrails.

---

## Domain Gate

Domain fact / invariant:

```text
A candidate that fails any predeclared veto window is rejected for promotion.
Later report-only windows must not compensate for, override, or tune away that
failure decision.
```

Correct owner or abstraction boundary:

```text
qts.research.optimizer owns research validation evidence. ResearchWorkflowRunner
orchestrates configured validation through ResearchSession. No Strategy SDK,
runtime, risk, order, execution, broker, account, or portfolio behavior changes.
```

Forbidden shortcut:

```text
Do not aggregate 2025-2026 report-only PnL or objective values into the veto
decision. Do not add strategy factor_filters or backtest-only trading paths.
```

Required gates / verification:

```text
Focused red/green tests for failure-window veto model, runner, summary, workflow
blocking, workflow config parsing, and report-only exclusion; private-helper
inspection for changed Python files; make format; make lint; make guardrails;
make typecheck; make test-unit.
```

## File Structure

- Create `backend/src/qts/research/optimizer/failure_veto.py`: failure-window window model, backtest rerun job, runner, summary, and decision.
- Modify `backend/src/qts/research/optimizer/__init__.py`: export the new public optimizer validation types.
- Modify `backend/src/qts/research/session.py`: add `validate_optimizer_failure_window_veto(...)` facade method that delegates to the new runner and summary owner.
- Modify `backend/src/qts/research/workflow.py`: parse `validation.failure_window_veto`, call the session facade, write summary artifacts, expose outputs, and block when configured.
- Modify `configs/research/workflows/vwap_factor_gc_long_search.yaml`, `configs/research/workflows/vwap_factor_si_long_search.yaml`, `configs/research/workflows/vwap_factor_gc_5m_long_search.yaml`, `configs/research/workflows/vwap_factor_si_5m_long_search.yaml`, `configs/research/workflows/vwap_factor_gc_15m_long_search.yaml`, and `configs/research/workflows/vwap_factor_si_15m_long_search.yaml`: add the first fixed 2022-2024 veto gate to long-sample workflows only.
- Create `tests/unit/research/test_optimizer_failure_veto.py`: unit tests for model validation, runner reruns, summary decisions, and report-only exclusion.
- Modify `tests/unit/research/test_research_session.py`: verify the `ResearchSession` facade delegates to the new runner with the base backtest config.
- Modify `tests/unit/research/test_research_workflow.py`: verify workflow parsing, calls, outputs, blocking behavior, and long-sample config coverage.

## Task 1: Failure Veto Optimizer Owner

**Files:**
- Create: `backend/src/qts/research/optimizer/failure_veto.py`
- Modify: `backend/src/qts/research/optimizer/__init__.py`
- Test: `tests/unit/research/test_optimizer_failure_veto.py`

- [ ] **Step 1: Write failing failure-veto unit tests**

Create `tests/unit/research/test_optimizer_failure_veto.py` with tests covering ordered windows, runner output paths, one failed veto window rejecting a candidate, and report-only windows not rescuing a rejection.

```python
"""Unit tests for failure-window veto optimizer validation."""

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
    FailureWindowVetoRunner,
    FailureWindowVetoSummary,
    MetricConstraint,
)


def _manifest(
    path: Path,
    *,
    manifest_hash: str,
    sharpe: str,
    total_return: str,
    drawdown: str,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "manifest_hash": manifest_hash,
                "metrics": {
                    "max_drawdown": drawdown,
                    "sharpe_ratio": sharpe,
                    "total_return": total_return,
                },
                "runtime_topology": {
                    "accounts": [{"initial_cash": "100000"}],
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def test_failure_window_rejects_empty_or_inverted_dates() -> None:
    with pytest.raises(ValueError, match="failure window name must not be empty"):
        FailureWindow(name="", start=date(2024, 1, 1), end=date(2025, 1, 1))

    with pytest.raises(ValueError, match="start must be before end"):
        FailureWindow(name="failure-2024", start=date(2025, 1, 1), end=date(2024, 1, 1))


def test_failure_veto_runner_reruns_candidates_for_veto_and_report_windows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runs: list[dict[str, Any]] = []

    class FakeEngine:
        def __init__(self, pipeline: FakeBacktestPipeline) -> None:
            self._pipeline = pipeline

        def run_streaming(self, output_dir: Path, *, compact_events: bool) -> SimpleNamespace:
            manifest_path = _manifest(
                output_dir / "manifest.json",
                manifest_hash=f"{self._pipeline.window_name}-{self._pipeline.params['alpha']}",
                sharpe="10",
                total_return="0.01",
                drawdown="0.01",
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
            return SimpleNamespace(manifest_path=manifest_path)

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
            name = "failure-2024" if start.date().isoformat() == "2024-01-01" else "report-2025"
            return FakeBacktestPipeline(start=start, end=end, params=self.params, window_name=name)

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
            windows=(FailureWindow("failure-2024", date(2024, 1, 1), date(2025, 1, 1)),),
            report_only_windows=(
                FailureWindow("report-2025", date(2025, 1, 1), date(2026, 1, 1), report_only=True),
            ),
        )
    )

    assert [(item.candidate_index, item.window_name, item.report_only) for item in results] == [
        (0, "failure-2024", False),
        (1, "failure-2024", False),
        (0, "report-2025", True),
        (1, "report-2025", True),
    ]
    assert [run["compact_events"] for run in runs] == [True, True, True, True]
    assert str(runs[0]["output_dir"]).endswith("failure-2024/veto/run-0000")
    assert str(runs[2]["output_dir"]).endswith("report-2025/report-only/run-0000")


def test_failure_veto_summary_rejects_candidate_failed_in_any_veto_window(
    tmp_path: Path,
) -> None:
    from qts.research.optimizer.failure_veto import FailureWindowVetoResult
    from qts.research.optimizer.result import OptimizationResult

    good = _manifest(
        tmp_path / "good.json",
        manifest_hash="good",
        sharpe="10",
        total_return="0.01",
        drawdown="0.01",
    )
    bad = _manifest(
        tmp_path / "bad.json",
        manifest_hash="bad",
        sharpe="-5",
        total_return="-0.01",
        drawdown="0.01",
    )
    report_good = _manifest(
        tmp_path / "report-good.json",
        manifest_hash="report-good",
        sharpe="500",
        total_return="0.50",
        drawdown="0.01",
    )
    results = (
        FailureWindowVetoResult(
            candidate_index=0,
            candidate_id="candidate-0000",
            window_name="failure-2023",
            start=date(2023, 1, 1),
            end=date(2024, 1, 1),
            report_only=False,
            result=OptimizationResult({"alpha": "1"}, good, "good", Decimal("10")),
        ),
        FailureWindowVetoResult(
            candidate_index=0,
            candidate_id="candidate-0000",
            window_name="failure-2024",
            start=date(2024, 1, 1),
            end=date(2025, 1, 1),
            report_only=False,
            result=OptimizationResult({"alpha": "1"}, bad, "bad", Decimal("-5")),
        ),
        FailureWindowVetoResult(
            candidate_index=0,
            candidate_id="candidate-0000",
            window_name="report-2025-2026",
            start=date(2025, 1, 1),
            end=date(2026, 4, 10),
            report_only=True,
            result=OptimizationResult({"alpha": "1"}, report_good, "report-good", Decimal("500")),
        ),
    )

    summary = FailureWindowVetoSummary.from_results(
        results,
        constraints=(
            MetricConstraint("pnl_usd", ">", Decimal("0")),
            MetricConstraint("max_drawdown", "<=", Decimal("0.05")),
        ),
        capital_metric_config={"margin_proxy": "12000"},
    )

    payload = summary.to_payload()
    assert payload["decision"]["accepted"] is False
    assert payload["accepted_candidates"] == ()
    assert payload["rejected_candidates"][0]["candidate_id"] == "candidate-0000"
    assert "report-2025-2026" in {
        item["window_name"] for item in payload["report_only_windows"]
    }
    assert payload["rejected_candidates"][0]["failed_veto_windows"] == ("failure-2024",)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/unit/research/test_optimizer_failure_veto.py -q
```

Expected: fail with import errors for `FailureWindow`, `FailureWindowVetoJob`, `FailureWindowVetoRunner`, and `FailureWindowVetoSummary`.

- [ ] **Step 3: Implement `failure_veto.py`**

Create `backend/src/qts/research/optimizer/failure_veto.py`. Use class-owned validation and shared module-private helpers only for JSON/date/Decimal conversions needed by multiple classes.

```python
"""Failure-window veto validation for optimizer candidates."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.backtest.pipeline import BacktestPipeline
from qts.research.optimizer.constraints import OptimizationConstraint
from qts.research.optimizer.result import OptimizationResult
from qts.research.optimizer.runner import extract_objective_from_manifest
from qts.research.optimizer.validation import OptimizerValidationSummary


@dataclass(frozen=True, slots=True)
class FailureWindow:
    """One deterministic failure-veto or report-only date window."""

    name: str
    start: date
    end: date
    report_only: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("failure window name must not be empty")
        if self.start >= self.end:
            raise ValueError("failure window start must be before end")

    def to_metadata(self) -> dict[str, Any]:
        return {
            "end": self.end.isoformat(),
            "name": self.name,
            "report_only": self.report_only,
            "start": self.start.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class FailureWindowVetoJob:
    """Backtest-pipeline rerun job for failure-window veto evidence."""

    base_config_path: Path
    candidate_parameters: tuple[dict[str, Any], ...]
    objective_metric: str
    output_root: Path
    windows: tuple[FailureWindow, ...]
    report_only_windows: tuple[FailureWindow, ...] = ()

    def __init__(
        self,
        *,
        base_config_path: Path,
        candidate_parameters: Iterable[Mapping[str, Any]],
        objective_metric: str,
        output_root: Path,
        windows: Sequence[FailureWindow],
        report_only_windows: Sequence[FailureWindow] = (),
    ) -> None:
        candidates = tuple(dict(parameters) for parameters in candidate_parameters)
        veto_windows = tuple(windows)
        report_windows = tuple(
            FailureWindow(window.name, window.start, window.end, report_only=True)
            for window in report_only_windows
        )
        if not candidates:
            raise ValueError("candidate_parameters must not be empty")
        if not objective_metric.strip():
            raise ValueError("objective_metric must not be empty")
        if not veto_windows:
            raise ValueError("failure-window veto requires at least one veto window")
        object.__setattr__(self, "base_config_path", Path(base_config_path))
        object.__setattr__(self, "candidate_parameters", candidates)
        object.__setattr__(self, "objective_metric", objective_metric)
        object.__setattr__(self, "output_root", Path(output_root))
        object.__setattr__(self, "windows", veto_windows)
        object.__setattr__(self, "report_only_windows", report_windows)


@dataclass(frozen=True, slots=True)
class FailureWindowVetoResult:
    """One candidate result for one veto or report-only window."""

    candidate_index: int
    candidate_id: str
    window_name: str
    start: date
    end: date
    report_only: bool
    result: OptimizationResult


class FailureWindowVetoRunner:
    """Rerun selected optimizer candidates across failure-veto windows."""

    def run(self, job: FailureWindowVetoJob) -> tuple[FailureWindowVetoResult, ...]:
        job.output_root.mkdir(parents=True, exist_ok=True)
        base_pipeline = BacktestPipeline.from_yaml(job.base_config_path)
        base_pipeline.catalog()
        results: list[FailureWindowVetoResult] = []
        for window in (*job.windows, *job.report_only_windows):
            role = "report-only" if window.report_only else "veto"
            window_pipeline = base_pipeline.with_date_range(
                start=_date_boundary(window.start),
                end=_date_boundary(window.end),
            )
            for index, parameters in enumerate(job.candidate_parameters):
                candidate_id = _candidate_id(index, parameters)
                run_dir = job.output_root / window.name / role / f"run-{index:04d}"
                run_pipeline = window_pipeline.with_strategy_params(parameters)
                engine, _bundle = run_pipeline.build_engine()
                stream_result = engine.run_streaming(run_dir, compact_events=True)
                manifest_path = Path(stream_result.manifest_path)
                payload = _read_manifest(manifest_path)
                results.append(
                    FailureWindowVetoResult(
                        candidate_index=index,
                        candidate_id=candidate_id,
                        window_name=window.name,
                        start=window.start,
                        end=window.end,
                        report_only=window.report_only,
                        result=OptimizationResult(
                            parameters=dict(parameters),
                            manifest_path=manifest_path,
                            manifest_hash=str(payload.get("manifest_hash", "")),
                            objective_value=extract_objective_from_manifest(
                                payload,
                                job.objective_metric,
                            ),
                        ),
                    )
                )
        return tuple(results)


@dataclass(frozen=True, slots=True)
class FailureWindowVetoSummary:
    """Candidate-level failure-window veto evidence."""

    candidate_count: int
    accepted_candidates: tuple[dict[str, Any], ...]
    rejected_candidates: tuple[dict[str, Any], ...]
    veto_windows: tuple[dict[str, Any], ...]
    report_only_windows: tuple[dict[str, Any], ...]
    decision: dict[str, Any]

    @classmethod
    def from_results(
        cls,
        results: Sequence[FailureWindowVetoResult],
        *,
        constraints: Iterable[OptimizationConstraint],
        capital_metric_config: Mapping[str, Any] | None = None,
    ) -> FailureWindowVetoSummary:
        materialized = tuple(constraints)
        grouped: dict[str, list[FailureWindowVetoResult]] = {}
        for result in results:
            grouped.setdefault(result.candidate_id, []).append(result)

        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        veto_evidence: list[dict[str, Any]] = []
        report_evidence: list[dict[str, Any]] = []

        for candidate_id, candidate_results in sorted(grouped.items()):
            candidate_payloads: list[dict[str, Any]] = []
            failed_windows: list[str] = []
            parameters = dict(candidate_results[0].result.parameters)
            for candidate_result in sorted(
                candidate_results,
                key=lambda item: (item.report_only, item.window_name, item.candidate_index),
            ):
                summary = OptimizerValidationSummary.from_results(
                    (candidate_result.result,),
                    materialized,
                    capital_metric_config=(
                        None if capital_metric_config is None else dict(capital_metric_config)
                    ),
                )
                payload = {
                    "candidate_id": candidate_id,
                    "end": candidate_result.end.isoformat(),
                    "report_only": candidate_result.report_only,
                    "start": candidate_result.start.isoformat(),
                    "summary": summary.to_payload(),
                    "window_name": candidate_result.window_name,
                }
                candidate_payloads.append(payload)
                if candidate_result.report_only:
                    report_evidence.append(payload)
                else:
                    veto_evidence.append(payload)
                    if summary.rejected_count:
                        failed_windows.append(candidate_result.window_name)

            candidate_evidence = {
                "candidate_id": candidate_id,
                "parameters": _json_safe_parameters(parameters),
                "windows": tuple(candidate_payloads),
            }
            if failed_windows:
                rejected.append(
                    {
                        **candidate_evidence,
                        "failed_veto_windows": tuple(failed_windows),
                    }
                )
            else:
                accepted.append(candidate_evidence)

        reasons = (
            ("no selected candidate survived failure-window veto",)
            if not accepted and grouped
            else ()
        )
        return cls(
            candidate_count=len(grouped),
            accepted_candidates=tuple(accepted),
            rejected_candidates=tuple(rejected),
            veto_windows=tuple(veto_evidence),
            report_only_windows=tuple(report_evidence),
            decision={"accepted": bool(accepted), "reasons": reasons},
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "accepted_candidates": self.accepted_candidates,
            "candidate_count": self.candidate_count,
            "decision": self.decision,
            "rejected_candidates": self.rejected_candidates,
            "report_only_windows": self.report_only_windows,
            "veto_windows": self.veto_windows,
        }


def _candidate_id(index: int, parameters: Mapping[str, Any]) -> str:
    payload = json.dumps(
        _json_safe_parameters(dict(parameters)),
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"candidate-{index:04d}-{digest}"


def _json_safe_parameters(parameters: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(name): _json_safe_parameter_value(value, path=str(name))
        for name, value in parameters.items()
    }


def _json_safe_parameter_value(value: Any, *, path: str) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"optimizer parameter {path} must be finite")
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"optimizer parameter {path} must be finite")
        return value
    if isinstance(value, (list, tuple)):
        return [
            _json_safe_parameter_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"unsupported optimizer parameter value at {path}: {type(value).__name__}")


def _date_boundary(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _read_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"failure-window manifest must be a JSON object: {path}")
    return payload


__all__ = [
    "FailureWindow",
    "FailureWindowVetoJob",
    "FailureWindowVetoResult",
    "FailureWindowVetoRunner",
    "FailureWindowVetoSummary",
]
```

- [ ] **Step 4: Export the new optimizer types**

Modify `backend/src/qts/research/optimizer/__init__.py`:

```python
from qts.research.optimizer.failure_veto import (
    FailureWindow,
    FailureWindowVetoJob,
    FailureWindowVetoResult,
    FailureWindowVetoRunner,
    FailureWindowVetoSummary,
)
```

Add the same names to `__all__`.

- [ ] **Step 5: Run focused optimizer tests**

Run:

```bash
uv run pytest tests/unit/research/test_optimizer_failure_veto.py tests/unit/research/test_optimizer_walk_forward.py tests/unit/research/test_optimizer_constraints.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit Task 1**

Commit only the files from this task. Do not include pre-existing dirty files.

```bash
git add backend/src/qts/research/optimizer/failure_veto.py backend/src/qts/research/optimizer/__init__.py tests/unit/research/test_optimizer_failure_veto.py
git commit -m "feat: add failure-window veto validation"
```

## Task 2: ResearchSession Facade

**Files:**
- Modify: `backend/src/qts/research/session.py`
- Test: `tests/unit/research/test_research_session.py`

- [ ] **Step 1: Write failing session delegation test**

Add this test near `test_research_session_delegates_walk_forward_validation_to_backtest_runner` in `tests/unit/research/test_research_session.py`.

```python
def test_research_session_delegates_failure_window_veto_to_backtest_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import date
    from decimal import Decimal

    from qts.research.optimizer import FailureWindow, MetricConstraint

    calls: list[object] = []

    class FakeRunner:
        def run(self, job: object) -> tuple[object, ...]:
            calls.append(job)
            return ()

    class FakeSummary:
        @classmethod
        def from_results(
            cls,
            results: object,
            *,
            constraints: object,
            capital_metric_config: object = None,
        ) -> object:
            calls.append(
                {
                    "capital_metric_config": capital_metric_config,
                    "constraints": constraints,
                    "results": results,
                }
            )
            return cls()

        def to_payload(self) -> dict[str, object]:
            return {"decision": {"accepted": True, "reasons": ()}}

    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    monkeypatch.setattr("qts.research.session.FailureWindowVetoRunner", FakeRunner)
    monkeypatch.setattr("qts.research.session.FailureWindowVetoSummary", FakeSummary)

    session = ResearchSession.from_yaml(config_path)
    summary = session.validate_optimizer_failure_window_veto(
        candidate_parameters=({"alpha": "1"},),
        windows=(FailureWindow("failure-2024", date(2024, 1, 1), date(2025, 1, 1)),),
        report_only_windows=(),
        constraints=(MetricConstraint("pnl_usd", ">", Decimal("0")),),
        capital_metric_config={"margin_proxy": "12000"},
        objective_metric="sharpe_ratio",
        output_root=tmp_path / "failure-veto",
    )

    assert summary.to_payload()["decision"]["accepted"] is True
    job = calls[0]
    assert job.base_config_path == session.config.backtest_config_path
    assert job.candidate_parameters == ({"alpha": "1"},)
    assert job.output_root == tmp_path / "failure-veto"
    assert calls[1]["capital_metric_config"] == {"margin_proxy": "12000"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/unit/research/test_research_session.py::test_research_session_delegates_failure_window_veto_to_backtest_runner -q
```

Expected: fail because `ResearchSession.validate_optimizer_failure_window_veto` and session imports do not exist.

- [ ] **Step 3: Add the facade method**

Modify `backend/src/qts/research/session.py` imports to include:

```python
from qts.research.optimizer import (
    FailureWindow,
    FailureWindowVetoJob,
    FailureWindowVetoRunner,
    FailureWindowVetoSummary,
)
```

Add this method to `ResearchSession` after `validate_optimizer_walk_forward(...)`:

```python
    def validate_optimizer_failure_window_veto(
        self,
        *,
        candidate_parameters: Sequence[Mapping[str, Any]],
        windows: Sequence[FailureWindow],
        report_only_windows: Sequence[FailureWindow] = (),
        constraints: Iterable[OptimizationConstraint] = (),
        capital_metric_config: Mapping[str, Any] | None = None,
        objective_metric: str | None = None,
        output_root: Path | None = None,
    ) -> FailureWindowVetoSummary:
        """Rerun selected optimizer candidates across failure-veto windows."""
        results = FailureWindowVetoRunner().run(
            FailureWindowVetoJob(
                base_config_path=self._config.backtest_config_path,
                candidate_parameters=tuple(dict(parameters) for parameters in candidate_parameters),
                objective_metric=objective_metric or self._config.objective_metric,
                output_root=output_root or self._config.output_root / "failure-veto",
                windows=tuple(windows),
                report_only_windows=tuple(report_only_windows),
            )
        )
        return FailureWindowVetoSummary.from_results(
            results,
            constraints=constraints,
            capital_metric_config=(
                None if capital_metric_config is None else dict(capital_metric_config)
            ),
        )
```

- [ ] **Step 4: Run focused session tests**

Run:

```bash
uv run pytest tests/unit/research/test_research_session.py::test_research_session_delegates_failure_window_veto_to_backtest_runner tests/unit/research/test_research_session.py::test_research_session_delegates_walk_forward_validation_to_backtest_runner -q
```

Expected: both tests pass.

- [ ] **Step 5: Commit Task 2**

```bash
git add backend/src/qts/research/session.py tests/unit/research/test_research_session.py
git commit -m "feat: expose failure-window veto on research session"
```

## Task 3: Workflow Parsing, Evidence Output, and Blocking

**Files:**
- Modify: `backend/src/qts/research/workflow.py`
- Test: `tests/unit/research/test_research_workflow.py`

- [ ] **Step 1: Write failing workflow tests**

Add one passing-output test and one blocking test near the existing walk-forward workflow test in `tests/unit/research/test_research_workflow.py`.

```python
def test_runner_runs_failure_window_veto_for_top_optimizer_candidates(tmp_path: Path) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: failure-window-veto
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    output_root: optimizer-output
    parameters:
      alpha: ["1", "2"]
    validation:
      failure_window_veto:
        top_n: 1
        require_passing_candidate: true
        output_root: failure-veto-output
        summary_output: failure-veto-summary.json
        windows:
          - name: failure-2024
            start: 2024-01-01
            end: 2025-01-01
        constraints:
          - metric: pnl_usd
            operator: ">"
            threshold: "0"
        report_only_windows:
          - name: report-2025-2026
            start: 2025-01-01
            end: 2026-04-10
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
            "capital_metric_config": None,
            "candidate_parameters": ({"entry_bar": 1, "quantity": "2"},),
            "constraint_count": 1,
            "objective_metric": "sharpe_ratio",
            "output_root": tmp_path / "failure-veto-output",
            "report_only_windows": (
                {
                    "end": "2026-04-10",
                    "name": "report-2025-2026",
                    "report_only": True,
                    "start": "2025-01-01",
                },
            ),
            "windows": (
                {
                    "end": "2025-01-01",
                    "name": "failure-2024",
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
    assert outputs["failure_window_veto_output"] == str(tmp_path / "failure-veto-summary.json")
    assert (tmp_path / "failure-veto-summary.json").exists()


def test_failure_window_veto_blocks_workflow_when_required_candidate_is_missing(
    tmp_path: Path,
) -> None:
    workflow_path = _write_workflow(
        tmp_path,
        """
version: 1
workflow_id: blocked-failure-window-veto
steps:
  - id: optimize
    kind: optimize
    objective_metric: sharpe_ratio
    parameters:
      alpha: ["1"]
    validation:
      failure_window_veto:
        top_n: 1
        require_passing_candidate: true
        windows:
          - name: failure-2024
            start: 2024-01-01
            end: 2025-01-01
        constraints:
          - metric: pnl_usd
            operator: ">"
            threshold: "0"
  - id: report
    kind: research_report
    output_path: should-not-run.md
""",
    )
    session = _FakeSession(accepted_specs=())
    session.failure_veto_accepted = False

    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(workflow_path),
    )

    assert result.status == "blocked"
    assert [step.step_id for step in result.steps] == ["optimize"]
    assert result.steps[0].status == "blocked"
    assert result.steps[0].message == "failure-window veto blocked workflow"
```

Extend `_FakeSession`:

```python
        self.failure_veto_calls: list[dict[str, object]] = []
        self.failure_veto_accepted = True
```

Add method:

```python
    def validate_optimizer_failure_window_veto(
        self,
        *,
        candidate_parameters: tuple[dict[str, object], ...],
        windows: tuple[object, ...],
        report_only_windows: tuple[object, ...] = (),
        constraints: tuple[object, ...] = (),
        capital_metric_config: dict[str, object] | None = None,
        objective_metric: str | None = None,
        output_root: Path | None = None,
    ) -> object:
        self.failure_veto_calls.append(
            {
                "candidate_parameters": candidate_parameters,
                "capital_metric_config": capital_metric_config,
                "constraint_count": len(constraints),
                "objective_metric": objective_metric,
                "output_root": output_root,
                "report_only_windows": tuple(window.to_metadata() for window in report_only_windows),
                "windows": tuple(window.to_metadata() for window in windows),
            }
        )
        payload = {
            "accepted_candidates": (() if not self.failure_veto_accepted else ({"candidate_id": "candidate-0000"},)),
            "candidate_count": 1,
            "decision": {
                "accepted": self.failure_veto_accepted,
                "reasons": (() if self.failure_veto_accepted else ("no selected candidate survived failure-window veto",)),
            },
            "rejected_candidates": (() if self.failure_veto_accepted else ({"candidate_id": "candidate-0000"},)),
            "report_only_windows": (),
            "veto_windows": (),
        }
        return SimpleNamespace(to_payload=lambda: payload)
```

- [ ] **Step 2: Run workflow tests to verify they fail**

Run:

```bash
uv run pytest tests/unit/research/test_research_workflow.py::test_runner_runs_failure_window_veto_for_top_optimizer_candidates tests/unit/research/test_research_workflow.py::test_failure_window_veto_blocks_workflow_when_required_candidate_is_missing -q
```

Expected: fail because workflow parsing and `_FakeSession` support do not exist.

- [ ] **Step 3: Implement workflow parsing and execution**

Modify imports in `backend/src/qts/research/workflow.py`:

```python
    FailureWindow,
```

In `_optimize(...)`, after walk-forward handling and before building `ranked_results`, add:

```python
        failure_veto_payload = self._failure_window_veto_payload(step.payload.get("validation"))
        failure_veto_summary_payload: dict[str, Any] | None = None
        failure_veto_output_path: Path | None = None
        failure_veto_required = False
        if failure_veto_payload is not None:
            veto_top_n = int(failure_veto_payload.get("top_n", 1))
            if veto_top_n <= 0:
                raise ValueError("validation.failure_window_veto.top_n must be positive")
            failure_veto_required = bool(
                failure_veto_payload.get("require_passing_candidate", False)
            )
            failure_veto_output_root = failure_veto_payload.get("output_root")
            failure_veto_summary = session.validate_optimizer_failure_window_veto(
                candidate_parameters=tuple(
                    dict(result.parameters) for result in results[:veto_top_n]
                ),
                windows=self._failure_windows(
                    failure_veto_payload,
                    field_name="windows",
                    report_only=False,
                ),
                report_only_windows=self._failure_windows(
                    failure_veto_payload,
                    field_name="report_only_windows",
                    report_only=True,
                ),
                constraints=self._failure_veto_constraints(failure_veto_payload),
                capital_metric_config=capital_metric_config,
                objective_metric=(None if objective_metric is None else str(objective_metric)),
                output_root=(
                    None
                    if failure_veto_output_root is None
                    else config.resolve_path(str(failure_veto_output_root))
                ),
            )
            failure_veto_summary_payload = failure_veto_summary.to_payload()
            raw_failure_veto_output = failure_veto_payload.get("summary_output")
            if raw_failure_veto_output is not None:
                failure_veto_output_path = config.resolve_path(str(raw_failure_veto_output))
                failure_veto_output_path.parent.mkdir(parents=True, exist_ok=True)
                failure_veto_output_path.write_text(
                    json.dumps(
                        _json_ready(failure_veto_summary_payload),
                        sort_keys=True,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
```

Add output handling before the return:

```python
        if failure_veto_summary_payload is not None:
            outputs["failure_window_veto"] = failure_veto_summary_payload
            outputs["failure_window_veto_output"] = (
                None if failure_veto_output_path is None else str(failure_veto_output_path)
            )
```

Replace the final `ResearchWorkflowStepResult(...)` status/message block with:

```python
        veto_decision = (
            {}
            if failure_veto_summary_payload is None
            else failure_veto_summary_payload.get("decision", {})
        )
        veto_blocked = (
            failure_veto_required
            and isinstance(veto_decision, Mapping)
            and veto_decision.get("accepted") is False
        )
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="blocked" if veto_blocked else "passed",
            message=(
                "failure-window veto blocked workflow"
                if veto_blocked
                else "optimization completed"
            ),
            outputs=outputs,
        )
```

Add helper methods near `_walk_forward_payload(...)`:

```python
    def _failure_window_veto_payload(self, value: Any) -> dict[str, Any] | None:
        validation = self._optional_mapping(value)
        if validation is None:
            return None
        raw_veto = validation.get("failure_window_veto")
        if raw_veto is None:
            return None
        if not isinstance(raw_veto, Mapping):
            raise ValueError("validation.failure_window_veto must be a mapping")
        return dict(raw_veto)

    def _failure_veto_constraints(self, value: Mapping[str, Any]) -> tuple[MetricConstraint, ...]:
        raw_constraints = value.get("constraints")
        if raw_constraints is None:
            return ()
        return self._metric_constraints_from_sequence(
            raw_constraints,
            field_name="validation.failure_window_veto.constraints",
        )

    def _failure_windows(
        self,
        value: Mapping[str, Any],
        *,
        field_name: str,
        report_only: bool,
    ) -> tuple[FailureWindow, ...]:
        raw_windows = value.get(field_name, ())
        if field_name == "windows" and (not isinstance(raw_windows, list) or not raw_windows):
            raise ValueError("validation.failure_window_veto.windows must be a non-empty list")
        if not isinstance(raw_windows, list):
            raise ValueError(f"validation.failure_window_veto.{field_name} must be a list")
        windows: list[FailureWindow] = []
        for index, raw_window in enumerate(raw_windows):
            if not isinstance(raw_window, Mapping):
                raise ValueError(
                    f"validation.failure_window_veto.{field_name}[{index}] must be a mapping"
                )
            window = dict(raw_window)
            windows.append(
                FailureWindow(
                    name=str(window["name"]),
                    start=self._iso_date(window["start"], "start"),
                    end=self._iso_date(window["end"], "end"),
                    report_only=report_only,
                )
            )
        return tuple(windows)
```

Refactor `_validation_constraints(...)` to delegate to a shared parser:

```python
    def _validation_constraints(self, value: Any) -> tuple[MetricConstraint, ...]:
        validation = self._optional_mapping(value)
        if validation is None:
            return ()
        raw_constraints = validation.get("constraints")
        if raw_constraints is None:
            return ()
        return self._metric_constraints_from_sequence(
            raw_constraints,
            field_name="validation.constraints",
        )

    def _metric_constraints_from_sequence(
        self,
        raw_constraints: Any,
        *,
        field_name: str,
    ) -> tuple[MetricConstraint, ...]:
        if not isinstance(raw_constraints, list):
            raise ValueError(f"{field_name} must be a list")
        constraints: list[MetricConstraint] = []
        for index, raw_constraint in enumerate(raw_constraints):
            if not isinstance(raw_constraint, Mapping):
                raise ValueError(f"{field_name}[{index}] must be a mapping")
            constraint = dict(raw_constraint)
            constraints.append(
                MetricConstraint(
                    metric_name=str(constraint["metric"]),
                    operator=str(constraint["operator"]),
                    threshold=Decimal(str(constraint["threshold"])),
                )
            )
        return tuple(constraints)
```

- [ ] **Step 4: Run workflow tests**

Run:

```bash
uv run pytest tests/unit/research/test_research_workflow.py::test_runner_runs_failure_window_veto_for_top_optimizer_candidates tests/unit/research/test_research_workflow.py::test_failure_window_veto_blocks_workflow_when_required_candidate_is_missing tests/unit/research/test_research_workflow.py::test_runner_runs_walk_forward_validation_for_top_optimizer_candidates -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit Task 3**

```bash
git add backend/src/qts/research/workflow.py tests/unit/research/test_research_workflow.py
git commit -m "feat: wire failure-window veto into research workflows"
```

## Task 4: VWAP Long-Sample Workflow Gates

**Files:**
- Modify: `configs/research/workflows/vwap_factor_gc_long_search.yaml`
- Modify: `configs/research/workflows/vwap_factor_si_long_search.yaml`
- Modify: `configs/research/workflows/vwap_factor_gc_5m_long_search.yaml`
- Modify: `configs/research/workflows/vwap_factor_si_5m_long_search.yaml`
- Modify: `configs/research/workflows/vwap_factor_gc_15m_long_search.yaml`
- Modify: `configs/research/workflows/vwap_factor_si_15m_long_search.yaml`
- Modify: `tests/unit/research/test_research_workflow.py`

- [ ] **Step 1: Write failing config coverage test**

Add this parametrized test near `test_vwap_long_research_configs_are_symbol_isolated_and_hold_out_oos`.

```python
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
def test_vwap_long_research_workflows_include_2022_2024_failure_veto(
    workflow_path: Path,
) -> None:
    workflow_config = ResearchWorkflowConfig.from_yaml(workflow_path)
    optimize_steps = [step for step in workflow_config.steps if step.kind == "optimize"]

    assert optimize_steps
    for step in optimize_steps:
        veto = step.payload["validation"]["failure_window_veto"]
        assert veto["top_n"] == 3
        assert veto["require_passing_candidate"] is True
        assert [
            {
                "name": str(window["name"]),
                "start": window["start"].isoformat(),
                "end": window["end"].isoformat(),
            }
            for window in veto["windows"]
        ] == [
            {"name": "failure-2022", "start": "2022-01-01", "end": "2023-01-01"},
            {"name": "failure-2023", "start": "2023-01-01", "end": "2024-01-01"},
            {"name": "failure-2024", "start": "2024-01-01", "end": "2025-01-01"},
        ]
        assert [
            {
                "name": str(window["name"]),
                "start": window["start"].isoformat(),
                "end": window["end"].isoformat(),
            }
            for window in veto["report_only_windows"]
        ] == [
            {"name": "report-2025-2026", "start": "2025-01-01", "end": "2026-04-10"}
        ]
        assert veto["constraints"] == [
            {"metric": "pnl_usd", "operator": ">", "threshold": "0"},
            {"metric": "max_drawdown", "operator": "<=", "threshold": "0.05"},
        ]
```

- [ ] **Step 2: Run config coverage test to verify it fails**

Run:

```bash
uv run pytest tests/unit/research/test_research_workflow.py::test_vwap_long_research_workflows_include_2022_2024_failure_veto -q
```

Expected: fail because long-sample workflows do not yet include `failure_window_veto`.

- [ ] **Step 3: Add failure-window veto blocks to each long-sample workflow**

In each listed workflow, under the existing optimize step `validation:` block and alongside existing `constraints` / `walk_forward`, add a workflow-specific `output_root` and `summary_output`.

Use this shape, replacing the path fragment for each workflow:

```yaml
      failure_window_veto:
        top_n: 3
        require_passing_candidate: true
        output_root: ../../../runs/research/vwap/gc-long/failure-veto/primary
        summary_output: ../../../runs/research/vwap/gc-long/validation/failure-veto.json
        windows:
          - name: failure-2022
            start: 2022-01-01
            end: 2023-01-01
          - name: failure-2023
            start: 2023-01-01
            end: 2024-01-01
          - name: failure-2024
            start: 2024-01-01
            end: 2025-01-01
        constraints:
          - metric: pnl_usd
            operator: ">"
            threshold: "0"
          - metric: max_drawdown
            operator: "<="
            threshold: "0.05"
        report_only_windows:
          - name: report-2025-2026
            start: 2025-01-01
            end: 2026-04-10
```

Use these path fragments:

```text
gc-long
si-long
gc-5m-long
si-5m-long
gc-15m-long
si-15m-long
```

- [ ] **Step 4: Run config and workflow tests**

Run:

```bash
uv run pytest tests/unit/research/test_research_workflow.py::test_vwap_long_research_workflows_include_2022_2024_failure_veto tests/unit/research/test_research_workflow.py::test_vwap_long_research_configs_are_symbol_isolated_and_hold_out_oos -q
```

Expected: selected tests pass.

- [ ] **Step 5: Commit Task 4**

```bash
git add configs/research/workflows/vwap_factor_gc_long_search.yaml configs/research/workflows/vwap_factor_si_long_search.yaml configs/research/workflows/vwap_factor_gc_5m_long_search.yaml configs/research/workflows/vwap_factor_si_5m_long_search.yaml configs/research/workflows/vwap_factor_gc_15m_long_search.yaml configs/research/workflows/vwap_factor_si_15m_long_search.yaml tests/unit/research/test_research_workflow.py
git commit -m "config: add vwap failure-window veto gates"
```

## Task 5: Verification and Review

**Files:**
- Inspect changed Python files.
- Update code graph after successful modifications.

- [ ] **Step 1: Run private-helper inspection**

Run:

```bash
rg -n "^def _|^class _" backend/src/qts/research/optimizer/failure_veto.py backend/src/qts/research/session.py backend/src/qts/research/workflow.py
```

Expected: helpers in `failure_veto.py` are shared deterministic JSON/date helpers; existing helpers in `session.py` / `workflow.py` remain module-owned parsing/orchestration helpers. If any helper serves only one new class, move it onto that class before proceeding.

- [ ] **Step 2: Run focused research tests**

Run:

```bash
uv run pytest tests/unit/research/test_optimizer_failure_veto.py tests/unit/research/test_optimizer_walk_forward.py tests/unit/research/test_optimizer_constraints.py tests/unit/research/test_research_session.py tests/unit/research/test_research_workflow.py -q
```

Expected: all selected research unit tests pass.

- [ ] **Step 3: Run required normal task gates**

Run:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

Expected: all commands pass. If any command fails due to pre-existing unrelated dirty-worktree edits, capture the exact failing command, affected files, and evidence that the failure is unrelated before asking for review.

- [ ] **Step 4: Refresh graph and run impact review**

Run graph update:

```text
build_or_update_graph_tool(repo_root="/Users/bjhl/Projects/QTS", full_rebuild=false)
```

Then run:

```text
detect_changes_tool(repo_root="/Users/bjhl/Projects/QTS", base="HEAD~1", detail_level="minimal")
```

Expected: review output shows changes contained to research optimizer/session/workflow/config/test/doc boundaries, with no runtime/risk/order/execution/account blast-radius concerns.

- [ ] **Step 5: Final diff check**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors. Status may include pre-existing user changes, but the implementation commits must contain only planned files.
