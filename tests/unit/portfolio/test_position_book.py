from __future__ import annotations

from decimal import Decimal


def test_position_book_tracks_long_and_short_positions_by_instrument_id() -> None:
    from qts.core.ids import InstrumentId
    from qts.portfolio.position_book import PositionBook

    aapl = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    msft = InstrumentId("EQUITY.US.NASDAQ.MSFT")
    book = PositionBook()

    book.apply_delta(aapl, Decimal("10"))
    book.apply_delta(aapl, Decimal("-3"))
    book.apply_delta(msft, Decimal("-5"))

    assert book.quantity(aapl) == Decimal("7")
    assert book.quantity(msft) == Decimal("-5")
    assert book.quantity(InstrumentId("EQUITY.US.NASDAQ.GOOG")) == Decimal("0")
    assert book.snapshot()[aapl].quantity == Decimal("7")
