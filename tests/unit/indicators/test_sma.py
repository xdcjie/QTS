from __future__ import annotations

from decimal import Decimal


def test_sma_warms_up_and_updates_incrementally() -> None:
    from qts.indicators.price.sma import SMA

    sma = SMA(window=3)

    assert not sma.ready
    assert sma.update(Decimal("1")) is None
    assert sma.update(Decimal("2")) is None
    assert sma.update(Decimal("3")) == Decimal("2")
    assert sma.ready
    assert sma.value == Decimal("2")
    assert sma.update(Decimal("6")) == Decimal("3.666666666666666666666666667")


def test_indicator_factory_creates_sma_for_user_assets() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef
    from qts.strategy_sdk.indicators import IndicatorFactory

    factory = IndicatorFactory()
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")

    indicator = factory.sma(asset, window=2)

    assert indicator.asset == asset
    assert indicator.update(Decimal("10")) is None
    assert indicator.update(Decimal("20")) == Decimal("15")
