from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


def _bar(
    index: int,
    *,
    open_: str | None = None,
    high: str = "10",
    low: str = "10",
    close: str = "10",
    volume: str = "1",
    session_id: str = "2026-01-02",
) -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=index)
    open_value = Decimal(open_ if open_ is not None else close)
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id=session_id,
        open=open_value,
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        is_complete=True,
    )


def test_average_true_range_uses_wilder_smoothing_after_warmup() -> None:
    from qts.indicators.technical import AverageTrueRange

    atr = AverageTrueRange(window=3)

    assert atr.update_bar(_bar(0, high="10", low="8", close="9")) is None
    assert atr.update_bar(_bar(1, high="11", low="9", close="10")) is None
    assert atr.update_bar(_bar(2, high="14", low="9", close="13")) == Decimal("3")
    assert atr.ready is True
    assert atr.update_bar(_bar(3, high="15", low="12", close="14")) == Decimal("3")
    assert atr.value == Decimal("3")


def test_rsi_uses_wilder_average_and_reports_ready_after_period_changes() -> None:
    from qts.indicators.technical import RSI

    rsi = RSI(window=3)

    assert rsi.update(Decimal("1")) is None
    assert rsi.update(Decimal("2")) is None
    assert rsi.update(Decimal("3")) is None
    value = rsi.update(Decimal("2"))

    assert rsi.ready is True
    assert value is not None
    assert value.quantize(Decimal("0.0001")) == Decimal("66.6667")


def test_session_vwap_resets_when_session_id_changes() -> None:
    from qts.indicators.technical import SessionVWAP

    vwap = SessionVWAP()

    assert vwap.update_bar(_bar(0, high="10", low="8", close="9", volume="2")) == Decimal("9")
    assert vwap.update_bar(_bar(1, high="12", low="10", close="11", volume="1")) == (
        Decimal("29") / Decimal("3")
    )
    assert vwap.update_bar(
        _bar(2, high="20", low="16", close="18", volume="4", session_id="2026-01-03")
    ) == Decimal("18")


def test_volume_ratio_compares_current_volume_with_rolling_average() -> None:
    from qts.indicators.technical import VolumeRatio

    ratio = VolumeRatio(window=3)

    assert ratio.update(Decimal("10")) is None
    assert ratio.update(Decimal("20")) is None
    assert ratio.update(Decimal("30")) == Decimal("1.5")
    value = ratio.update(Decimal("40"))
    assert value is not None
    assert value.quantize(Decimal("0.0001")) == Decimal("1.3333")


def test_bollinger_bands_use_population_standard_deviation_anchor() -> None:
    from qts.indicators.technical import BollingerBands

    bands = BollingerBands(window=3, standard_deviations=Decimal("2"))

    assert bands.update(Decimal("1")) is None
    assert bands.update(Decimal("2")) is None
    value = bands.update(Decimal("3"))

    assert bands.ready is True
    assert value is not None
    assert value.middle == Decimal("2")
    assert value.standard_deviation.quantize(Decimal("0.00000001")) == Decimal("0.81649658")
    assert value.upper.quantize(Decimal("0.00000001")) == Decimal("3.63299316")
    assert value.lower.quantize(Decimal("0.00000001")) == Decimal("0.36700684")


def test_macd_uses_sma_seeded_emas_and_signal_anchor() -> None:
    from qts.indicators.technical import MACD

    macd = MACD(fast_window=3, slow_window=6, signal_window=3)

    values = [
        macd.update(Decimal(price)) for price in ("1", "2", "3", "4", "5", "6", "8", "10", "9")
    ]

    assert values[:7] == [None, None, None, None, None, None, None]
    value = values[-1]
    assert macd.ready is True
    assert value is not None
    assert value.macd.quantize(Decimal("0.00000001")) == Decimal("1.57106414")
    assert value.signal.quantize(Decimal("0.00000001")) == Decimal("1.65032799")
    assert value.histogram.quantize(Decimal("0.00000001")) == Decimal("-0.07926385")


def test_rate_of_change_compares_with_price_n_periods_ago_anchor() -> None:
    from qts.indicators.technical import RateOfChange

    roc = RateOfChange(window=3)

    assert roc.update(Decimal("10")) is None
    assert roc.update(Decimal("12")) is None
    assert roc.update(Decimal("15")) is None
    value = roc.update(Decimal("18"))

    assert roc.ready is True
    assert value == Decimal("80")


