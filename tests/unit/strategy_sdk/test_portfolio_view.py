from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest


def test_portfolio_view_is_read_only_and_supports_position_lookup() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef
    from qts.strategy_sdk.portfolio_view import PortfolioPosition, PortfolioView

    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    position = PortfolioPosition(quantity=Decimal("10"), market_value=Decimal("1000"))
    portfolio = PortfolioView(
        cash=Decimal("5000"),
        equity=Decimal("6000"),
        positions={asset.instrument_id: position},
    )

    assert portfolio.cash == Decimal("5000")
    assert portfolio.position(asset) == position
    assert portfolio.exposure(asset) == Decimal("1000")
    assert portfolio.weight(asset) == Decimal("0.1666666666666666666666666667")
    with pytest.raises(FrozenInstanceError):
        portfolio.cash = Decimal("0")  # type: ignore[misc]
