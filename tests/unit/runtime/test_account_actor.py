from __future__ import annotations

from decimal import Decimal


def test_account_actor_owns_portfolio_state_and_applies_fill_once() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.execution.order_manager import OrderFill, OrderSide
    from qts.runtime.actors.account_actor import AccountActor, ApplyFill

    actor = AccountActor(initial_cash={"USD": Decimal("10000")})
    fill = OrderFill(
        fill_id="fill-001",
        order_id=OrderId("ord-001"),
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
