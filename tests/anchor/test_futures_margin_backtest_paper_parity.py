"""Anchor: futures margin economics reject identically on the shared runtime path."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.risk.margin.calculator import MarginCalculator
from qts.risk.rules.margin_limit import MarginRule

from tests.support.risk_runtime_harness import RiskRuntimeHarness


def test_futures_margin_backtest_paper_parity() -> None:
    harness = RiskRuntimeHarness(
        rules=[MarginRule()],
        multiplier=Decimal("100"),
        initial_cash=Decimal("10000"),
        margin_calculator=MarginCalculator(initial_margin_rate=Decimal("0.05")),
    )

    result = harness.submit(
        target_quantity="30",
        when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        price="100",
    )

    assert result.orders == ()
    assert result.fills == ()
    assert result.risk_decisions[0].reason_code == "MARGIN_LIMIT_EXCEEDED"
