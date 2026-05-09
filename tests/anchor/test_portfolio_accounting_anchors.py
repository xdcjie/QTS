from __future__ import annotations

from decimal import Decimal


def test_portfolio_accounting_anchor_formulas() -> None:
    from qts.portfolio.valuation.models import equity_notional, future_pnl, option_premium_value

    assert equity_notional(quantity=Decimal("100"), price=Decimal("50")) == Decimal("5000")
    assert future_pnl(
        contracts=Decimal("1"),
        entry_price=Decimal("2350.10"),
        exit_price=Decimal("2351.20"),
        multiplier=Decimal("100"),
    ) == Decimal("110.00")
    assert option_premium_value(
        contracts=Decimal("1"),
        option_price=Decimal("4.25"),
        multiplier=Decimal("100"),
    ) == Decimal("425.00")
