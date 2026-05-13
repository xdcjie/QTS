from __future__ import annotations

import pytest
from qts.runtime.live import LiveRuntimeState, LiveRuntimeStateMachine


def test_live_runtime_state_machine_allows_only_operational_transitions() -> None:
    machine = LiveRuntimeStateMachine()

    assert machine.apply("start") is LiveRuntimeState.STARTING
    assert machine.apply("started") is LiveRuntimeState.RUNNING
    assert machine.apply("pause") is LiveRuntimeState.PAUSED
    assert machine.apply("resume") is LiveRuntimeState.RUNNING
    assert machine.apply("degrade") is LiveRuntimeState.DEGRADED
    assert machine.apply("recover") is LiveRuntimeState.RUNNING
    assert machine.apply("stop") is LiveRuntimeState.STOPPED

    with pytest.raises(ValueError, match="invalid live runtime transition"):
        machine.apply("resume")


def test_live_runtime_degrades_from_runtime_event_and_rejects_new_orders() -> None:
    from decimal import Decimal

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId
    from qts.data.live_feed import FakeLiveFeedAdapter
    from qts.execution.broker import BrokerOrderRequest, FakeBrokerAdapter
    from qts.execution.order_manager import OrderSide
    from qts.runtime.live import LiveRuntime
    from qts.runtime.sinks.base import RuntimeEvent

    runtime = LiveRuntime(
        broker=FakeBrokerAdapter(broker_id=BrokerId("paper")),
        feed=FakeLiveFeedAdapter(source_id="ibkr-paper-md"),
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
            account_id=AccountId("DU1234567"),
            strategy_id=None,
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        )
    )

    assert state is LiveRuntimeState.DEGRADED
    assert result.accepted is False
    assert result.reason_code == "RUNTIME_DEGRADED"
