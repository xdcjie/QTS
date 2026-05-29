"""Integration: intraday loss limit halts new orders once breached (DR-006)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.risk.intraday_pnl import IntradayPnlCalculator
from qts.risk.rules.intraday_loss_limit import IntradayLossLimitRule

from tests.support.risk_runtime_harness import RiskRuntimeHarness


def test_runtime_rejects_new_order_after_intraday_loss_breached() -> None:
    harness = RiskRuntimeHarness(
        rules=[IntradayLossLimitRule(max_loss=Decimal("50"))],
        multiplier=Decimal("1"),
        initial_cash=Decimal("100000"),
        intraday_pnl_calculator=IntradayPnlCalculator(),
    )

    # Open a 10-lot long at 100 (flat session start -> intraday pnl 0, approved).
    opened = harness.submit(
        target_quantity="10", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100"
    )
    assert opened.fills

    # Same session, price drops to 90 -> unrealized = 10*(90-100) = -100 < -50.
    blocked = harness.submit(
        target_quantity="11", when=datetime(2026, 1, 2, 15, 0, tzinfo=UTC), price="90"
    )
    assert blocked.orders == ()
    assert blocked.risk_decisions[0].reason_code == "INTRADAY_LOSS_LIMIT_EXCEEDED"


def test_runtime_resets_intraday_window_on_new_session() -> None:
    harness = RiskRuntimeHarness(
        rules=[IntradayLossLimitRule(max_loss=Decimal("50"))],
        multiplier=Decimal("1"),
        initial_cash=Decimal("100000"),
        intraday_pnl_calculator=IntradayPnlCalculator(),
    )
    harness.submit(target_quantity="10", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100")
    # New session (next day) at the recovered price 100 -> unrealized 0 -> allowed again.
    recovered = harness.submit(
        target_quantity="11", when=datetime(2026, 1, 5, 14, 30, tzinfo=UTC), price="100"
    )
    assert recovered.orders
