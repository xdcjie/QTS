"""Unit tests for the stateful MarginLedger."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding
from qts.portfolio.margin_ledger import MarginLedger, MarginState
from qts.risk.margin.calculator import MarginCalculator

_ES = InstrumentId("FUT.US.CME.ES")


def _holding(quantity: Decimal) -> Holding:
    return Holding(
        instrument_id=_ES,
        quantity=quantity,
        average_cost=Decimal("50"),
        realized_pnl=Decimal("0"),
    )


def test_initial_and_maintenance_from_positions() -> None:
    """Initial/maintenance margin derive from rate-based notional."""
    ledger = MarginLedger(account_equity=Decimal("100000"))
    state = ledger.update(
        positions={_ES: _holding(Decimal("2"))},
        marks={_ES: Decimal("50")},
        multipliers={_ES: Decimal("50")},
    )
    # notional = 2 * 50 * 50 = 5000; initial = 250, maintenance = 200.
    assert state.initial_margin == Decimal("250")
    assert state.maintenance_margin == Decimal("200")
    # First mark seeds the variation reference and accrues nothing.
    assert state.variation_margin == Decimal("0")


def test_variation_margin_accrues_as_mark_moves() -> None:
    """Variation margin accumulates mark-to-market settlements across updates."""
    ledger = MarginLedger(account_equity=Decimal("100000"))
    ledger.update(
        positions={_ES: _holding(Decimal("2"))},
        marks={_ES: Decimal("50")},
        multipliers={_ES: Decimal("50")},
    )

    up = ledger.update(
        positions={_ES: _holding(Decimal("2"))},
        marks={_ES: Decimal("60")},
        multipliers={_ES: Decimal("50")},
    )
    # Mark 50 -> 60: 2 * (60 - 50) * 50 = +1000.
    assert up.variation_margin == Decimal("1000")
    # notional = 2 * 60 * 50 = 6000; initial = 300, maintenance = 240.
    assert up.initial_margin == Decimal("300")
    assert up.maintenance_margin == Decimal("240")

    down = ledger.update(
        positions={_ES: _holding(Decimal("2"))},
        marks={_ES: Decimal("55")},
        multipliers={_ES: Decimal("50")},
    )
    # Mark 60 -> 55: 2 * (55 - 60) * 50 = -500; cumulative 1000 - 500 = 500.
    assert down.variation_margin == Decimal("500")
    assert down.initial_margin == Decimal("275")
    assert down.maintenance_margin == Decimal("220")


def test_short_position_variation_margin_sign() -> None:
    """A short position loses variation margin when the mark rises."""
    ledger = MarginLedger(account_equity=Decimal("100000"))
    ledger.update(
        positions={_ES: _holding(Decimal("-3"))},
        marks={_ES: Decimal("100")},
        multipliers={_ES: Decimal("50")},
    )
    state = ledger.update(
        positions={_ES: _holding(Decimal("-3"))},
        marks={_ES: Decimal("110")},
        multipliers={_ES: Decimal("50")},
    )
    # Short 3, mark 100 -> 110: -3 * (110 - 100) * 50 = -1500.
    assert state.variation_margin == Decimal("-1500")


def test_unchanged_mark_accrues_no_variation_margin() -> None:
    """Repeating the same mark settles nothing further."""
    ledger = MarginLedger()
    ledger.update(
        positions={_ES: _holding(Decimal("1"))},
        marks={_ES: Decimal("50")},
        multipliers={_ES: Decimal("50")},
    )
    state = ledger.update(
        positions={_ES: _holding(Decimal("1"))},
        marks={_ES: Decimal("50")},
        multipliers={_ES: Decimal("50")},
    )
    assert state.variation_margin == Decimal("0")


def test_state_returns_current_snapshot() -> None:
    """state() returns the same values as the last update()."""
    ledger = MarginLedger(account_equity=Decimal("100000"))
    returned = ledger.update(
        positions={_ES: _holding(Decimal("2"))},
        marks={_ES: Decimal("60")},
        multipliers={_ES: Decimal("50")},
    )
    assert ledger.state() == returned
    assert isinstance(returned, MarginState)


def test_custom_calculator_rates_flow_through() -> None:
    """An injected MarginCalculator drives the initial/maintenance rates."""
    ledger = MarginLedger(
        calculator=MarginCalculator(
            initial_margin_rate=Decimal("0.10"),
            maintenance_margin_rate=Decimal("0.07"),
        ),
        account_equity=Decimal("100000"),
    )
    state = ledger.update(
        positions={_ES: _holding(Decimal("1"))},
        marks={_ES: Decimal("100")},
        multipliers={_ES: Decimal("100")},
    )
    # notional = 1 * 100 * 100 = 10000; initial = 1000, maintenance = 700.
    assert state.initial_margin == Decimal("1000")
    assert state.maintenance_margin == Decimal("700")


def test_variation_margin_property_matches_state() -> None:
    ledger = MarginLedger()
    ledger.update(
        positions={_ES: _holding(Decimal("1"))},
        marks={_ES: Decimal("50")},
        multipliers={_ES: Decimal("50")},
    )
    ledger.update(
        positions={_ES: _holding(Decimal("1"))},
        marks={_ES: Decimal("55")},
        multipliers={_ES: Decimal("50")},
    )
    assert ledger.variation_margin == ledger.state().variation_margin == Decimal("250")
