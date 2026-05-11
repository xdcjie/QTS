"""Backtest metrics."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal


def compute_equity_metrics(equity_values: Sequence[Decimal]) -> dict[str, Decimal | int]:
    """Compute deterministic metrics from an equity curve."""

    if not equity_values:
        raise ValueError("equity curve must not be empty")
    first = equity_values[0]
    if first == Decimal("0"):
        raise ValueError("first equity value must not be zero")
    peak = first
    max_drawdown = Decimal("0")
    for value in equity_values:
        if value > peak:
            peak = value
        if peak != Decimal("0"):
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
    return {
        "points": len(equity_values),
        "total_return": (equity_values[-1] - first) / first,
        "max_drawdown": max_drawdown,
    }


__all__ = ["compute_equity_metrics"]
