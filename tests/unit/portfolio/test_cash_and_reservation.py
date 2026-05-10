from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path


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


def test_cash_and_reservation_books_keep_currency_normalization_inside_the_books() -> None:
    cash_tree = ast.parse(
        Path("backend/src/qts/portfolio/cash_book.py").read_text(encoding="utf-8")
    )
    reservation_tree = ast.parse(
        Path("backend/src/qts/portfolio/reservation_book.py").read_text(encoding="utf-8")
    )

    cash_private_functions = {
        node.name
        for node in cash_tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }
    reservation_private_functions = {
        node.name
        for node in reservation_tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_normalize_currency" not in cash_private_functions
    assert "_normalize_currency" not in reservation_private_functions
