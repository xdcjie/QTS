"""Optimization result payload."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    """One run's outcome inside a sweep."""

    parameters: dict[str, Any]
    manifest_path: Path
    manifest_hash: str
    objective_value: Decimal
    processed_bars: int | None = None
    trading_bars: int | None = None
    elapsed_seconds: Decimal | None = None
    bars_per_second: Decimal | None = None
    equity_curve_sample_interval: int | None = None


__all__ = ["OptimizationResult"]
