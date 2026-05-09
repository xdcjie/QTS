from __future__ import annotations

from decimal import Decimal


def test_valuation_formulas_use_product_multipliers() -> None:
    from qts.portfolio.valuation.models import equity_notional, future_pnl, option_premium_value

    assert equity_notional(quantity=Decimal("10"), price=Decimal("25")) == Decimal("250")
    assert future_pnl(
        contracts=Decimal("2"),
        entry_price=Decimal("5000"),
        exit_price=Decimal("5010"),
        multiplier=Decimal("50"),
    ) == Decimal("1000")
    assert option_premium_value(
        contracts=Decimal("3"),
        option_price=Decimal("2.50"),
        multiplier=Decimal("100"),
    ) == Decimal("750.00")
