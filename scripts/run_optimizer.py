"""Run a parameter-sweep optimizer from a YAML config.

Loads a strategy module dynamically, builds a ``ParameterGrid`` from the
config, drives every combination through ``OptimizationRunner`` (which
routes through ``BacktestEngine``), and prints a human-readable ranked
table to stdout.

Usage:
    uv run python scripts/run_optimizer.py configs/optimizer/quickstart.yaml

The CLI is the production caller that closes the OPT-65 wiring gap for
``qts.research.optimizer.*``; without it the optimizer was library-only.
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
    OptimizationJob,
    OptimizationResult,
    OptimizationRunner,
    ParameterGrid,
    ParameterSpace,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"optimizer config not found: {config_path}")
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"optimizer config must be a YAML mapping, got {type(payload).__name__}")
    for required in ("strategy_module", "strategy_factory", "bars_factory", "parameters"):
        if required not in payload:
            raise KeyError(f"optimizer config missing required key: {required!r}")
    return payload


def _resolve_factory(module_path: str, attribute: str) -> Any:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    module = importlib.import_module(module_path)
    try:
        return getattr(module, attribute)
    except AttributeError as exc:
        raise AttributeError(f"module {module_path!r} has no attribute {attribute!r}") from exc


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
    strategy_factory = _resolve_factory(config["strategy_module"], config["strategy_factory"])
    bars_factory = _resolve_factory(config["strategy_module"], config["bars_factory"])
    objective_metric = str(config.get("objective_metric", "sharpe_ratio"))

    raw_parameters = list(config["parameters"])
    if not raw_parameters:
        raise ValueError("optimizer config 'parameters' must list at least one entry")
    grid = ParameterGrid(
        *(ParameterSpace(name=str(p["name"]), values=tuple(p["values"])) for p in raw_parameters)
    )

    job = OptimizationJob(
        strategy_factory=strategy_factory,
        bars_factory=bars_factory,
        initial_cash=Decimal(str(config.get("initial_cash", "100000"))),
        parameter_grid=grid,
        output_root=args.output_root,
        objective_metric=objective_metric,
    )

    runner = OptimizationRunner()
    results = runner.run(job)
    print(_format_ranked_table(results, objective_metric))
    return 0


if __name__ == "__main__":
    sys.exit(main())
