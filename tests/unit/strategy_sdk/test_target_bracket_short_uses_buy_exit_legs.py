"""QTS-FINAL-014: bracket exit legs follow the parent direction.

A long parent (positive quantity) is exited by selling; a short parent (negative
quantity) is exited by buying. The SDK must not hardcode ``sell`` exit legs.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.domain.orders import OrderSide
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.context import StrategyContext


def _asset(symbol: str = "AAPL") -> AssetRef:
    return AssetRef(InstrumentId(f"EQUITY.US.NASDAQ.{symbol}"), symbol)


def test_long_bracket_uses_sell_exit_legs() -> None:
    ctx = StrategyContext()
    intent = ctx.target_bracket(
        _asset(),
        take_profit_price=Decimal("110"),
        stop_loss_price=Decimal("90"),
        quantity=Decimal("5"),
    )
    bracket = intent.order_spec.bracket
    assert bracket is not None
    legs = bracket.legs
    assert {leg.side for leg in legs} == {OrderSide.SELL}
    assert all(leg.quantity == Decimal("5") for leg in legs)


def test_short_bracket_uses_buy_exit_legs() -> None:
    ctx = StrategyContext()
    intent = ctx.target_bracket(
        _asset(),
        take_profit_price=Decimal("90"),
        stop_loss_price=Decimal("110"),
        quantity=Decimal("-5"),
    )
    bracket = intent.order_spec.bracket
    assert bracket is not None
    legs = bracket.legs
    # Short exits are buys, and the legs carry the absolute quantity.
    assert {leg.side for leg in legs} == {OrderSide.BUY}
    assert all(leg.quantity == Decimal("5") for leg in legs)


def test_zero_quantity_bracket_is_rejected() -> None:
    ctx = StrategyContext()
    with pytest.raises(ValueError, match="non-zero"):
        ctx.target_bracket(
            _asset(),
            take_profit_price=Decimal("110"),
            stop_loss_price=Decimal("90"),
            quantity=Decimal("0"),
        )
