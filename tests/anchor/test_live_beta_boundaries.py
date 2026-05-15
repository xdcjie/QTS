from __future__ import annotations

from decimal import Decimal

from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId
from qts.execution.broker import BrokerOrderRequest
from qts.execution.order_manager import OrderSide
from qts.reconciliation import OrderSnapshot, ReconciliationSnapshot, reconcile_snapshots
from qts.testing.fakes.broker import FakeBrokerAdapter


def test_live_broker_boundary_preserves_internal_identifiers() -> None:
    adapter = FakeBrokerAdapter(broker_id=BrokerId("fake"))
    request = BrokerOrderRequest(
        order_id=OrderId("internal-order"),
        client_order_id="client-internal-order",
        account_id=AccountId("internal-account"),
        strategy_id=None,
        instrument_id=InstrumentId("FUTURE.CME.GC.202606"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
    )

    report = adapter.submit_order(request)

    assert report.order_id == request.order_id
    assert report.account_id == request.account_id
    assert report.instrument_id == request.instrument_id
    assert "FUTURE.CME.GC.202606" not in report.broker_order_id


def test_broker_execution_adapter_normalizes_reports_without_account_mutation() -> None:
    import inspect

    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter

    source = inspect.getsource(BrokerExecutionAdapter)

    assert "BrokerOrderRequest" in source
    assert "normalize_broker_execution_report" in source
    assert "AccountActor" not in source
    assert "ApplyFill" not in source


def test_reconciliation_does_not_directly_change_order_state() -> None:
    order = OrderSnapshot(
        order_id=OrderId("order-1"),
        instrument_id=InstrumentId("FUTURE.CME.GC.202606"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        status="accepted",
    )

    report = reconcile_snapshots(
        internal=ReconciliationSnapshot(account_id=AccountId("acct-a"), orders=(order,)),
        broker=ReconciliationSnapshot(account_id=AccountId("acct-a")),
    )

    assert report.has_drift
    assert order.status == "accepted"
