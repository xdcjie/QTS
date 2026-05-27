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


def test_gc_and_si_futures_pnl_use_contract_multipliers() -> None:
    from qts.portfolio.valuation.models import future_pnl

    assert future_pnl(
        contracts=Decimal("1"),
        entry_price=Decimal("2000.0"),
        exit_price=Decimal("2001.0"),
        multiplier=Decimal("100"),
    ) == Decimal("100.0")
    assert future_pnl(
        contracts=Decimal("1"),
        entry_price=Decimal("25.000"),
        exit_price=Decimal("25.005"),
        multiplier=Decimal("5000"),
    ) == Decimal("25.000")


def test_fill_accounting_anchor_uses_contract_multiplier_for_futures_and_options() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.orders import OrderSide
    from qts.portfolio.accounting.fill_accounting import AccountingFill, FillAccounting
    from qts.portfolio.cash_book import CashBook
    from qts.portfolio.holdings import HoldingBook

    future_cash = CashBook({"USD": Decimal("1000000")})
    future_holdings = HoldingBook()
    future_fill = AccountingFill(
        fill_id=OrderId("fill-future-001"),
        instrument_id=InstrumentId("FUTURE.US.COMEX.GC.202606"),
        side=OrderSide.BUY,
        quantity=Decimal("2"),
        price=Decimal("2350.10"),
        currency="USD",
        multiplier=Decimal("100"),
    )

    FillAccounting.apply(future_fill, cash_book=future_cash, holding_book=future_holdings)

    assert future_holdings.quantity(future_fill.instrument_id) == Decimal("2")
    assert future_cash.balance("USD") == Decimal("529980.00")

    option_cash = CashBook({"USD": Decimal("10000")})
    option_holdings = HoldingBook()
    option_fill = AccountingFill(
        fill_id=OrderId("fill-option-001"),
        instrument_id=InstrumentId("OPTION.US.OPRA.AAPL.20260619.C.200"),
        side=OrderSide.BUY,
        quantity=Decimal("3"),
        price=Decimal("4.25"),
        currency="USD",
        multiplier=Decimal("100"),
    )

    FillAccounting.apply(option_fill, cash_book=option_cash, holding_book=option_holdings)

    assert option_holdings.quantity(option_fill.instrument_id) == Decimal("3")
    assert option_cash.balance("USD") == Decimal("8725.00")
