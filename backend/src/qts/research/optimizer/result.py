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


__all__ = ["OptimizationResult"]
