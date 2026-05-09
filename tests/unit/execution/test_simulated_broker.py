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
