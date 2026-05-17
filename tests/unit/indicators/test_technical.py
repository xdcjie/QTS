from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

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
