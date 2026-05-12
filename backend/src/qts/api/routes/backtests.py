"""Backtest API routes."""

from __future__ import annotations

from fastapi import APIRouter

from qts.api.mappers import (
    map_backtest_request_schema,
    map_backtest_run_dto,
)
from qts.api.schemas import BacktestRequestSchema, BacktestRunSchema
from qts.application.dto import BacktestRequestDTO
from qts.application.services import BacktestService

router = APIRouter()


@router.post("/backtests", response_model=BacktestRunSchema)
def submit_backtest(request: BacktestRequestSchema) -> BacktestRunSchema:
    """Submit a backtest request through the backtest application service."""
    request_dto: BacktestRequestDTO = map_backtest_request_schema(request)
    result = BacktestService().submit(request_dto)
    return map_backtest_run_dto(result)


__all__ = ["router"]
