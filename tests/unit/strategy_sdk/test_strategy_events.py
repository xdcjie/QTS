from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.orders import OrderSide, OrderState
from qts.strategy_sdk.events import Fill


def test_timer_event_requires_name_and_aware_time() -> None:
    from qts.strategy_sdk.events import TimerEvent

    TimerEvent(name="market-open", time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC))

    with pytest.raises(ValueError, match="name"):
        TimerEvent(name=" ", time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC))

    with pytest.raises(ValueError, match="time"):
        TimerEvent(name="market-open", time=datetime(2026, 1, 2, 14, 30))


def test_order_update_rejects_negative_fill_quantity() -> None:
    from qts.strategy_sdk.events import OrderUpdate

    with pytest.raises(ValueError, match="filled_quantity"):
        OrderUpdate(
            order_id=OrderId("order-1"),
            state=OrderState.PARTIALLY_FILLED,
            filled_quantity=Decimal("-1"),
        )


def test_fill_event_requires_positive_quantity_and_non_negative_costs() -> None:
    _fill()

    with pytest.raises(ValueError, match="quantity"):
        _fill(quantity=Decimal("0"))

    with pytest.raises(ValueError, match="commission"):
        _fill(commission=Decimal("-1"))

    with pytest.raises(ValueError, match="slippage"):
        _fill(slippage=Decimal("-1"))


def _fill(
    *,
    quantity: Decimal = Decimal("1"),
    commission: Decimal = Decimal("0"),
    slippage: Decimal = Decimal("0"),
) -> Fill:
    return Fill(
        fill_id="fill-1",
        order_id=OrderId("order-1"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=quantity,
        price=Decimal("100"),
        commission=commission,
        slippage=slippage,
        account_id=AccountId("acct-1"),
    )
