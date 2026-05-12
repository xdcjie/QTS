"""Strategy API routes."""

from __future__ import annotations

from fastapi import APIRouter

from qts.api.schemas.common import StrategyStatusSchema

router = APIRouter(prefix="/strategies")


@router.get("", response_model=list[StrategyStatusSchema])
def list_strategies() -> list[StrategyStatusSchema]:
    """Perform list_strategies."""
    return [StrategyStatusSchema(strategy_id="strategy-001", status="stopped")]


@router.post("/{strategy_id}/start", response_model=StrategyStatusSchema)
def start_strategy(strategy_id: str) -> StrategyStatusSchema:
    """Perform start_strategy."""
    return StrategyStatusSchema(strategy_id=strategy_id, status="running")


@router.post("/{strategy_id}/stop", response_model=StrategyStatusSchema)
def stop_strategy(strategy_id: str) -> StrategyStatusSchema:
    """Perform stop_strategy."""
    return StrategyStatusSchema(strategy_id=strategy_id, status="stopped")


__all__ = ["router"]
