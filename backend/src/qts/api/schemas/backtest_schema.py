"""Backtest API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BacktestRequestSchema(BaseModel):
    """HTTP request for submitting a backtest."""

    config_path: str = Field(min_length=1)


class BacktestRunSchema(BaseModel):
    """HTTP response for a submitted backtest."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    config_path: str
    status: str


class BacktestStrategyOptionSchema(BaseModel):
    """HTTP response for a runnable backtest strategy option."""

    model_config = ConfigDict(from_attributes=True)

    label: str
    config_path: str


__all__ = [
    "BacktestRequestSchema",
    "BacktestRunSchema",
    "BacktestStrategyOptionSchema",
]
