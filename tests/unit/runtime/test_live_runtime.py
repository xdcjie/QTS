from __future__ import annotations

import pytest
from qts.runtime.state import (
    RuntimeSessionState as RuntimeSessionState,
)
from qts.runtime.state import (
    RuntimeStateMachine as RuntimeStateMachine,
)


def test_live_runtime_state_machine_allows_only_operational_transitions() -> None:
    machine = RuntimeStateMachine()

    assert machine.apply("start") is RuntimeSessionState.STARTING
    assert machine.apply("started") is RuntimeSessionState.RUNNING
    assert machine.apply("pause") is RuntimeSessionState.PAUSED
    assert machine.apply("resume") is RuntimeSessionState.RUNNING
    assert machine.apply("degrade") is RuntimeSessionState.DEGRADED
    assert machine.apply("recover") is RuntimeSessionState.RUNNING
    assert machine.apply("stop") is RuntimeSessionState.STOPPED

    with pytest.raises(ValueError, match="invalid runtime transition"):
        machine.apply("resume")


def test_live_runtime_degrades_from_runtime_event_and_rejects_new_orders() -> None:
    from decimal import Decimal

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId
    from qts.execution.broker import BrokerOrderRequest
    from qts.execution.order_manager import OrderSide
    from qts.runtime.live import LiveRuntime
    from qts.runtime.sinks.base import RuntimeEvent
    from qts.testing.fakes.broker import FakeBrokerAdapter
    from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

    runtime = LiveRuntime(
        broker=FakeBrokerAdapter(broker_id=BrokerId("paper")),
        feed=FakeStreamingMarketDataAdapter(source_id="ibkr-paper-md"),
    )
    runtime.start()

    state = runtime.apply_runtime_event(
        RuntimeEvent(
            kind="runtime.degraded",
            payload={"reason": "stale_market_data"},
        )
    )
    result = runtime.submit_order(
        BrokerOrderRequest(
            order_id=OrderId("ord-001"),
            client_order_id="client-ord-001",
            account_id=AccountId("DU1234567"),
            strategy_id=None,
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        )
    )

    assert state is RuntimeSessionState.DEGRADED
    assert result.accepted is False
    assert result.reason_code == "RUNTIME_DEGRADED"


def test_live_runtime_direct_submit_path_is_disabled_when_running() -> None:
    from decimal import Decimal

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId
    from qts.execution.broker import BrokerOrderRequest
    from qts.execution.order_manager import OrderSide
    from qts.runtime.live import LiveRuntime
    from qts.testing.fakes.broker import FakeBrokerAdapter
    from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

    broker = FakeBrokerAdapter(broker_id=BrokerId("paper"))
    runtime = LiveRuntime(
        broker=broker,
        feed=FakeStreamingMarketDataAdapter(source_id="ibkr-paper-md"),
    )
    runtime.start()

    result = runtime.submit_order(
        BrokerOrderRequest(
            order_id=OrderId("ord-direct-001"),
            client_order_id="client-ord-direct-001",
            account_id=AccountId("DU1234567"),
            strategy_id=None,
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        )
    )

    assert result.accepted is False
    assert result.reason_code == "DIRECT_ORDER_PATH_DISABLED"
    assert result.report is None
