from __future__ import annotations

from decimal import Decimal


def test_operational_dashboard_snapshot_serializes_runtime_schema() -> None:
    from qts.observability.dashboard import (
        BrokerConnectionSnapshot,
        DashboardCashSnapshot,
        DashboardPositionSnapshot,
        OpenOrderSnapshot,
        OperationalDashboardSnapshot,
        RiskStatusSnapshot,
        RuntimeSubscriptionSnapshot,
    )

    snapshot = OperationalDashboardSnapshot(
        runtime_state="running",
        subscriptions=(
            RuntimeSubscriptionSnapshot(
                subscription_id="sub-1",
                instrument_id="EQUITY.US.NASDAQ.AAPL",
                requested_timeframe="1m",
                source_id="live-feed",
                status="active",
            ),
        ),
        open_orders=(
            OpenOrderSnapshot(
                order_id="order-1",
                account_id="acct-1",
                instrument_id="EQUITY.US.NASDAQ.AAPL",
                status="submitted",
            ),
        ),
        positions=(
            DashboardPositionSnapshot(
                account_id="acct-1",
                instrument_id="EQUITY.US.NASDAQ.AAPL",
                quantity=Decimal("10"),
            ),
        ),
        cash=(DashboardCashSnapshot(account_id="acct-1", currency="USD", balance=Decimal("1000")),),
        risk=RiskStatusSnapshot(status="enabled", kill_switch_active=False),
        broker_connection=BrokerConnectionSnapshot(status="connected", broker_id="broker-1"),
        reconciliation_status="clean",
    )

    assert snapshot.to_schema() == {
        "runtime_state": "running",
        "subscriptions": [
            {
                "subscription_id": "sub-1",
                "instrument_id": "EQUITY.US.NASDAQ.AAPL",
                "requested_timeframe": "1m",
                "source_id": "live-feed",
                "status": "active",
            }
        ],
        "open_orders": [
            {
                "order_id": "order-1",
                "account_id": "acct-1",
                "instrument_id": "EQUITY.US.NASDAQ.AAPL",
                "status": "submitted",
            }
        ],
        "positions": [
            {
                "account_id": "acct-1",
                "instrument_id": "EQUITY.US.NASDAQ.AAPL",
                "quantity": "10",
            }
        ],
        "cash": [{"account_id": "acct-1", "currency": "USD", "balance": "1000"}],
        "risk": {"status": "enabled", "kill_switch_active": False},
        "broker_connection": {"status": "connected", "broker_id": "broker-1"},
        "reconciliation_status": "clean",
    }
