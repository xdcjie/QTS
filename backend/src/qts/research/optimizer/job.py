"""Optimization job specification."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.market_data import Bar
from qts.research.optimizer.parameter_space import ParameterGrid
from qts.strategy_sdk import Strategy

StrategyFactory = Callable[[dict[str, Any]], Strategy]
BarsFactory = Callable[[], Iterable[Bar]]


@dataclass(frozen=True, slots=True)
class OptimizationJob:
    """Inputs the optimizer needs to run one sweep.

    Each parameter combination produces a fresh strategy instance and a
    fresh bar iterable. The optimizer routes them through ``BacktestEngine``
    so simulation behaviour matches a normal backtest one-for-one.
    """

    strategy_factory: StrategyFactory
    bars_factory: BarsFactory
    initial_cash: Decimal
    parameter_grid: ParameterGrid
    output_root: Path
    objective_metric: str = "sharpe_ratio"

    def __post_init__(self) -> None:
        if self.initial_cash <= Decimal("0"):
            raise ValueError("initial_cash must be positive")
        if not self.objective_metric.strip():
            raise ValueError("objective_metric must not be empty")


__all__ = ["BarsFactory", "OptimizationJob", "StrategyFactory"]
