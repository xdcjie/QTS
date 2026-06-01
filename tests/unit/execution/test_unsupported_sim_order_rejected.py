"""Unsupported simulated order shapes become structured rejection reports."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import (
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
    OrderSpec,
    OrderType,
)
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.runtime.config import BacktestCostModel


def test_simulated_adapter_rejects_unsupported_order_without_exception() -> None:
    adapter = SimulatedExecutionAdapter(BacktestCostModel())
    intent = OrderIntent(
        order_id=OrderId("order-1"),
        instrument_id=InstrumentId("FUTURE.CME.GC.GCM6"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        account_id=AccountId("acct-1"),
        order_spec=OrderSpec(order_type=OrderType.TRAILING_STOP, trail_amount=Decimal("1")),
    )

    report = adapter.execute_market_order(
        intent,
        broker_order_id="broker-1",
        market_price=Decimal("100"),
        account_id=AccountId("acct-1"),
        strategy_id=StrategyId("strategy-1"),
        client_order_id="client-1",
        correlation_id=CorrelationId("corr-1"),
        bar_high=Decimal("101"),
        bar_low=Decimal("99"),
        bar_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
    )

    assert report.status is ExecutionReportStatus.REJECTED
    assert report.reason_code == "UNSUPPORTED_ORDER_TYPE"
    assert report.failure_reason == "simulated execution does not support trailing_stop orders"
