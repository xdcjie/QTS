from __future__ import annotations

from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.orders import OrderSide
from qts.reconciliation import (
    DriftKind,
    OrderSnapshot,
    ReconciliationCashSnapshot,
    ReconciliationPositionSnapshot,
    ReconciliationSnapshot,
    reconcile_snapshots,
)


def test_reconciliation_classifies_order_position_and_cash_drift_deterministically() -> None:
    account_id = AccountId("acct-a")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    internal = ReconciliationSnapshot(
        account_id=account_id,
        orders=(
            OrderSnapshot(
                order_id=OrderId("1"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("10"),
                status="accepted",
            ),
            OrderSnapshot(
                order_id=OrderId("2"),
                instrument_id=instrument_id,
                side=OrderSide.SELL,
                quantity=Decimal("1"),
                status="accepted",
            ),
        ),
        positions=(
            ReconciliationPositionSnapshot(instrument_id=instrument_id, quantity=Decimal("10")),
        ),
        cash=(ReconciliationCashSnapshot(currency="USD", balance=Decimal("1000.00")),),
    )
    broker = ReconciliationSnapshot(
        account_id=account_id,
        orders=(
            OrderSnapshot(
                order_id=OrderId("1"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("12"),
                status="accepted",
            ),
            OrderSnapshot(
                order_id=OrderId("3"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("5"),
                status="accepted",
            ),
        ),
        positions=(
            ReconciliationPositionSnapshot(instrument_id=instrument_id, quantity=Decimal("10")),
        ),
        cash=(ReconciliationCashSnapshot(currency="USD", balance=Decimal("1000.005")),),
    )

    report = reconcile_snapshots(internal=internal, broker=broker, tolerance=Decimal("0.01"))

    assert [item.kind for item in report.items] == [
        DriftKind.DIVERGENT,
        DriftKind.MISSING_AT_BROKER,
        DriftKind.EXTRA_AT_BROKER,
        DriftKind.MATCHED,
        DriftKind.TOLERANCE_ONLY,
    ]
    assert report.to_dict()["items"][0]["key"] == "order:1"
