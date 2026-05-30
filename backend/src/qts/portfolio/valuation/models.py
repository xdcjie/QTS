"""Portfolio valuation formulas."""

from __future__ import annotations

from decimal import Decimal


def equity_notional(*, quantity: Decimal, price: Decimal) -> Decimal:
    """Return the equity notional value (quantity times price)."""
    return quantity * price


def future_pnl(
    *,
    contracts: Decimal,
    entry_price: Decimal,
    exit_price: Decimal,
    multiplier: Decimal,
) -> Decimal:
    """Return the futures P&L from entry to exit across all contracts."""
    return contracts * (exit_price - entry_price) * multiplier


def option_premium_value(
    *,
    contracts: Decimal,
    option_price: Decimal,
    multiplier: Decimal,
) -> Decimal:
    """Return the total option premium value across all contracts."""
    return contracts * option_price * multiplier


__all__ = ["equity_notional", "future_pnl", "option_premium_value"]