def test_adx_uses_wilder_directional_movement_anchor() -> None:
    from qts.indicators.technical import ADX

    adx = ADX(window=3)

    assert adx.update_bar(_bar(0, high="10", low="8", close="9")) is None
    assert adx.update_bar(_bar(1, high="12", low="9", close="11")) is None
    first = adx.update_bar(_bar(2, high="11", low="7", close="8"))
    second = adx.update_bar(_bar(3, high="13", low="8", close="12"))

    assert first is not None
    assert first.plus_di.quantize(Decimal("0.0001")) == Decimal("22.2222")
    assert first.minus_di.quantize(Decimal("0.0001")) == Decimal("22.2222")
    assert first.adx == Decimal("0")
    assert second is not None
    assert second.plus_di.quantize(Decimal("0.0001")) == Decimal("30.3030")
    assert second.minus_di.quantize(Decimal("0.0001")) == Decimal("12.1212")
    assert second.dx.quantize(Decimal("0.0001")) == Decimal("42.8571")
    assert second.adx.quantize(Decimal("0.0001")) == Decimal("14.2857")


def test_keltner_channel_uses_ema_middle_and_atr_width_anchor() -> None:
    from qts.indicators.technical import KeltnerChannel

    channel = KeltnerChannel(window=3, multiplier=Decimal("2"))

    assert channel.update_bar(_bar(0, high="11", low="9", close="10")) is None
    assert channel.update_bar(_bar(1, high="12", low="10", close="11")) is None
    value = channel.update_bar(_bar(2, high="13", low="11", close="12"))

    assert value is not None
    assert value.middle == Decimal("11")
    assert value.upper == Decimal("15")
    assert value.lower == Decimal("7")


def test_donchian_channel_uses_rolling_high_low_anchor() -> None:
    from qts.indicators.technical import DonchianChannel

    channel = DonchianChannel(window=3)

    assert channel.update_bar(_bar(0, high="11", low="9", close="10")) is None
    assert channel.update_bar(_bar(1, high="12", low="8", close="11")) is None
    value = channel.update_bar(_bar(2, high="10", low="7", close="9"))

    assert value is not None
    assert value.upper == Decimal("12")
    assert value.lower == Decimal("7")
    assert value.middle == Decimal("9.5")


def test_stochastic_oscillator_anchors_percent_k_and_percent_d() -> None:
    from qts.indicators.technical import StochasticOscillator

    stochastic = StochasticOscillator(window=3, signal_window=2)

    assert stochastic.update_bar(_bar(0, high="10", low="8", close="9")) is None
    assert stochastic.update_bar(_bar(1, high="12", low="9", close="11")) is None
    assert stochastic.update_bar(_bar(2, high="14", low="10", close="13")) is None
    value = stochastic.update_bar(_bar(3, high="15", low="11", close="12"))

    assert value is not None
    assert value.percent_k.quantize(Decimal("0.0001")) == Decimal("50.0000")
    assert value.percent_d.quantize(Decimal("0.0001")) == Decimal("66.6667")


def test_cci_uses_typical_price_mean_deviation_anchor() -> None:
    from qts.indicators.technical import CommodityChannelIndex

    cci = CommodityChannelIndex(window=3)

    assert cci.update_bar(_bar(0, high="10", low="10", close="10")) is None
    assert cci.update_bar(_bar(1, high="11", low="11", close="11")) is None
    value = cci.update_bar(_bar(2, high="13", low="13", close="13"))

    assert value is not None
    assert value.quantize(Decimal("0.0001")) == Decimal("100.0000")


def test_williams_r_uses_rolling_extremes_anchor() -> None:
    from qts.indicators.technical import WilliamsR

    williams = WilliamsR(window=3)

    assert williams.update_bar(_bar(0, high="10", low="8", close="9")) is None
    assert williams.update_bar(_bar(1, high="12", low="9", close="11")) is None
    value = williams.update_bar(_bar(2, high="14", low="10", close="13"))

    assert value is not None
    assert value.quantize(Decimal("0.0001")) == Decimal("-16.6667")


def test_standard_deviation_uses_population_window_anchor() -> None:
    from qts.indicators.technical import StandardDeviation

    deviation = StandardDeviation(window=3)

    assert deviation.update(Decimal("1")) is None
    assert deviation.update(Decimal("2")) is None
    value = deviation.update(Decimal("3"))

    assert value is not None
    assert value.quantize(Decimal("0.00000001")) == Decimal("0.81649658")


