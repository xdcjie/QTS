from __future__ import annotations

from decimal import Decimal


def test_holding_book_tracks_long_and_short_quantities_by_instrument_id() -> None:
    from qts.core.ids import InstrumentId
    from qts.portfolio.holdings import HoldingBook

    aapl = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    msft = InstrumentId("EQUITY.US.NASDAQ.MSFT")
    book = HoldingBook()

    book.apply_fill(
        instrument_id=aapl,
        signed_quantity=Decimal("10"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
    )
    book.apply_fill(
        instrument_id=aapl,
        signed_quantity=Decimal("-3"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
    )
    book.apply_fill(
        instrument_id=msft,
        signed_quantity=Decimal("-5"),
        price=Decimal("50"),
        multiplier=Decimal("1"),
    )

    assert book.quantity(aapl) == Decimal("7")
    assert book.quantity(msft) == Decimal("-5")
    assert book.quantity(InstrumentId("EQUITY.US.NASDAQ.GOOG")) == Decimal("0")
    assert book.snapshot()[aapl].quantity == Decimal("7")
