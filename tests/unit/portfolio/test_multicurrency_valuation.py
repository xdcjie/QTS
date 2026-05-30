"""Gate tests for multi-currency portfolio valuation with FX rates (DR-032)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.portfolio.valuation.valuator import PortfolioValuator


def test_valuate_converts_cash_with_fx_rates_to_base_currency() -> None:
    valuation = PortfolioValuator.valuate(
        cash={"USD": Decimal("1000"), "EUR": Decimal("500")},
        holdings={},
        marks={},
        multipliers={},
        fx_rates={"EUR": Decimal("1.1")},
        base_currency="USD",
    )
    # 1000 USD + 500 EUR * 1.1 = 1550 USD.
    assert valuation.account_equity == Decimal("1550.0")


def test_valuate_fails_closed_on_missing_fx_rate() -> None:
    with pytest.raises(ValueError, match="missing FX rate"):
        PortfolioValuator.valuate(
            cash={"USD": Decimal("1000"), "JPY": Decimal("100000")},
            holdings={},
            marks={},
            multipliers={},
            fx_rates={"EUR": Decimal("1.1")},
            base_currency="USD",
        )


def test_valuate_single_currency_without_rates_is_unchanged() -> None:
    valuation = PortfolioValuator.valuate(
        cash={"USD": Decimal("1000")},
        holdings={},
        marks={},
        multipliers={},
    )
    assert valuation.account_equity == Decimal("1000")
