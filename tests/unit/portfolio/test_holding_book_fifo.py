"""FIFO lot-accounting anchor: FIFO realized PnL differs from average-cost."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import CostBasisMethod, HoldingBook, Lot, LotLedger, PositionClosed

_AAPL = InstrumentId("EQUITY.US.NASDAQ.AAPL")
_T0 = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)


def _fifo_book() -> HoldingBook:
    return HoldingBook(cost_basis_method=CostBasisMethod.FIFO)


def _average_book() -> HoldingBook:
    return HoldingBook(cost_basis_method=CostBasisMethod.AVERAGE)


def _buy_two_lots(book: HoldingBook) -> None:
    """Buy 10 @ 100 then 10 @ 110; net long 20, average cost 105."""
    book.apply_fill(
        instrument_id=_AAPL,
        signed_quantity=Decimal("10"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        fill_time=_T0,
    )
    book.apply_fill(
        instrument_id=_AAPL,
        signed_quantity=Decimal("10"),
        price=Decimal("110"),
        multiplier=Decimal("1"),
        fill_time=_T0 + timedelta(minutes=1),
    )


def test_fifo_and_average_partial_sell_realized_pnl_differ() -> None:
    """On identical fills, FIFO realized PnL must differ from average-cost.

    Lots: buy 10 @ 100, buy 10 @ 110, then sell 15 @ 120.
    FIFO consumes the 10 @ 100 lot then 5 of the 10 @ 110 lot:
        10 * (120 - 100) + 5 * (120 - 110) = 200 + 50 = 250.
    Average-cost closes 15 against the 105 average:
        15 * (120 - 105) = 225.
    """
    fifo = _fifo_book()
    average = _average_book()
    _buy_two_lots(fifo)
    _buy_two_lots(average)

    sell_time = _T0 + timedelta(minutes=2)
    fifo_events = fifo.apply_fill(
        instrument_id=_AAPL,
        signed_quantity=Decimal("-15"),
        price=Decimal("120"),
        multiplier=Decimal("1"),
        fill_time=sell_time,
    )
    average_events = average.apply_fill(
        instrument_id=_AAPL,
        signed_quantity=Decimal("-15"),
        price=Decimal("120"),
        multiplier=Decimal("1"),
        fill_time=sell_time,
    )

    fifo_realized = fifo.holding(_AAPL).realized_pnl
    average_realized = average.holding(_AAPL).realized_pnl

    assert fifo_realized == Decimal("250")
    assert average_realized == Decimal("225")
    assert fifo_realized != average_realized

    # Both reduce a still-open position, so neither emits a PositionClosed event.
    assert fifo_events == ()
    assert average_events == ()

    # FIFO leaves the surviving 5 units at the second lot's 110 cost; average
    # carries the blended 105 cost.
    assert fifo.holding(_AAPL).quantity == Decimal("5")
    assert fifo.holding(_AAPL).average_cost == Decimal("110")
    assert average.holding(_AAPL).quantity == Decimal("5")
    assert average.holding(_AAPL).average_cost == Decimal("105")


def test_fifo_default_method_is_average() -> None:
    """A fresh book is average-cost unless FIFO is requested."""
    assert HoldingBook().holding(_AAPL).cost_basis_method is CostBasisMethod.AVERAGE
    assert _fifo_book().holding(_AAPL).cost_basis_method is CostBasisMethod.FIFO


def test_fifo_full_close_emits_position_closed_with_fifo_realized() -> None:
    """Closing the whole position emits one event carrying FIFO realized PnL."""
    book = _fifo_book()
    _buy_two_lots(book)
    close_time = _T0 + timedelta(minutes=3)

    events = book.apply_fill(
        instrument_id=_AAPL,
        signed_quantity=Decimal("-20"),
        price=Decimal("120"),
        multiplier=Decimal("1"),
        fill_time=close_time,
    )

    # FIFO: 10 * (120 - 100) + 10 * (120 - 110) = 200 + 100 = 300.
    assert events == (
        PositionClosed(
            instrument_id=_AAPL,
            closed_quantity=Decimal("20"),
            exit_price=Decimal("120"),
            realized_pnl=Decimal("300"),
            opened_at=_T0,
            closed_at=close_time,
        ),
    )
    assert book.holding(_AAPL).quantity == Decimal("0")
    assert book.holding(_AAPL).realized_pnl == Decimal("300")
    assert book.holding(_AAPL).lots == ()
    assert book.holding(_AAPL).opened_at is None


def test_fifo_flip_consumes_all_lots_then_opens_opposite_side() -> None:
    """A fill larger than the position flips it, realizing on every old lot."""
    book = _fifo_book()
    _buy_two_lots(book)  # long 20
    flip_time = _T0 + timedelta(minutes=4)

    events = book.apply_fill(
        instrument_id=_AAPL,
        signed_quantity=Decimal("-25"),
        price=Decimal("120"),
        multiplier=Decimal("1"),
        fill_time=flip_time,
    )

    # Realized from closing the long 20 (same as full close): 300.
    assert events == (
        PositionClosed(
            instrument_id=_AAPL,
            closed_quantity=Decimal("20"),
            exit_price=Decimal("120"),
            realized_pnl=Decimal("300"),
            opened_at=_T0,
            closed_at=flip_time,
        ),
    )
    holding = book.holding(_AAPL)
    assert holding.quantity == Decimal("-5")
    assert holding.lots == (
        Lot(quantity=Decimal("-5"), price=Decimal("120"), acquired_at=flip_time),
    )
    assert holding.average_cost == Decimal("120")
    assert holding.opened_at == flip_time


def test_fifo_multiplier_scales_realized_pnl() -> None:
    """Realized PnL scales by the contract multiplier."""
    book = _fifo_book()
    book.apply_fill(
        instrument_id=_AAPL,
        signed_quantity=Decimal("2"),
        price=Decimal("100"),
        multiplier=Decimal("50"),
        fill_time=_T0,
    )
    book.apply_fill(
        instrument_id=_AAPL,
        signed_quantity=Decimal("-2"),
        price=Decimal("110"),
        multiplier=Decimal("50"),
        fill_time=_T0 + timedelta(minutes=1),
    )
    # 2 * (110 - 100) * 50 = 1000.
    assert book.holding(_AAPL).realized_pnl == Decimal("1000")


def test_lot_ledger_average_cost_and_quantity_helpers() -> None:
    """LotLedger exposes weighted average cost and signed net quantity."""
    lots = (
        Lot(quantity=Decimal("10"), price=Decimal("100")),
        Lot(quantity=Decimal("10"), price=Decimal("110")),
    )
    assert LotLedger.quantity(lots) == Decimal("20")
    assert LotLedger.average_cost(lots) == Decimal("105")
    assert LotLedger.quantity(()) == Decimal("0")
    assert LotLedger.average_cost(()) == Decimal("0")
