"""Backtest API routes."""

from __future__ import annotations

from fastapi import APIRouter

from qts.api.schemas import BacktestRequestSchema, BacktestRunSchema
from qts.application.dto import BacktestRequestDTO
from qts.application.services import BacktestService

router = APIRouter()


@router.post("/backtests", response_model=BacktestRunSchema)
def submit_backtest(request: BacktestRequestSchema) -> BacktestRunSchema:
    result = BacktestService().submit(BacktestRequestDTO(strategy_name=request.strategy_name))
    return BacktestRunSchema.model_validate(result)


__all__ = ["router"]
