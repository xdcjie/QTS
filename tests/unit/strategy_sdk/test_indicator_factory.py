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


def test_indicator_factory_registers_anchored_core_indicator_group() -> None:
    from qts.indicators.technical import (
        BollingerBandsValue,
        DonchianChannelValue,
        KeltnerChannelValue,
        MACDValue,
        StochasticOscillatorValue,
    )
    from qts.strategy_sdk.indicators import IndicatorFactory

    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    indicators = IndicatorFactory()
    bands = indicators.bollinger_bands(asset, window=3, standard_deviations=Decimal("2"))
    macd = indicators.macd(asset, fast_window=3, slow_window=6, signal_window=3)
    roc = indicators.rate_of_change(asset, window=3)
    adx = indicators.adx(asset, window=3)
    keltner = indicators.keltner_channel(asset, window=3, multiplier=Decimal("2"))
    donchian = indicators.donchian_channel(asset, window=3)
    stochastic = indicators.stochastic(asset, window=3, signal_window=2)
    cci = indicators.cci(asset, window=3)
    williams = indicators.williams_r(asset, window=3)
    standard_deviation = indicators.standard_deviation(asset, window=3)
    historical_volatility = indicators.historical_volatility(
        asset,
        window=3,
        periods_per_year=Decimal("252"),
    )
    obv = indicators.on_balance_volume(asset)
    mfi = indicators.money_flow_index(asset, window=3)
    adl = indicators.accumulation_distribution(asset)
    cmf = indicators.chaikin_money_flow(asset, window=3)

    for index, close in enumerate(("1", "2", "3", "4", "5", "6", "8", "10", "9")):
        indicators.update_from_bar(_bar(index, close=close))

    assert bands.ready is True
    bands_value = bands.value
    assert isinstance(bands_value, BollingerBandsValue)
    assert bands_value.middle == Decimal("9")
    assert bands_value.upper.quantize(Decimal("0.00000001")) == Decimal("10.63299316")
    assert macd.ready is True
    macd_value = macd.value
    assert isinstance(macd_value, MACDValue)
    assert macd_value.histogram.quantize(Decimal("0.00000001")) == Decimal("-0.07926385")
    assert roc.ready is True
    assert roc.value == Decimal("50")
    assert adx.ready is True
    assert adx.value is not None
    keltner_value = keltner.value
    assert isinstance(keltner_value, KeltnerChannelValue)
    donchian_value = donchian.value
    assert isinstance(donchian_value, DonchianChannelValue)
    stochastic_value = stochastic.value
    assert isinstance(stochastic_value, StochasticOscillatorValue)
    assert cci.ready is True
    assert williams.ready is True
    assert standard_deviation.ready is True
    assert historical_volatility.ready is True
    assert obv.ready is True
    assert mfi.ready is True
    assert adl.ready is True
    assert cmf.ready is True


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


def test_indicator_factory_registers_supertrend_indicator() -> None:
    from qts.indicators.technical import SupertrendValue
    from qts.strategy_sdk.indicators import IndicatorFactory

    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    indicators = IndicatorFactory()
    trend = indicators.supertrend(asset, window=3, multiplier=Decimal("2"))

    for index, close in enumerate(("9", "10", "13", "16", "19")):
        base = _bar(index, close=close)
        high = Decimal(close) + Decimal("1")
        low = Decimal(close) - Decimal("1")
        indicators.update_from_bar(
            Bar(
                instrument_id=asset.instrument_id,
                start_time=base.start_time,
                end_time=base.end_time,
                timeframe="1m",
                session_id="2026-01-02",
                open=Decimal(close),
                high=high,
                low=low,
                close=Decimal(close),
                volume=Decimal("10"),
                is_complete=True,
            )
        )

    assert trend.ready is True
    assert isinstance(trend.value, SupertrendValue)
    assert trend.value.direction in {-1, 1}
