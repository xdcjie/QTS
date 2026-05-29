"""Tests for PortfolioValuator and AccountValuation."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding
from qts.portfolio.valuation.valuator import PortfolioValuator


def test_equity_equals_cash_plus_marked_holdings() -> None:
    instr = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    result = PortfolioValuator.valuate(
        cash={"USD": Decimal("100000")},
        holdings={
            instr: Holding(
                instrument_id=instr,
                quantity=Decimal("100"),
                average_cost=Decimal("50"),
                realized_pnl=Decimal("0"),
            ),
        },
        marks={instr: Decimal("150")},
        multipliers={instr: Decimal("1")},
    )
    assert result.account_equity == Decimal("115000")
    assert result.current_exposure == Decimal("15000")


def test_exposure_is_sum_of_abs_market_values() -> None:
    instr_a = InstrumentId("FUTURE.CME.GC.GCG6")
    instr_b = InstrumentId("FUTURE.CME.SI.SIH6")
    result = PortfolioValuator.valuate(
        cash={"USD": Decimal("50000")},
        holdings={
            instr_a: Holding(instr_a, Decimal("10"), Decimal("2000"), Decimal("0")),
            instr_b: Holding(instr_b, Decimal("-5"), Decimal("25"), Decimal("0")),
        },
        marks={instr_a: Decimal("2000"), instr_b: Decimal("25")},
        multipliers={instr_a: Decimal("100"), instr_b: Decimal("5000")},
    )
    # A: 10 * 2000 * 100 = 2,000,000
    # B: -5 * 25 * 5000 = -625,000
    # exposure = |2,000,000| + |-625,000| = 2,625,000
    assert result.current_exposure == Decimal("2625000")


def test_notional_by_instrument_is_absolute() -> None:
    instr = InstrumentId("FUTURE.CME.GC.GCG6")
    result = PortfolioValuator.valuate(
        cash={"USD": Decimal("100000")},
        holdings={instr: Holding(instr, Decimal("-3"), Decimal("2000"), Decimal("0"))},
        marks={instr: Decimal("2000")},
        multipliers={instr: Decimal("100")},
    )
    assert result.current_notional_by_instrument[instr] == Decimal("600000")


def test_position_by_instrument_preserves_sign() -> None:
    instr = InstrumentId("FUTURE.CME.GC.GCG6")
    result = PortfolioValuator.valuate(
        cash={"USD": Decimal("100000")},
        holdings={instr: Holding(instr, Decimal("-3"), Decimal("2000"), Decimal("0"))},
        marks={instr: Decimal("2000")},
        multipliers={instr: Decimal("100")},
    )
    assert result.current_position_by_instrument[instr] == Decimal("-3")


def test_missing_mark_defaults_to_zero_market_value() -> None:
    instr = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    result = PortfolioValuator.valuate(
        cash={"USD": Decimal("50000")},
        holdings={instr: Holding(instr, Decimal("100"), Decimal("50"), Decimal("0"))},
        marks={},
        multipliers={instr: Decimal("1")},
    )
    # No mark price → market_value = 0 → equity = 50000
    assert result.account_equity == Decimal("50000")
    assert result.current_notional_by_instrument[instr] == Decimal("0")


def test_flat_holding_contributes_zero() -> None:
    instr = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    result = PortfolioValuator.valuate(
        cash={"USD": Decimal("75000")},
        holdings={instr: Holding(instr, Decimal("0"), Decimal("0"), Decimal("0"))},
        marks={instr: Decimal("100")},
        multipliers={instr: Decimal("1")},
    )
    assert result.account_equity == Decimal("75000")
    assert result.current_notional_by_instrument[instr] == Decimal("0")
