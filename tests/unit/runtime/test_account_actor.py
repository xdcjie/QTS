from __future__ import annotations

from decimal import Decimal


def test_account_actor_owns_portfolio_state_and_applies_fill_once() -> None:
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.execution.order_manager import OrderFill, OrderSide
    from qts.runtime.actors.account_actor import AccountActor, ApplyFill

    account_id = AccountId("acct-a")
    actor = AccountActor(account_id=account_id, initial_cash={"USD": Decimal("10000")})
    fill = OrderFill(
        fill_id="fill-001",
        order_id=OrderId("ord-001"),
        account_id=account_id,
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("100"),
    )

    actor.handle(ApplyFill(fill=fill, currency="USD", multiplier=Decimal("1")))
    actor.handle(ApplyFill(fill=fill, currency="USD", multiplier=Decimal("1")))

    snapshot = actor.snapshot()
    assert snapshot.cash["USD"] == Decimal("9000")
    assert snapshot.positions[fill.instrument_id].quantity == Decimal("10")


def test_account_actor_restore_preserves_positions_cash_and_fill_idempotency() -> None:
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.execution.order_manager import OrderFill, OrderSide
    from qts.runtime.actors.account_actor import AccountActor, ApplyFill

    account_id = AccountId("acct-a")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    actor = AccountActor(account_id=account_id, initial_cash={"USD": Decimal("10000")})
    first_fill = OrderFill(
        fill_id="fill-001",
        order_id=OrderId("ord-001"),
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("100"),
    )
    next_fill = OrderFill(
        fill_id="fill-002",
        order_id=OrderId("ord-002"),
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("5"),
        price=Decimal("100"),
    )

    actor.handle(ApplyFill(fill=first_fill, currency="USD", multiplier=Decimal("1")))
    restored = AccountActor.restore(actor.snapshot())
    restored.handle(ApplyFill(fill=first_fill, currency="USD", multiplier=Decimal("1")))
    restored.handle(ApplyFill(fill=next_fill, currency="USD", multiplier=Decimal("1")))

    snapshot = restored.snapshot()
    assert snapshot.cash["USD"] == Decimal("8500")
    assert snapshot.positions[instrument_id].quantity == Decimal("15")
    assert snapshot.seen_fill_ids == ("fill-001", "fill-002")


def test_fill_for_account_a_never_updates_account_b() -> None:
    import pytest
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.execution.order_manager import OrderFill, OrderSide
    from qts.runtime.actors.account_actor import AccountActor, ApplyFill

    account_b = AccountActor(
        account_id=AccountId("acct-b"),
        initial_cash={"USD": Decimal("10000")},
    )
    fill = OrderFill(
        fill_id="fill-001",
        order_id=OrderId("ord-001"),
        account_id=AccountId("acct-a"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("100"),
    )

    with pytest.raises(ValueError, match="fill account_id"):
        account_b.handle(ApplyFill(fill=fill, currency="USD", multiplier=Decimal("1")))

    snapshot = account_b.snapshot()
    assert snapshot.cash["USD"] == Decimal("10000")
    assert snapshot.positions == {}
