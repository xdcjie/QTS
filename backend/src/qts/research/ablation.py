"""Strategy research ablation evidence and deterministic artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class AblationRun:
    """Completed metrics for one baseline, module, or combined ablation run."""

    name: str
    modules: tuple[str, ...]
    metrics: Mapping[str, float]
    split_metrics: Mapping[str, Mapping[str, float]] | None = None
    trade_count: int | None = None
    cost_stress_metrics: Mapping[str, Mapping[str, float]] | None = None

    def __init__(
        self,
        *,
        name: str,
        modules: Sequence[str],
        metrics: Mapping[str, float],
        split_metrics: Mapping[str, Mapping[str, float]] | None = None,
        trade_count: int | None = None,
        cost_stress_metrics: Mapping[str, Mapping[str, float]] | None = None,
    ) -> None:
        if not name:
            raise ValueError("ablation run name is required")
        if not metrics:
            raise ValueError("ablation run metrics are required")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "modules", tuple(modules))
        object.__setattr__(self, "metrics", dict(metrics))
        object.__setattr__(
            self,
            "split_metrics",
            {split: dict(values) for split, values in (split_metrics or {}).items()},
        )
        object.__setattr__(self, "trade_count", trade_count)
        object.__setattr__(
            self,
            "cost_stress_metrics",
            {scenario: dict(values) for scenario, values in (cost_stress_metrics or {}).items()},
        )


@dataclass(frozen=True, slots=True)
class AblationPlan:
    """Validated baseline-first ablation protocol for strategy research evidence."""

    baseline: str
    modules: tuple[str, ...]
    runs: tuple[AblationRun, ...]

    def __init__(
        self,
        *,
        baseline: str,
        modules: Sequence[str],
        runs: Sequence[AblationRun],
    ) -> None:
        module_tuple = tuple(modules)
        run_tuple = tuple(runs)
        self._validate(baseline, module_tuple, run_tuple)
        object.__setattr__(self, "baseline", baseline)
        object.__setattr__(self, "modules", module_tuple)
        object.__setattr__(self, "runs", run_tuple)

    @staticmethod
    def _validate(baseline: str, modules: tuple[str, ...], runs: tuple[AblationRun, ...]) -> None:
        if not baseline:
            raise ValueError("baseline run name is required")
        if len(set(modules)) != len(modules):
            raise ValueError("ablation modules must be unique")
        if not runs or all(run.name != baseline for run in runs):
            raise ValueError("ablation plan requires a baseline run")
        if runs[0].name != baseline:
            raise ValueError("baseline run must be first in ablation order")
        if runs[0].modules:
            raise ValueError("baseline run must not enable ablation modules")
        known_modules = set(modules)
        seen_single_modules: set[str] = set()
        for run in runs[1:]:
            unknown = set(run.modules) - known_modules
            if unknown:
                raise ValueError(f"ablation run uses unknown modules: {sorted(unknown)}")
            if len(run.modules) == 1:
                seen_single_modules.add(run.modules[0])
            if len(run.modules) > 1 and not set(run.modules).issubset(seen_single_modules):
                raise ValueError("combined ablation runs must appear after their module runs")
        missing_single_modules = known_modules - seen_single_modules
        if missing_single_modules:
            raise ValueError(
                f"missing single-module ablation runs: {sorted(missing_single_modules)}"
            )


@dataclass(frozen=True, slots=True)
class AblationVariantSummary:
    """Delta summary for one ablation variant compared with the baseline."""

    name: str
    modules: tuple[str, ...]
    metrics: Mapping[str, float]
    metric_deltas: Mapping[str, float]
    is_delta: float | None
    oos_delta: float | None
    trade_count: int | None
    trade_count_delta: int | None
    cost_stress_deltas: Mapping[str, Mapping[str, float]]
    unstable: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable summary."""

        return {
            "name": self.name,
            "modules": list(self.modules),
            "metrics": dict(sorted(self.metrics.items())),
            "metric_deltas": dict(sorted(self.metric_deltas.items())),
            "is_delta": self.is_delta,
            "oos_delta": self.oos_delta,
            "trade_count": self.trade_count,
            "trade_count_delta": self.trade_count_delta,
            "cost_stress_deltas": {
                scenario: dict(sorted(values.items()))
                for scenario, values in sorted(self.cost_stress_deltas.items())
            },
            "unstable": self.unstable,
        }


