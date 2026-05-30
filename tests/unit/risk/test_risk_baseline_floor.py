"""Mandatory baseline risk floor: order-submitting runtimes never run naked.

Invariant (CLAUDE.md §5 risk safety + backtest/live parity): backtest, paper, and
live share one capital-scaled max-notional floor, owned by ``RiskEngine``. An
empty ``RiskEngine`` approves every order; the baseline floor closes that, and a
single owner guarantees the floor a promoted strategy clears in backtest is the
floor its paper/live runtime enforces.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.backtest.dependencies import BacktestEngineDependencies
from qts.core.ids import InstrumentId
from qts.domain.risk import OrderRiskRequest
from qts.risk.risk_engine import RiskEngine

_INSTRUMENT = InstrumentId("FUTURE.US.COMEX.GC")


def _order_with_notional(notional: Decimal) -> OrderRiskRequest:
    """Build a request whose notional equals ``notional`` (price=multiplier=1)."""
    return OrderRiskRequest(
        instrument_id=_INSTRUMENT,
        quantity=notional,
        price=Decimal("1"),
        multiplier=Decimal("1"),
    )


def test_baseline_floor_rejects_orders_above_capital_scaled_ceiling() -> None:
    engine = RiskEngine.with_baseline_floor(Decimal("1000"))  # ceiling = 100x = 100_000

    assert engine.check(_order_with_notional(Decimal("100001"))).approved is False
    assert engine.check(_order_with_notional(Decimal("99999"))).approved is True


def test_baseline_floor_requires_positive_capital() -> None:
    # A zero/negative-capital order-submitting runtime cannot derive a floor; fail
    # closed rather than silently fall back to an all-orders-approved engine.
    with pytest.raises(ValueError):
        RiskEngine.with_baseline_floor(Decimal("0"))


def test_backtest_default_and_baseline_floor_are_identical_for_equal_capital() -> None:
    # Parity: the backtest default risk engine and the shared baseline floor reject
    # and approve the same boundary order for the same capital.
    capital = Decimal("1000")
    backtest_engine = BacktestEngineDependencies.with_defaults(initial_cash=capital).risk_engine
    baseline_engine = RiskEngine.with_baseline_floor(capital)

    for notional in (Decimal("100001"), Decimal("99999")):
        order = _order_with_notional(notional)
        assert backtest_engine.check(order).approved == baseline_engine.check(order).approved
