"""Tests for RiskStateSnapshot construction and behavior."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding
from qts.risk.risk_state import RiskStateSnapshot
from qts.runtime.actors.account_actor import AccountSnapshot


def test_from_account_builds_correct_snapshot() -> None:
    instr = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    snapshot = AccountSnapshot(
        cash={"USD": Decimal("100000")},
        holdings={
            instr: Holding(instr, Decimal("100"), Decimal("50"), Decimal("0")),
        },
    )
    risk_state = RiskStateSnapshot.from_account(
        snapshot,
        marks={instr: Decimal("150")},
        multipliers={instr: Decimal("1")},
        intraday_pnl=Decimal("200"),
    )
    assert risk_state.account_equity == Decimal("115000")
    assert risk_state.current_exposure == Decimal("15000")
    assert risk_state.intraday_pnl == Decimal("200")
    assert risk_state.current_notional_by_instrument[instr] == Decimal("15000")
    assert risk_state.current_position_by_instrument[instr] == Decimal("100")


def test_current_position_returns_zero_for_unknown_instrument() -> None:
    instr = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    snapshot = AccountSnapshot(cash={"USD": Decimal("100000")}, holdings={})
    risk_state = RiskStateSnapshot.from_account(
        snapshot,
        marks={instr: Decimal("150")},
        multipliers={instr: Decimal("1")},
    )
    unknown = InstrumentId("EQUITY.US.NASDAQ.MSFT")
    assert risk_state.current_position(unknown) == Decimal("0")


def test_from_account_with_no_holdings() -> None:
    snapshot = AccountSnapshot(cash={"USD": Decimal("50000")}, holdings={})
    risk_state = RiskStateSnapshot.from_account(snapshot, marks={}, multipliers={})
    assert risk_state.account_equity == Decimal("50000")
    assert risk_state.current_exposure == Decimal("0")


def test_margin_fields_default_to_zero() -> None:
    snapshot = AccountSnapshot(cash={"USD": Decimal("50000")}, holdings={})
    risk_state = RiskStateSnapshot.from_account(snapshot, marks={}, multipliers={})
    assert risk_state.current_margin_requirement == Decimal("0")
    assert risk_state.available_margin == Decimal("0")


def test_risk_state_snapshot_is_frozen() -> None:
    snapshot = AccountSnapshot(cash={"USD": Decimal("50000")}, holdings={})
    risk_state = RiskStateSnapshot.from_account(snapshot, marks={}, multipliers={})
    import pytest

    with pytest.raises(AttributeError):
        risk_state.account_equity = Decimal("0")  # type: ignore[misc]
