from __future__ import annotations

from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.execution.order_manager import Order, OrderIntent, OrderSide, OrderStateSnapshot
from qts.execution.order_state_machine import OrderState
from qts.runtime.actors.account_actor import AccountSnapshot


def test_live_reconciliation_builds_internal_snapshot_and_blocks_startup_on_drift() -> None:
    from qts.portfolio.holdings import Holding
    from qts.reconciliation.snapshots import ReconciliationCashSnapshot, ReconciliationSnapshot
    from qts.runtime.broker_runtime_reconciliation import BrokerRuntimeReconciliation

    account_id = AccountId("acct-a")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    order_id = OrderId("ord-1")
    reconciler = BrokerRuntimeReconciliation(account_id=account_id)
    internal = reconciler.internal_snapshot(
        order_manager=OrderStateSnapshot(
            orders=(
                Order(
                    order_id=order_id,
                    intent=OrderIntent(
                        order_id=order_id,
                        instrument_id=instrument_id,
                        side=OrderSide.BUY,
                        quantity=Decimal("1"),
                    ),
                    state=OrderState.ACCEPTED,
                    broker_order_id="broker-1",
                ),
            ),
            broker_to_order=(("broker-1", order_id),),
        ),
        account=AccountSnapshot(
            cash={"USD": Decimal("1000")},
            positions={
                instrument_id: Holding(
                    instrument_id=instrument_id,
                    quantity=Decimal("1"),
                    average_cost=Decimal("0"),
                    realized_pnl=Decimal("0"),
                )
            },
        ),
    )
    broker = ReconciliationSnapshot(
        account_id=account_id,
        cash=(ReconciliationCashSnapshot(currency="USD", balance=Decimal("900")),),
    )

    decision = reconciler.startup_decision(internal=internal, broker=broker)

    assert decision.trading_enabled is False
    assert decision.reason_code == "RECONCILIATION_DRIFT"
    assert [item.key for item in decision.report.items] == [
        "order:ord-1",
        "position:EQUITY.US.NASDAQ.AAPL",
        "cash:USD",
    ]


def test_live_reconciliation_periodic_drift_emits_degradation_event() -> None:
    from qts.reconciliation.snapshots import ReconciliationCashSnapshot, ReconciliationSnapshot
    from qts.runtime.broker_runtime_reconciliation import BrokerRuntimeReconciliation

    account_id = AccountId("acct-a")
    reconciler = BrokerRuntimeReconciliation(account_id=account_id)

    result = reconciler.periodic_check(
        internal=ReconciliationSnapshot(
            account_id=account_id,
            cash=(ReconciliationCashSnapshot(currency="USD", balance=Decimal("1000")),),
        ),
        broker=ReconciliationSnapshot(
            account_id=account_id,
            cash=(ReconciliationCashSnapshot(currency="USD", balance=Decimal("999")),),
        ),
    )

    assert result.report.has_drift is True
    assert result.runtime_event is not None
    assert result.runtime_event.kind == "runtime.degraded"
    assert result.runtime_event.payload["reason"] == "reconciliation_drift"
