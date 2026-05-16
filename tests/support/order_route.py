from __future__ import annotations

from qts.core.ids import AccountId, BrokerId, CorrelationId, StrategyId
from qts.runtime.actors.order_manager_actor import OrderRouteMetadata


def order_route_metadata(
    *,
    account_id: AccountId,
    strategy_id: StrategyId,
    client_order_id: str = "client-001",
    correlation_id: CorrelationId | None = None,
    broker_id: BrokerId | None = None,
) -> OrderRouteMetadata:
    return OrderRouteMetadata(
        broker_id=broker_id or BrokerId("broker-route"),
        account_id=account_id,
        strategy_id=strategy_id,
        client_order_id=client_order_id,
        correlation_id=correlation_id or CorrelationId("corr-001"),
    )
