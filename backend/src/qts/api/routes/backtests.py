"""Backtest API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from qts.api.mappers import (
    map_backtest_request_schema,
    map_backtest_run_dto,
    map_backtest_run_result_dto,
    map_backtest_strategy_option_dto,
)
from qts.api.schemas import (
    BacktestRequestSchema,
    BacktestRunResultSchema,
    BacktestRunSchema,
    BacktestStrategyOptionSchema,
)
from qts.application.dto import BacktestRequestDTO
from qts.application.services import BacktestService, BacktestStrategyCatalog

router = APIRouter()


@router.post("/backtests", response_model=BacktestRunResultSchema)
def submit_backtest(request: BacktestRequestSchema) -> BacktestRunResultSchema:
    """Submit a backtest request through the backtest application service."""
    request_dto: BacktestRequestDTO = map_backtest_request_schema(request)
    result = BacktestService().submit(request_dto)
    return map_backtest_run_result_dto(result)


@router.get("/backtests", response_model=tuple[BacktestRunSchema, ...])
def list_backtests(
    limit: int | None = Query(default=None, ge=1),
) -> tuple[BacktestRunSchema, ...]:
    """List recent backtest runs from persisted summaries."""
    runs = BacktestService().list_runs(limit=limit)
    return tuple(map_backtest_run_dto(run) for run in runs)


@router.get(
    "/backtests/strategy-options",
    response_model=tuple[BacktestStrategyOptionSchema, ...],
)
def list_backtest_strategy_options() -> tuple[BacktestStrategyOptionSchema, ...]:
    """List runnable backtest strategy options from configured backtest files."""
    options = BacktestStrategyCatalog().list_options()
    return tuple(map_backtest_strategy_option_dto(option) for option in options)


__all__ = ["router"]
