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
