from __future__ import annotations

from decimal import Decimal


def test_strategy_target_order_spec_flows_into_order_intent() -> None:
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.domain.orders import OrderIntent, OrderSide, OrderType, TimeInForce
    from qts.strategy_sdk.target import OrderSpec

    spec = OrderSpec(
        order_type=OrderType.STOP_LIMIT,
        time_in_force=TimeInForce.GTD,
        limit_price=Decimal("101"),
        stop_price=Decimal("100"),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        account_id=AccountId("acct-1"),
        order_spec=spec,
    )

    assert intent.order_spec == spec
    assert intent.order_spec.order_type is OrderType.STOP_LIMIT
