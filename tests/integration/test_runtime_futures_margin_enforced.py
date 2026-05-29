"""Integration: futures order exceeding available margin is rejected pre-trade (DR-005)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.risk.margin.calculator import MarginCalculator
from qts.risk.rules.margin_limit import MarginRule

from tests.support.risk_runtime_harness import RiskRuntimeHarness


def _harness(initial_cash: str) -> RiskRuntimeHarness:
    return RiskRuntimeHarness(
        rules=[MarginRule()],
        multiplier=Decimal("100"),
        initial_cash=Decimal(initial_cash),
        margin_calculator=MarginCalculator(initial_margin_rate=Decimal("0.05")),
    )


def test_runtime_rejects_order_exceeding_available_margin() -> None:
    # Equity 10000; a 30-lot needs 30*100*100*0.05 = 15000 initial margin > 10000.
    harness = _harness("10000")
    result = harness.submit(
        target_quantity="30", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100"
    )
    assert result.orders == ()
    assert result.fills == ()
    assert len(result.risk_decisions) == 1
    decision = result.risk_decisions[0]
    assert decision.reason_code == "MARGIN_LIMIT_EXCEEDED"
    assert decision.evidence["available_margin"] == Decimal("10000")
    assert decision.evidence["projected_margin"] == Decimal("15000")


def test_runtime_approves_order_within_available_margin() -> None:
    # Equity 1,000,000; a 2-lot needs only 1000 margin -> approved and filled.
    harness = _harness("1000000")
    result = harness.submit(
        target_quantity="2", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100"
    )
    assert result.orders
    assert all(d.approved for d in result.risk_decisions)
