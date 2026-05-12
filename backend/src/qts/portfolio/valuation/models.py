"""Portfolio valuation formulas."""

from __future__ import annotations

from decimal import Decimal


def equity_notional(*, quantity: Decimal, price: Decimal) -> Decimal:
    """Perform equity_notional."""
    return quantity * price


def future_pnl(
    *,
    contracts: Decimal,
    entry_price: Decimal,
    exit_price: Decimal,
    multiplier: Decimal,
) -> Decimal:
    """Perform future_pnl."""
    return contracts * (exit_price - entry_price) * multiplier


def option_premium_value(
    *,
    contracts: Decimal,
    option_price: Decimal,
    multiplier: Decimal,
) -> Decimal:
    """Perform option_premium_value."""
    return contracts * option_price * multiplier


__all__ = ["equity_notional", "future_pnl", "option_premium_value"]
