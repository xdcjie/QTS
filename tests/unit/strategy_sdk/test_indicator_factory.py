from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef


def _bar(index: int, *, close: str, volume: str = "10") -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=index)
    close_value = Decimal(close)
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=close_value,
        high=close_value + Decimal("1"),
        low=close_value - Decimal("1"),
        close=close_value,
        volume=Decimal(volume),
        is_complete=True,
    )


def test_indicator_factory_binds_common_technical_indicators_to_asset_bars() -> None:
    from qts.strategy_sdk.indicators import IndicatorFactory

    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    indicators = IndicatorFactory()
    MA_3 = indicators.ema(asset, window=3)
    ATR_3 = indicators.atr(asset, window=3)
    RSI_3 = indicators.rsi(asset, window=3)
    VWAP = indicators.session_vwap(asset)
    VOL_3 = indicators.volume_ratio(asset, window=3)

    for index, close in enumerate(("10", "11", "12", "11")):
        indicators.update_from_bar(_bar(index, close=close, volume=str((index + 1) * 10)))

    assert MA_3.ready is True
    assert MA_3.value == Decimal("11")
    assert ATR_3.ready is True
    assert ATR_3.value is not None
    assert RSI_3.ready is True
    assert RSI_3.value is not None
    assert VWAP.ready is True
    assert VWAP.value is not None
    assert VOL_3.ready is True
    assert VOL_3.value == Decimal("1.333333333333333333333333333")


def test_indicator_factory_updates_only_matching_asset() -> None:
    from qts.strategy_sdk.indicators import IndicatorFactory

    aapl = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    msft = AssetRef(InstrumentId("EQUITY.US.NASDAQ.MSFT"), "MSFT")
    indicators = IndicatorFactory()
    MA_2 = indicators.ema(aapl, window=2)

    indicators.update_from_bar(
        Bar(
            instrument_id=msft.instrument_id,
            start_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            end_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("1"),
            is_complete=True,
        )
    )

    assert MA_2.ready is False
    assert MA_2.value is None
