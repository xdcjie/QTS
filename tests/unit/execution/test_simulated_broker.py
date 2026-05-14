from __future__ import annotations

from decimal import Decimal


def test_simulated_broker_fills_market_order_from_provided_market_data() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.execution.order_manager import ExecutionReportStatus, OrderIntent, OrderSide
    from qts.execution.simulator.simulated_broker import SimulatedBroker

    broker = SimulatedBroker()
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    report = broker.execute_market_order(
        intent,
        broker_order_id="sim-001",
        market_price=Decimal("101.25"),
    )

    assert report.broker_order_id == "sim-001"
    assert report.status is ExecutionReportStatus.FILLED
    assert report.filled_quantity == Decimal("10")
    assert report.fill_price == Decimal("101.25")
    assert report.fill_id == "sim-001-fill-1"


def test_simulated_execution_adapter_rejects_orders_blocked_by_broker_capabilities() -> None:
    import pytest
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.execution.broker import BrokerCapabilities
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.runtime.config import BacktestCostModel

    adapter = SimulatedExecutionAdapter(
        cost_model=BacktestCostModel(),
        capabilities=BrokerCapabilities(
            broker_id=BrokerId("ibkr-equity"),
            supports_market_orders=True,
            supports_fractional=False,
            max_order_quantity=Decimal("100"),
        ),
    )

    with pytest.raises(ValueError, match="fractional"):
        adapter.execute_market_order(
            OrderIntent(
                order_id=OrderId("ord-fractional"),
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                side=OrderSide.BUY,
                quantity=Decimal("1.5"),
            ),
            broker_order_id="sim-001",
            market_price=Decimal("101.25"),
        )

    with pytest.raises(ValueError, match="max order quantity"):
        adapter.execute_market_order(
            OrderIntent(
                order_id=OrderId("ord-large"),
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                side=OrderSide.BUY,
                quantity=Decimal("101"),
            ),
            broker_order_id="sim-002",
            market_price=Decimal("101.25"),
        )
