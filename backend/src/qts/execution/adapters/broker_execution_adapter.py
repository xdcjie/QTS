"""Broker-backed execution adapter boundary."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from qts.core.ids import AccountId, OrderId, StrategyId
from qts.execution.broker import (
    BrokerAdapter,
    BrokerExecutionReport,
    BrokerOrderRequest,
    normalize_broker_execution_report,
)
from qts.execution.order_manager import ExecutionReport, OrderIntent


class BrokerExecutionAdapter:
    """Adapt live or paper broker reports to the shared execution actor contract."""

    def __init__(
        self,
        *,
        broker: BrokerAdapter,
        account_id: AccountId,
        strategy_id: StrategyId | None = None,
    ) -> None:
        """Create a broker-backed execution adapter."""
        self._broker = broker
        self._account_id = account_id
        self._strategy_id = strategy_id
        self._runtime_broker_order_id_by_broker_order_id: dict[str, str] = {}

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        """Submit a market order and normalize the broker acknowledgement."""
        _ = market_price
        broker_report = self._broker.submit_order(
            BrokerOrderRequest(
                order_id=intent.order_id,
                account_id=self._account_id,
                strategy_id=self._strategy_id,
                instrument_id=intent.instrument_id,
                side=intent.side,
                quantity=intent.quantity,
            )
        )
        self._runtime_broker_order_id_by_broker_order_id[broker_report.broker_order_id] = (
            broker_order_id
        )
        return self._normalize_with_runtime_broker_order_id(broker_report)

    def normalize_execution_report(
        self,
        report: BrokerExecutionReport,
    ) -> ExecutionReport:
        """Normalize an asynchronous broker callback for the order manager actor."""
        return self._normalize_with_runtime_broker_order_id(report)

    def cancel_order(self, order_id: OrderId, *, broker_order_id: str) -> ExecutionReport:
        """Cancel an active broker order and normalize the broker callback."""
        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        broker_report = self._broker.cancel_order(order_id)
        return self._normalize_with_runtime_broker_order_id(broker_report)

    def _normalize_with_runtime_broker_order_id(
        self,
        report: BrokerExecutionReport,
    ) -> ExecutionReport:
        runtime_broker_order_id = self._runtime_broker_order_id_by_broker_order_id.get(
            report.broker_order_id
        )
        if runtime_broker_order_id is None:
            raise ValueError(f"unknown broker_order_id: {report.broker_order_id}")
        return replace(
            normalize_broker_execution_report(report),
            broker_order_id=runtime_broker_order_id,
        )


__all__ = ["BrokerExecutionAdapter"]
