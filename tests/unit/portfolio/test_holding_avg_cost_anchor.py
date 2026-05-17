from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal


def test_holding_book_tracks_average_cost_realized_pnl_and_close_event() -> None:
    from qts.core.ids import InstrumentId
    from qts.portfolio.holdings import HoldingBook, PositionClosed

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    book = HoldingBook()
    opened = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    closed = datetime(2026, 1, 2, 14, 33, tzinfo=UTC)

    assert (
        book.apply_fill(
            instrument_id=instrument_id,
            signed_quantity=Decimal("10"),
            price=Decimal("100"),
            multiplier=Decimal("1"),
            fill_time=opened,
        )
        == ()
    )
    assert (
        book.apply_fill(
            instrument_id=instrument_id,
            signed_quantity=Decimal("10"),
            price=Decimal("110"),
            multiplier=Decimal("1"),
            fill_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        )
        == ()
    )

    holding = book.holding(instrument_id)
    assert holding.quantity == Decimal("20")
    assert holding.average_cost == Decimal("105")

    assert (
        book.apply_fill(
            instrument_id=instrument_id,
            signed_quantity=Decimal("-5"),
            price=Decimal("120"),
            multiplier=Decimal("1"),
            fill_time=datetime(2026, 1, 2, 14, 32, tzinfo=UTC),
        )
        == ()
    )
    holding = book.holding(instrument_id)
    assert holding.quantity == Decimal("15")
    assert holding.average_cost == Decimal("105")
    assert holding.realized_pnl == Decimal("75")

    events = book.apply_fill(
        instrument_id=instrument_id,
        signed_quantity=Decimal("-15"),
        price=Decimal("90"),
        multiplier=Decimal("1"),
        fill_time=closed,
    )

    assert events == (
        PositionClosed(
            instrument_id=instrument_id,
            closed_quantity=Decimal("15"),
            exit_price=Decimal("90"),
            realized_pnl=Decimal("-225"),
            opened_at=opened,
            closed_at=closed,
        ),
    )
    assert book.holding(instrument_id).quantity == Decimal("0")
    assert book.holding(instrument_id).realized_pnl == Decimal("-150")
