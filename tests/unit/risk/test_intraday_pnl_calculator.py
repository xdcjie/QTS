"""Gate tests for the session-aware intraday PnL calculator (DR-006)."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding
from qts.risk.intraday_pnl import IntradayPnlCalculator

_INSTRUMENT = InstrumentId("FUTURE.US.COMEX.GC")
_MULT = {_INSTRUMENT: Decimal("100")}


def _holding(quantity: Decimal, average_cost: Decimal, realized_pnl: Decimal) -> Holding:
    return Holding(
        instrument_id=_INSTRUMENT,
        quantity=quantity,
        average_cost=average_cost,
        realized_pnl=realized_pnl,
    )


def test_realized_loss_since_session_open_is_reported() -> None:
    calc = IntradayPnlCalculator()
    # Session opens flat (realized 0). A subsequent closed trade realizes -100 * mult.
    calc.start_session(
        "2026-01-02", {_INSTRUMENT: _holding(Decimal("0"), Decimal("0"), Decimal("0"))}
    )
    holdings = {_INSTRUMENT: _holding(Decimal("0"), Decimal("0"), Decimal("-100"))}
    pnl = calc.compute(session_id="2026-01-02", holdings=holdings, marks={}, multipliers=_MULT)
    assert pnl == Decimal("-100")


def test_unrealized_loss_on_open_position_is_reported() -> None:
    calc = IntradayPnlCalculator()
    calc.start_session("2026-01-02", {})
    # Long 10 @ 2000, mark 1990 -> unrealized = 10*(1990-2000)*100 = -10000.
    holdings = {_INSTRUMENT: _holding(Decimal("10"), Decimal("2000"), Decimal("0"))}
    pnl = calc.compute(
        session_id="2026-01-02",
        holdings=holdings,
        marks={_INSTRUMENT: Decimal("1990")},
        multipliers=_MULT,
    )
    assert pnl == Decimal("-10000")


def test_realized_and_unrealized_combine() -> None:
    calc = IntradayPnlCalculator()
    calc.start_session(
        "2026-01-02", {_INSTRUMENT: _holding(Decimal("0"), Decimal("0"), Decimal("0"))}
    )
    holdings = {_INSTRUMENT: _holding(Decimal("10"), Decimal("2000"), Decimal("-100"))}
    pnl = calc.compute(
        session_id="2026-01-02",
        holdings=holdings,
        marks={_INSTRUMENT: Decimal("1990")},
        multipliers=_MULT,
    )
    assert pnl == Decimal("-10100")


def test_new_session_resets_realized_window() -> None:
    calc = IntradayPnlCalculator()
    # Day 1 opens flat, realizes -100 by close.
    day1_open = {_INSTRUMENT: _holding(Decimal("0"), Decimal("0"), Decimal("0"))}
    calc.start_session("2026-01-02", day1_open)
    day1_holdings = {_INSTRUMENT: _holding(Decimal("0"), Decimal("0"), Decimal("-100"))}
    assert calc.compute(
        session_id="2026-01-02", holdings=day1_holdings, marks={}, multipliers=_MULT
    ) == Decimal("-100")
    # Day 2: cumulative realized is still -100, but the intraday window resets,
    # so day-2 realized starts at zero.
    pnl_day2 = calc.compute(
        session_id="2026-01-03", holdings=day1_holdings, marks={}, multipliers=_MULT
    )
    assert pnl_day2 == Decimal("0")
    assert calc.session_id == "2026-01-03"
