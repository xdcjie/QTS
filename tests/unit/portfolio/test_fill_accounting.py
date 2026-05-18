from __future__ import annotations

from decimal import Decimal


def test_equity_buy_fill_updates_position_and_cash() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.portfolio.accounting.fill_accounting import AccountingFill, FillAccounting, TradeSide
    from qts.portfolio.cash_book import CashBook
    from qts.portfolio.holdings import HoldingBook

    cash = CashBook({"USD": Decimal("10000")})
    holdings = HoldingBook()
    fill = AccountingFill(
        fill_id=OrderId("fill-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=TradeSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("100"),
        currency="USD",
        multiplier=Decimal("1"),
    )

    FillAccounting.apply(fill, cash_book=cash, holding_book=holdings)

    assert holdings.quantity(fill.instrument_id) == Decimal("10")
    assert cash.balance("USD") == Decimal("9000")


def test_sell_fill_updates_position_and_cash() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.portfolio.accounting.fill_accounting import AccountingFill, FillAccounting, TradeSide
    from qts.portfolio.cash_book import CashBook
    from qts.portfolio.holdings import HoldingBook

    cash = CashBook({"USD": Decimal("1000")})
    holdings = HoldingBook()
    fill = AccountingFill(
        fill_id=OrderId("fill-002"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=TradeSide.SELL,
        quantity=Decimal("3"),
        price=Decimal("50"),
        currency="USD",
        multiplier=Decimal("1"),
    )

    FillAccounting.apply(fill, cash_book=cash, holding_book=holdings)

    assert holdings.quantity(fill.instrument_id) == Decimal("-3")
    assert cash.balance("USD") == Decimal("1150")
