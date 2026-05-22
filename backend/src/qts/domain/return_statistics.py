"""Pure return-series statistics shared by research and production logic."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal


def mean_return(values: Iterable[Decimal]) -> Decimal:
    """Return the arithmetic mean of decimal return-like values."""
    items = tuple(values)
    if not items:
        return Decimal("0")
    return sum(items, Decimal("0")) / Decimal(len(items))


def compound_return(returns: Iterable[Decimal]) -> Decimal:
    """Return cumulative compounded return from period returns."""
    compounded = Decimal("1")
    for value in returns:
        compounded *= Decimal("1") + value
    return compounded - Decimal("1")


def realized_volatility(returns: Iterable[Decimal]) -> Decimal:
    """Return realized volatility using population variance."""
    values = tuple(returns)
    if len(values) < 2:
        return Decimal("0")
    avg = mean_return(values)
    variance = mean_return((value - avg) ** 2 for value in values)
    return variance.sqrt() if variance > Decimal("0") else Decimal("0")


__all__ = ["compound_return", "mean_return", "realized_volatility"]
