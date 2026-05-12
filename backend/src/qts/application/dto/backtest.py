"""Backtest application DTOs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BacktestRequestDTO:
    """Stable application request for starting a backtest."""

    strategy_name: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.strategy_name.strip():
            raise ValueError("strategy_name must not be empty")


@dataclass(frozen=True, slots=True)
class BacktestRunDTO:
    """Stable application response for a submitted backtest."""

    run_id: str
    strategy_name: str
    status: str


__all__ = ["BacktestRequestDTO", "BacktestRunDTO"]
