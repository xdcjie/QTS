"""Backtest application service skeleton."""

from __future__ import annotations

from itertools import count

from qts.application.dto import BacktestRequestDTO, BacktestRunDTO


class BacktestService:
    """Application boundary for backtest use cases."""

    def __init__(self) -> None:
        self._ids = count(1)

    def submit(self, request: BacktestRequestDTO) -> BacktestRunDTO:
        return BacktestRunDTO(
            run_id=f"bt-{next(self._ids):06d}",
            strategy_name=request.strategy_name,
            status="accepted",
        )


__all__ = ["BacktestService"]
