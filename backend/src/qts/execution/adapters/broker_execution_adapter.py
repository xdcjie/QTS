"""Broker-backed execution adapter boundary."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from qts.core.ids import AccountId, CorrelationId, OrderId, StrategyId
from qts.domain.orders import ExecutionReport, OrderIntent, OrderStateSnapshot
from qts.execution.broker import (
    BrokerAdapter,
    BrokerCapabilities,
    BrokerExecutionReport,
    BrokerOrderRequest,
    normalize_broker_execution_report,
)


class BrokerExecutionAdapter:
    """Adapt live or paper broker reports to the shared execution actor contract."""

    def __init__(
        self,
        *,
        broker: BrokerAdapter,
        account_id: AccountId,
        strategy_id: StrategyId | None = None,
        live_capital_decision: object | None = None,
    ) -> None:
        """Create a broker-backed execution adapter."""
        self._broker = broker
        self._account_id = account_id
        self._strategy_id = strategy_id
        self._live_capital_decision = live_capital_decision
        self._runtime_broker_order_id_by_broker_order_id: dict[str, str] = {}

    @property
    def capabilities(self) -> BrokerCapabilities:
        """Return the broker capabilities enforced by the wrapped adapter."""
        return self._broker.capabilities

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId | None = None,
        bar_time: datetime | None = None,
    ) -> ExecutionReport:
        """Submit a market order and normalize the broker acknowledgement."""
        _ = market_price, correlation_id
        self._assert_live_capital_order_allowed()
        if intent.account_id is not None and intent.account_id != account_id:
            raise ValueError("intent account_id does not match execution route account_id")
        self._validate_route(account_id=account_id, strategy_id=strategy_id)
        broker_report = self._broker.submit_order(
            BrokerOrderRequest(
                order_id=intent.order_id,
                client_order_id=client_order_id,
                account_id=account_id,
                strategy_id=strategy_id,
                instrument_id=intent.instrument_id,
                side=intent.side,
                quantity=intent.quantity,
            )
        )
        self._runtime_broker_order_id_by_broker_order_id[broker_report.broker_order_id] = (
            broker_order_id
        )
        return self._normalize_with_runtime_broker_order_id(broker_report, bar_time=bar_time)

    def normalize_execution_report(
        self,
        report: BrokerExecutionReport,
    ) -> ExecutionReport:
        """Normalize an asynchronous broker callback for the order manager actor."""
        return self._normalize_with_runtime_broker_order_id(report)

    def restore_order_mapping(
        self,
        snapshot: OrderStateSnapshot,
        *,
        broker_order_ids_by_runtime_id: dict[str, str] | None = None,
    ) -> None:
        """Restore broker callback ID mapping from recovered order manager state."""
        external_by_runtime = dict(broker_order_ids_by_runtime_id or {})
        for runtime_broker_order_id, _order_id in snapshot.broker_to_order:
            external_broker_order_id = external_by_runtime.get(
                runtime_broker_order_id,
                runtime_broker_order_id,
            )
            self._runtime_broker_order_id_by_broker_order_id[external_broker_order_id] = (
                runtime_broker_order_id
            )

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId | None = None,
    ) -> ExecutionReport:
        """Cancel an active broker order and normalize the broker callback."""
        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        if not client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        _ = correlation_id
        self._validate_route(account_id=account_id, strategy_id=strategy_id)
        broker_report = self._broker.cancel_order(order_id)
        return self._normalize_with_runtime_broker_order_id(broker_report)

    def replace_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        new_quantity: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId | None = None,
    ) -> ExecutionReport:
        """Replace an active broker order's quantity and normalize the callback."""
        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        if not client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        _ = correlation_id
        self._validate_route(account_id=account_id, strategy_id=strategy_id)
        broker_report = self._broker.replace_order(order_id, new_quantity=new_quantity)
        return self._normalize_with_runtime_broker_order_id(broker_report)

    def _validate_route(self, *, account_id: AccountId, strategy_id: StrategyId) -> None:
        if account_id != self._account_id:
            raise ValueError("account_id does not match BrokerExecutionAdapter account_id")
        if self._strategy_id is not None and strategy_id != self._strategy_id:
            raise ValueError("strategy_id does not match BrokerExecutionAdapter strategy_id")

    def _assert_live_capital_order_allowed(self) -> None:
        gate = self._live_capital_decision
        if gate is None:
            return
        cast(Any, gate).assert_live_order_allowed()

    def _normalize_with_runtime_broker_order_id(
        self,
        report: BrokerExecutionReport,
        *,
        bar_time: datetime | None = None,
    ) -> ExecutionReport:
        runtime_broker_order_id = self._runtime_broker_order_id_by_broker_order_id.get(
            report.broker_order_id
        )
        if runtime_broker_order_id is None:
            raise ValueError(f"unknown broker_order_id: {report.broker_order_id}")
        runtime_report = normalize_broker_execution_report(report)
        # Prefer the broker's own fill timestamp; fall back to bar_time when the
        # broker omits it so downstream holding-bar tracking stays correct.
        if runtime_report.fill_time is None and bar_time is not None:
            runtime_report = replace(runtime_report, fill_time=bar_time)
        return replace(runtime_report, broker_order_id=runtime_broker_order_id)


__all__ = ["BrokerExecutionAdapter"]