@dataclass(frozen=True, slots=True)
class AblationReport:
    """Baseline-relative ablation report for completed research artifacts."""

    baseline: str
    primary_metric: str
    variants: tuple[AblationVariantSummary, ...]

    @classmethod
    def from_plan(
        cls,
        plan: AblationPlan,
        *,
        primary_metric: str,
        higher_is_better: bool = True,
    ) -> AblationReport:
        """Build baseline-relative deltas for each run in the plan."""

        baseline_run = plan.runs[0]
        variants = tuple(
            cls._summarize_run(
                run,
                baseline_run=baseline_run,
                primary_metric=primary_metric,
                higher_is_better=higher_is_better,
            )
            for run in plan.runs
        )
        return cls(
            baseline=plan.baseline,
            primary_metric=primary_metric,
            variants=variants,
        )

    @staticmethod
    def _summarize_run(
        run: AblationRun,
        *,
        baseline_run: AblationRun,
        primary_metric: str,
        higher_is_better: bool,
    ) -> AblationVariantSummary:
        metric_deltas = {
            metric: _round_delta(value - baseline_run.metrics[metric])
            for metric, value in run.metrics.items()
            if metric in baseline_run.metrics
        }
        is_delta = _split_delta(run, baseline_run, "IS", primary_metric)
        oos_delta = _split_delta(run, baseline_run, "OOS", primary_metric)
        trade_count_delta = (
            None
            if run.trade_count is None or baseline_run.trade_count is None
            else run.trade_count - baseline_run.trade_count
        )
        cost_stress_deltas = _cost_stress_deltas(run, baseline_run)
        unstable = _is_unstable(
            is_delta=is_delta,
            oos_delta=oos_delta,
            higher_is_better=higher_is_better,
        )
        return AblationVariantSummary(
            name=run.name,
            modules=run.modules,
            metrics=run.metrics,
            metric_deltas=metric_deltas,
            is_delta=is_delta,
            oos_delta=oos_delta,
            trade_count=run.trade_count,
            trade_count_delta=trade_count_delta,
            cost_stress_deltas=cost_stress_deltas,
            unstable=unstable,
        )

    def variant(self, name: str) -> AblationVariantSummary:
        """Return the summary for a named ablation variant."""

        for variant in self.variants:
            if variant.name == name:
                return variant
        raise KeyError(name)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable report payload."""

        return {
            "baseline": self.baseline,
            "primary_metric": self.primary_metric,
            "variants": [variant.to_dict() for variant in self.variants],
            "promotion_boundary": (
                "Ablation evidence is completed-artifact research evidence only "
                "and does not auto-promote paper/live runtime configuration."
            ),
        }

    def to_markdown(self) -> str:
        """Render a deterministic markdown ablation report."""

        lines = [
            "# Strategy Ablation Report",
            "",
            f"baseline: {self.baseline}",
            f"primary_metric: {self.primary_metric}",
            "",
            "## Variants",
            (
                "| Variant | Modules | "
                f"{self.primary_metric}_delta | IS delta | OOS delta | "
                "Trade count delta | Unstable |"
            ),
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for variant in self.variants:
            primary_delta = variant.metric_deltas.get(self.primary_metric, 0.0)
            trade_count_delta = (
                variant.trade_count_delta if variant.trade_count_delta is not None else "<none>"
            )
            lines.append(
                "| "
                f"{variant.name} | "
                f"{', '.join(variant.modules) or '<baseline>'} | "
                f"{self.primary_metric}_delta: {_format_number(primary_delta)} | "
                f"{_format_optional_number(variant.is_delta)} | "
                f"{_format_optional_number(variant.oos_delta)} | "
                f"{trade_count_delta} | "
                f"{variant.unstable} |"
            )
        lines.extend(
            [
                "",
                "## Non-Promotion Boundary",
                (
                    "This ablation report is research evidence only. It does not "
                    "promote strategy code into paper/live execution."
                ),
            ]
        )
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class AblationReportPaths:
    """Paths written by the ablation artifact writer."""

    json_path: Path
    markdown_path: Path


class AblationReportWriter:
    """Owns deterministic JSON and markdown ablation artifact serialization."""

    def __init__(self, output_root: Path) -> None:
        self._output_root = output_root

    def write(
        self,
        report: AblationReport,
        *,
        json_path: str | Path = "ablation-report.json",
        markdown_path: str | Path = "ablation-report.md",
    ) -> AblationReportPaths:
        """Write JSON and markdown artifacts under the configured output root."""

        json_target = self._resolve_output_path(json_path)
        markdown_target = self._resolve_output_path(markdown_path)
        json_target.parent.mkdir(parents=True, exist_ok=True)
        markdown_target.parent.mkdir(parents=True, exist_ok=True)
        json_target.write_text(
            json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        markdown_target.write_text(report.to_markdown() + "\n", encoding="utf-8")
        return AblationReportPaths(json_path=json_target, markdown_path=markdown_target)

    def _resolve_output_path(self, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        if output_path.is_absolute():
            raise ValueError("output_path must be relative to ablation output root")
        if any(part == ".." for part in output_path.parts):
            raise ValueError("output_path must not use parent traversal")
        if output_path.as_posix() in {"", "."}:
            raise ValueError("output_path must include a filename")
        target = (self._output_root / output_path).resolve()
        root = self._output_root.resolve()
        if not target.is_relative_to(root):
            raise ValueError("output_path must remain inside ablation output root")
        return target


def _split_delta(
    run: AblationRun,
    baseline_run: AblationRun,
    split: str,
    metric: str,
) -> float | None:
    run_splits = run.split_metrics or {}
    baseline_splits = baseline_run.split_metrics or {}
    if split not in run_splits or split not in baseline_splits:
        return None
    if metric not in run_splits[split] or metric not in baseline_splits[split]:
        return None
    return _round_delta(run_splits[split][metric] - baseline_splits[split][metric])


def _cost_stress_deltas(
    run: AblationRun,
    baseline_run: AblationRun,
) -> dict[str, dict[str, float]]:
    deltas: dict[str, dict[str, float]] = {}
    for scenario, metrics in (run.cost_stress_metrics or {}).items():
        baseline_metrics = (baseline_run.cost_stress_metrics or {}).get(
            scenario,
            baseline_run.metrics,
        )
        scenario_deltas = {
            metric: _round_delta(value - baseline_metrics[metric])
            for metric, value in metrics.items()
            if metric in baseline_metrics
        }
        deltas[scenario] = scenario_deltas
    return deltas


def _is_unstable(
    *,
    is_delta: float | None,
    oos_delta: float | None,
    higher_is_better: bool,
) -> bool:
    if is_delta is None or oos_delta is None:
        return False
    if higher_is_better:
        return is_delta > 0 and oos_delta <= 0
    return is_delta < 0 and oos_delta >= 0


def _format_optional_number(value: float | None) -> str:
    if value is None:
        return "<none>"
    return _format_number(value)


def _format_number(value: float) -> str:
    return f"{value:.12g}"


def _round_delta(value: float) -> float:
    return round(value, 12)
