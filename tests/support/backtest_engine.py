from __future__ import annotations

from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.backtest.run_plan import BacktestRunPlan


def backtest_engine_from_inputs(**inputs: Any) -> BacktestEngine:
    """Build a backtest engine from legacy test inputs via the final run plan API."""

    return BacktestEngine(BacktestRunPlan.from_inputs(**inputs))
