"""Integration: signed position limit blocks risk-increasing but not de-risking orders (DR-007)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.risk.rules.position_limit import PositionLimitRule

from tests.support.risk_runtime_harness import RiskRuntimeHarness


def _harness() -> RiskRuntimeHarness:
    return RiskRuntimeHarness(
        rules=[PositionLimitRule(max_position=Decimal("10"))],
        multiplier=Decimal("1"),
        initial_cash=Decimal("1000000"),
    )


def test_de_risking_order_is_allowed_at_limit() -> None:
    harness = _harness()
    # Build to the limit (target 10 from flat -> +10 -> projected 10, allowed).
    opened = harness.submit(
        target_quantity="10", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100"
    )
    assert opened.fills
    # De-risk to 5 (target 5 -> -5 -> net projected 5) must be allowed.
    derisk = harness.submit(
        target_quantity="5", when=datetime(2026, 1, 2, 14, 31, tzinfo=UTC), price="100"
    )
    assert derisk.orders
    assert all(d.approved for d in derisk.risk_decisions)


def test_risk_increasing_order_beyond_limit_is_blocked() -> None:
    harness = _harness()
    harness.submit(target_quantity="10", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100")
    # Target 20 from 10 -> +10 -> projected 20 > limit 10 -> rejected.
    blocked = harness.submit(
        target_quantity="20", when=datetime(2026, 1, 2, 14, 31, tzinfo=UTC), price="100"
    )
    assert blocked.orders == ()
    assert blocked.risk_decisions[0].reason_code == "POSITION_LIMIT_EXCEEDED"
    assert blocked.risk_decisions[0].evidence["projected_position"] == Decimal("20")
