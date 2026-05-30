"""Actor-facing order execution adapter protocol."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from qts.core.ids import AccountId, CorrelationId, OrderId, StrategyId
from qts.domain.orders import ExecutionReport, OrderIntent


class ExecutionAdapter(Protocol):
    """Execution boundary contract used by runtime actors."""

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
        bar_time: datetime | None = None,
    ) -> ExecutionReport:
        """Execute a market order."""
        ...

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        """Cancel an active order."""
        ...

    def replace_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        new_quantity: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        """Replace (modify) an active order's quantity at the broker.

        Only invoked for brokers whose ``BrokerCapabilities.supports_replace``
        is true; the runtime gates unsupported brokers with
        ``UnsupportedOrderReplace`` before routing here.
        """
        ...


__all__ = ["ExecutionAdapter"]
