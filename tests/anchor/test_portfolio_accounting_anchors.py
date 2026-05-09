from __future__ import annotations

from decimal import Decimal


def test_portfolio_accounting_anchor_formulas() -> None:
    from qts.portfolio.valuation.models import equity_notional, future_pnl, option_premium_value

    assert equity_notional(quantity=Decimal("100"), price=Decimal("50")) == Decimal("5000")
    assert future_pnl(
        contracts=Decimal("1"),
        entry_price=Decimal("2350.10"),
        exit_price=Decimal("2351.20"),
        multiplier=Decimal("100"),
    ) == Decimal("110.00")
    assert option_premium_value(
        contracts=Decimal("1"),
        option_price=Decimal("4.25"),
        multiplier=Decimal("100"),
    ) == Decimal("425.00")


def test_fill_accounting_anchor_uses_contract_multiplier_for_futures_and_options() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.portfolio.accounting.fill_accounting import Fill, FillAccounting, TradeSide
    from qts.portfolio.cash_book import CashBook
    from qts.portfolio.position_book import PositionBook

    future_cash = CashBook({"USD": Decimal("1000000")})
    future_positions = PositionBook()
    future_fill = Fill(
        fill_id=OrderId("fill-future-001"),
        instrument_id=InstrumentId("FUTURE.US.COMEX.GC.202606"),
        side=TradeSide.BUY,
        quantity=Decimal("2"),
        price=Decimal("2350.10"),
        currency="USD",
        multiplier=Decimal("100"),
    )

    FillAccounting.apply(future_fill, cash_book=future_cash, position_book=future_positions)

    assert future_positions.quantity(future_fill.instrument_id) == Decimal("2")
    assert future_cash.balance("USD") == Decimal("529980.00")

    option_cash = CashBook({"USD": Decimal("10000")})
    option_positions = PositionBook()
    option_fill = Fill(
        fill_id=OrderId("fill-option-001"),
        instrument_id=InstrumentId("OPTION.US.OPRA.AAPL.20260619.C.200"),
        side=TradeSide.BUY,
        quantity=Decimal("3"),
        price=Decimal("4.25"),
        currency="USD",
        multiplier=Decimal("100"),
    )

    FillAccounting.apply(option_fill, cash_book=option_cash, position_book=option_positions)

    assert option_positions.quantity(option_fill.instrument_id) == Decimal("3")
    assert option_cash.balance("USD") == Decimal("8725.00")
