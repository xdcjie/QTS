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


def test_account_fill_application_uses_contract_multiplier_for_futures_and_options() -> None:
    # Anchor the contract-multiplier cash invariant on the production fill path
    # (AccountActor), not a parallel helper: cash moves by
    # quantity * price * multiplier and the holding by quantity.
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.domain.orders import OrderFill, OrderSide
    from qts.runtime.actors.account_actor import AccountActor, ApplyFill

    account_id = AccountId("acct-accounting-anchor")

    future_actor = AccountActor(account_id=account_id, initial_cash={"USD": Decimal("1000000")})
    future_fill = OrderFill(
        fill_id="fill-future-001",
        order_id=OrderId("ord-future-001"),
        account_id=account_id,
        instrument_id=InstrumentId("FUTURE.US.COMEX.GC.202606"),
        side=OrderSide.BUY,
        quantity=Decimal("2"),
        price=Decimal("2350.10"),
    )
    future_actor.handle(ApplyFill(fill=future_fill, currency="USD", multiplier=Decimal("100")))
    future_snapshot = future_actor.snapshot()
    assert future_snapshot.positions[future_fill.instrument_id].quantity == Decimal("2")
    assert future_snapshot.cash["USD"] == Decimal("529980.00")

    option_actor = AccountActor(account_id=account_id, initial_cash={"USD": Decimal("10000")})
    option_fill = OrderFill(
        fill_id="fill-option-001",
        order_id=OrderId("ord-option-001"),
        account_id=account_id,
        instrument_id=InstrumentId("OPTION.US.OPRA.AAPL.20260619.C.200"),
        side=OrderSide.BUY,
        quantity=Decimal("3"),
        price=Decimal("4.25"),
    )
    option_actor.handle(ApplyFill(fill=option_fill, currency="USD", multiplier=Decimal("100")))
    option_snapshot = option_actor.snapshot()
    assert option_snapshot.positions[option_fill.instrument_id].quantity == Decimal("3")
    assert option_snapshot.cash["USD"] == Decimal("8725.00")
