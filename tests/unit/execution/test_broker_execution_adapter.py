from __future__ import annotations

from decimal import Decimal


def test_broker_execution_adapter_normalizes_submit_and_callback_reports() -> None:
    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
    from qts.execution.order_manager import ExecutionReportStatus, OrderIntent, OrderSide
    from qts.simulation.broker import SimulatedBrokerAdapter

    broker = SimulatedBrokerAdapter(broker_id=BrokerId("paper"))
    adapter = BrokerExecutionAdapter(
        broker=broker,
        account_id=AccountId("acct-a"),
        strategy_id=StrategyId("strategy-a"),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("2"),
    )

    accepted = adapter.execute_market_order(
        intent,
        broker_order_id="runtime-broker-001",
        market_price=Decimal("100"),
        account_id=AccountId("acct-a"),
        strategy_id=StrategyId("strategy-a"),
        client_order_id="client-001",
        correlation_id=None,
    )
    callback = broker.emit_fill(
        order_id=intent.order_id,
        quantity=Decimal("2"),
        price=Decimal("101"),
        fill_id="fill-001",
    )
    filled = adapter.normalize_execution_report(callback)

    assert accepted.status is ExecutionReportStatus.ACCEPTED
    assert accepted.broker_order_id == "runtime-broker-001"
    assert broker.order_request(intent.order_id).client_order_id == "client-001"
    assert filled.status is ExecutionReportStatus.FILLED
    assert filled.broker_order_id == "runtime-broker-001"
    assert filled.fill_price == Decimal("101")


def test_broker_execution_adapter_normalizes_cancel_reports_with_runtime_order_id() -> None:
    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
    from qts.execution.order_manager import ExecutionReportStatus, OrderIntent, OrderSide
    from qts.simulation.broker import SimulatedBrokerAdapter

    broker = SimulatedBrokerAdapter(broker_id=BrokerId("paper"))
    adapter = BrokerExecutionAdapter(
        broker=broker,
        account_id=AccountId("acct-a"),
        strategy_id=StrategyId("strategy-a"),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("2"),
    )
    adapter.execute_market_order(
        intent,
        broker_order_id="runtime-broker-001",
        market_price=Decimal("100"),
        account_id=AccountId("acct-a"),
        strategy_id=StrategyId("strategy-a"),
        client_order_id="client-001",
        correlation_id=None,
    )

    cancelled = adapter.cancel_order(
        intent.order_id,
        broker_order_id="runtime-broker-001",
        account_id=AccountId("acct-a"),
        strategy_id=StrategyId("strategy-a"),
        client_order_id="client-001",
        correlation_id=None,
    )

    assert cancelled.status is ExecutionReportStatus.CANCELLED
    assert cancelled.broker_order_id == "runtime-broker-001"


def test_broker_execution_adapter_rejects_intent_account_route_mismatch() -> None:
    import pytest
    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.simulation.broker import SimulatedBrokerAdapter

    adapter = BrokerExecutionAdapter(
        broker=SimulatedBrokerAdapter(broker_id=BrokerId("paper")),
        account_id=AccountId("acct-a"),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("2"),
        account_id=AccountId("acct-b"),
    )

    with pytest.raises(ValueError, match="intent account_id"):
        adapter.execute_market_order(
            intent,
            broker_order_id="runtime-broker-001",
            market_price=Decimal("100"),
            account_id=AccountId("acct-a"),
            strategy_id=StrategyId("strategy-a"),
            client_order_id="client-001",
            correlation_id=None,
        )


def test_broker_execution_adapter_rejects_unknown_broker_order_id() -> None:
    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId
    from qts.domain.orders import ExecutionReportStatus
    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
    from qts.execution.broker import BrokerExecutionReport
    from qts.simulation.broker import SimulatedBrokerAdapter

    adapter = BrokerExecutionAdapter(
        broker=SimulatedBrokerAdapter(broker_id=BrokerId("paper")),
        account_id=AccountId("acct-a"),
    )

    unknown = BrokerExecutionReport(
        report_id="rpt-unknown",
        broker_id=BrokerId("paper"),
        broker_order_id="broker-missing",
        order_id=OrderId("ord-unknown"),
        account_id=AccountId("acct-a"),
        strategy_id=None,
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        status=ExecutionReportStatus.FILLED,
        filled_quantity=Decimal("1"),
        fill_price=Decimal("100"),
        fill_id="fill-unknown",
    )

    import pytest

    with pytest.raises(ValueError, match="unknown broker_order_id"):
        adapter.normalize_execution_report(unknown)


def test_broker_execution_adapter_can_recover_runtime_broker_order_mapping() -> None:
    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId
    from qts.domain.orders import ExecutionReportStatus
    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
    from qts.execution.broker import BrokerExecutionReport
    from qts.execution.order_manager import Order, OrderIntent, OrderSide, OrderStateSnapshot
    from qts.execution.order_state_machine import OrderState
    from qts.simulation.broker import SimulatedBrokerAdapter

    order_id = OrderId("ord-001")
    adapter = BrokerExecutionAdapter(
        broker=SimulatedBrokerAdapter(broker_id=BrokerId("paper")),
        account_id=AccountId("acct-a"),
    )
    adapter.restore_order_mapping(
        OrderStateSnapshot(
            orders=(
                Order(
                    order_id=order_id,
                    intent=OrderIntent(
                        order_id=order_id,
                        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                        side=OrderSide.BUY,
                        quantity=Decimal("1"),
                    ),
                    state=OrderState.ACCEPTED,
                    broker_order_id="runtime-broker-001",
                ),
            ),
            broker_to_order=(("runtime-broker-001", order_id),),
        ),
        broker_order_ids_by_runtime_id={"runtime-broker-001": "paper-1"},
    )

    report = BrokerExecutionReport(
        report_id="rpt-001",
        broker_id=BrokerId("paper"),
        broker_order_id="paper-1",
        order_id=order_id,
        account_id=AccountId("acct-a"),
        strategy_id=None,
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        status=ExecutionReportStatus.FILLED,
        filled_quantity=Decimal("1"),
        fill_price=Decimal("100"),
        fill_id="fill-001",
    )

    normalized = adapter.normalize_execution_report(report)

    assert normalized.broker_order_id == "runtime-broker-001"
