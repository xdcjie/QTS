"""Run a parameter-sweep optimizer from a YAML config.

Two YAML shapes are supported:

1. **Factory-driven** (the original OPT-65 shape) — supply
   ``strategy_module``, ``strategy_factory``, ``bars_factory`` plus a
   ``parameters`` grid. The CLI dynamically loads the factories and
   drives ``OptimizationRunner`` over the cartesian product.

2. **Pipeline-driven** (OPT-67) — supply ``backtest_config`` pointing
   at the same ``configs/backtest.yaml`` shape ``scripts/run_backtest.py``
   reads. The CLI loads the base config once, then per combination
   replaces ``strategy_params`` and drives the same
   ``HistoricalCatalog -> ReplayMarketDataSource -> BacktestEngine.from_config``
   pipeline as a single-run backtest.

Either way the CLI prints a ranked-results table to stdout. Result
ranking is identical: descending by ``objective_metric``.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from qts.research.optimizer import (
    BacktestPipelineJob,
    BacktestPipelineRunner,
    OptimizationJob,
    OptimizationResult,
    OptimizationRunner,
    ParameterGrid,
    ParameterSpace,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

_FACTORY_KEYS = ("strategy_module", "strategy_factory", "bars_factory", "parameters")
_PIPELINE_KEYS = ("backtest_config", "parameters")


def _load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"optimizer config not found: {config_path}")
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"optimizer config must be a YAML mapping, got {type(payload).__name__}")
    if "backtest_config" in payload:
        missing = [key for key in _PIPELINE_KEYS if key not in payload]
        if missing:
            raise KeyError(f"pipeline optimizer config missing keys: {missing}")
    else:
        missing = [key for key in _FACTORY_KEYS if key not in payload]
        if missing:
            raise KeyError(f"factory optimizer config missing keys: {missing}")
    return payload


def _resolve_factory(module_path: str, attribute: str) -> Any:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    module = importlib.import_module(module_path)
    try:
        return getattr(module, attribute)
    except AttributeError as exc:
        raise AttributeError(f"module {module_path!r} has no attribute {attribute!r}") from exc


def _build_grid(raw_parameters: list[dict[str, Any]]) -> ParameterGrid:
    if not raw_parameters:
        raise ValueError("optimizer config 'parameters' must list at least one entry")
    return ParameterGrid(
        *(ParameterSpace(name=str(p["name"]), values=tuple(p["values"])) for p in raw_parameters)
    )


def _format_ranked_table(results: Sequence[OptimizationResult], objective_metric: str) -> str:
    parameter_names = sorted({key for result in results for key in result.parameters})
    header = ["rank", *parameter_names, objective_metric, "manifest_hash"]
    rows: list[list[str]] = [header]
    for index, result in enumerate(results, start=1):
        row = [str(index)]
        for name in parameter_names:
            row.append(str(result.parameters.get(name, "")))
        row.append(str(result.objective_value))
        row.append(result.manifest_hash[:12])
        rows.append(row)
    widths = [max(len(row[col]) for row in rows) for col in range(len(header))]
    lines = []
    for row_index, row in enumerate(rows):
        formatted = "  ".join(value.ljust(widths[col]) for col, value in enumerate(row))
        lines.append(formatted)
        if row_index == 0:
            lines.append("  ".join("-" * widths[col] for col in range(len(header))))
    return "\n".join(lines)


def _run_factory_path(
    config: dict[str, Any], *, output_root: Path
) -> tuple[Sequence[OptimizationResult], str]:
    strategy_factory = _resolve_factory(config["strategy_module"], config["strategy_factory"])
    bars_factory = _resolve_factory(config["strategy_module"], config["bars_factory"])
    objective_metric = str(config.get("objective_metric", "sharpe_ratio"))
    job = OptimizationJob(
        strategy_factory=strategy_factory,
        bars_factory=bars_factory,
        initial_cash=Decimal(str(config.get("initial_cash", "100000"))),
        parameter_grid=_build_grid(list(config["parameters"])),
        output_root=output_root,
        objective_metric=objective_metric,
    )
    return OptimizationRunner().run(job), objective_metric


def _run_pipeline_path(
    config: dict[str, Any], *, output_root: Path, config_dir: Path
) -> tuple[Sequence[OptimizationResult], str]:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    base_path = Path(config["backtest_config"])
    if not base_path.is_absolute():
        candidate = (config_dir / base_path).resolve()
        if not candidate.exists():
            candidate = (_REPO_ROOT / base_path).resolve()
        base_path = candidate
    objective_metric = str(config.get("objective_metric", "sharpe_ratio"))
    job = BacktestPipelineJob(
        base_config_path=base_path,
        parameter_grid=_build_grid(list(config["parameters"])),
        output_root=output_root,
        objective_metric=objective_metric,
    )
    return BacktestPipelineRunner().run(job), objective_metric


def main(argv: Sequence[str] | None = None) -> int:
    """Perform main."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to optimizer YAML config")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("runs/optimizer"),
        help="Root directory for per-combination backtest manifests",
    )
    args = parser.parse_args(argv)

    config = _load_config(args.config)
    if "backtest_config" in config:
        results, objective_metric = _run_pipeline_path(
            config,
            output_root=args.output_root,
            config_dir=args.config.resolve().parent,
        )
    else:
        results, objective_metric = _run_factory_path(config, output_root=args.output_root)
    print(_format_ranked_table(results, objective_metric))
    return 0


if __name__ == "__main__":
    sys.exit(main())
