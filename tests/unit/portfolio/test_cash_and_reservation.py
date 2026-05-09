from __future__ import annotations

from decimal import Decimal


def test_cash_book_tracks_balances_and_available_cash_after_reservations() -> None:
    from qts.core.ids import OrderId
    from qts.portfolio.cash_book import CashBook
    from qts.portfolio.reservation_book import ReservationBook

    cash = CashBook()
    reservations = ReservationBook()

    cash.apply_delta("USD", Decimal("1000"))
    reservations.reserve(OrderId("ord-001"), "USD", Decimal("250"))
    reservations.reserve(OrderId("ord-001"), "USD", Decimal("250"))

    assert cash.balance("USD") == Decimal("1000")
    assert reservations.reserved("USD") == Decimal("250")
    assert cash.available("USD", reservations=reservations) == Decimal("750")

    reservations.release(OrderId("ord-001"))
    assert cash.available("USD", reservations=reservations) == Decimal("1000")


def test_releasing_unknown_reservation_is_explicit_noop() -> None:
    from qts.core.ids import OrderId
    from qts.portfolio.reservation_book import ReservationBook

    reservations = ReservationBook()

    reservations.release(OrderId("missing"))

    assert reservations.reserved("USD") == Decimal("0")