def test_historical_volatility_annualizes_rolling_simple_returns_anchor() -> None:
    from qts.indicators.technical import HistoricalVolatility

    volatility = HistoricalVolatility(window=3, periods_per_year=Decimal("252"))

    assert volatility.update(Decimal("100")) is None
    assert volatility.update(Decimal("110")) is None
    assert volatility.update(Decimal("99")) is None
    value = volatility.update(Decimal("108.9"))

    assert value is not None
    assert value.quantize(Decimal("0.00000001")) == Decimal("1.49666295")


def test_on_balance_volume_accumulates_directional_volume_anchor() -> None:
    from qts.indicators.technical import OnBalanceVolume

    obv = OnBalanceVolume()

    assert obv.update(close=Decimal("10"), volume=Decimal("100")) == Decimal("0")
    assert obv.update(close=Decimal("11"), volume=Decimal("20")) == Decimal("20")
    assert obv.update(close=Decimal("10.5"), volume=Decimal("5")) == Decimal("15")
    assert obv.update(close=Decimal("10.5"), volume=Decimal("7")) == Decimal("15")


def test_money_flow_index_uses_positive_and_negative_money_flow_anchor() -> None:
    from qts.indicators.technical import MoneyFlowIndex

    mfi = MoneyFlowIndex(window=3)

    assert mfi.update_bar(_bar(0, high="10", low="10", close="10", volume="10")) is None
    assert mfi.update_bar(_bar(1, high="11", low="11", close="11", volume="10")) is None
    assert mfi.update_bar(_bar(2, high="9", low="9", close="9", volume="10")) is None
    value = mfi.update_bar(_bar(3, high="12", low="12", close="12", volume="10"))

    assert value is not None
    assert value.quantize(Decimal("0.0001")) == Decimal("71.8750")


def test_accumulation_distribution_tracks_cumulative_money_flow_volume_anchor() -> None:
    from qts.indicators.technical import AccumulationDistribution

    adl = AccumulationDistribution()

    assert adl.update_bar(_bar(0, high="10", low="0", close="7", volume="100")) == Decimal("40")
    assert adl.update_bar(_bar(1, high="20", low="10", close="15", volume="10")) == Decimal("40")
    assert adl.update_bar(_bar(2, high="10", low="0", close="0", volume="5")) == Decimal("35")


def test_chaikin_money_flow_uses_rolling_money_flow_volume_anchor() -> None:
    from qts.indicators.technical import ChaikinMoneyFlow

    cmf = ChaikinMoneyFlow(window=3)

    assert cmf.update_bar(_bar(0, high="10", low="0", close="7", volume="100")) is None
    assert cmf.update_bar(_bar(1, high="20", low="10", close="15", volume="10")) is None
    value = cmf.update_bar(_bar(2, high="10", low="0", close="0", volume="5"))

    assert value is not None
    assert value.quantize(Decimal("0.00000001")) == Decimal("0.30434783")


def test_supertrend_uses_atr_bands_and_flips_direction_anchor() -> None:
    from qts.indicators.technical import Supertrend, SupertrendValue

    supertrend = Supertrend(window=3, multiplier=Decimal("2"))

    bars = (
        _bar(0, high="10", low="8", close="9"),
        _bar(1, high="11", low="9", close="10"),
        _bar(2, high="14", low="9", close="13"),
        _bar(3, high="17", low="13", close="16"),
        _bar(4, high="20", low="15", close="19"),
        _bar(5, high="12", low="8", close="9"),
    )
    values = [supertrend.update_bar(bar) for bar in bars]

    assert values[0] is None
    assert values[1] is None

    first = values[2]
    assert isinstance(first, SupertrendValue)
    assert first.direction == -1
    assert first.upper_band == Decimal("17.5")
    assert first.lower_band == Decimal("5.5")
    assert first.value == Decimal("17.5")

    bullish = values[4]
    assert isinstance(bullish, SupertrendValue)
    assert bullish.direction == 1
    assert bullish.value.quantize(Decimal("0.00000001")) == Decimal("9.72222222")

    bearish = values[5]
    assert isinstance(bearish, SupertrendValue)
    assert bearish.direction == -1
    assert bearish.value.quantize(Decimal("0.00000001")) == Decimal("22.51851852")
    assert supertrend.ready is True


def test_supertrend_rejects_invalid_configuration() -> None:
    from qts.indicators.technical import Supertrend

    with pytest.raises(ValueError, match="window must be positive"):
        Supertrend(window=0)

    with pytest.raises(ValueError, match="multiplier must be non-negative"):
        Supertrend(window=3, multiplier=Decimal("-1"))
