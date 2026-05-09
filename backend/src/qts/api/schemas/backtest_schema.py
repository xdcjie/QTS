"""Backtest API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BacktestRequestSchema(BaseModel):
    """HTTP request for submitting a backtest."""

    strategy_name: str = Field(min_length=1)


class BacktestRunSchema(BaseModel):
    """HTTP response for a submitted backtest."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    strategy_name: str
    status: str


__all__ = ["BacktestRequestSchema", "BacktestRunSchema"]
