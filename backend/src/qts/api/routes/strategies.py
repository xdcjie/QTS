"""Strategy API routes."""

from __future__ import annotations

from fastapi import APIRouter

from qts.api.mappers import map_strategy_status_dto
from qts.api.schemas.common import StrategyStatusSchema
from qts.application.services import StrategyControlService
from qts.application.strategy_lifecycle import StrategyInstance
from qts.core.ids import AccountId, StrategyId

router = APIRouter(prefix="/strategies")

# Configured strategy roster served by this API deployment. The roster is API
# wiring; lifecycle state and transitions are owned by StrategyControlService.
_CONFIGURED_STRATEGIES = (
    StrategyInstance(
        strategy_id=StrategyId("strategy-001"),
        class_path="examples.strategies.hello_world.HelloWorldStrategy",
        account_id=AccountId("acct-001"),
    ),
)
_strategies = StrategyControlService.with_configured_strategies(_CONFIGURED_STRATEGIES)


@router.get("", response_model=list[StrategyStatusSchema])
def list_strategies() -> list[StrategyStatusSchema]:
    """List configured strategies with their lifecycle status."""
    return [map_strategy_status_dto(status) for status in _strategies.list_strategies()]


@router.post("/{strategy_id}/start", response_model=StrategyStatusSchema)
def start_strategy(strategy_id: str) -> StrategyStatusSchema:
    """Start a configured strategy through the strategy control service."""
    return map_strategy_status_dto(_strategies.start(strategy_id))


@router.post("/{strategy_id}/stop", response_model=StrategyStatusSchema)
def stop_strategy(strategy_id: str) -> StrategyStatusSchema:
    """Stop a configured strategy through the strategy control service."""
    return map_strategy_status_dto(_strategies.stop(strategy_id))


__all__ = ["router"]
