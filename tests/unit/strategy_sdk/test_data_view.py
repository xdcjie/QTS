from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.domain.market_data import Bar


def _bar(
    start: datetime,
    close: str,
    *,
    is_complete: bool = True,
    is_partial: bool = False,
) -> Bar:
    from qts.core.ids import InstrumentId

    close_value = Decimal(close)
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=max(Decimal("101"), close_value),
        low=Decimal("99"),
        close=close_value,
        volume=Decimal("100"),
        is_complete=is_complete,
        is_partial=is_partial,
    )


def test_data_view_is_time_sliced_by_as_of() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef
    from qts.strategy_sdk.data_view import DataView

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    data = DataView(
        bars={
            asset.instrument_id: [
                _bar(start, "100"),
                _bar(start + timedelta(minutes=1), "101"),
            ]
        },
        as_of=start + timedelta(minutes=1),
    )

    assert data.close(asset) == Decimal("100")
    assert data.bar(asset).close == Decimal("100")
    assert len(data.history(asset, bars=10, timeframe="1m")) == 1


def test_data_view_only_exposes_complete_non_partial_bars() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef
    from qts.strategy_sdk.data_view import DataView

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    data = DataView(
        bars={
            asset.instrument_id: [
                _bar(start, "100"),
                _bar(start + timedelta(minutes=1), "101", is_complete=False),
                _bar(start + timedelta(minutes=2), "102", is_partial=True),
            ]
        },
        as_of=start + timedelta(minutes=3),
    )

    history = data.history(asset, bars=10, timeframe="1m")

    assert [bar.close for bar in history] == [Decimal("100")]
    assert data.close(asset) == Decimal("100")


def test_indicator_updates_after_exactly_window_visible_bars() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef
    from qts.strategy_sdk.indicators import IndicatorFactory

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    indicators = IndicatorFactory()
    sma = indicators.sma(asset, window=2)

    indicators.update_from_bar(_bar(start, "100"))
    assert sma.ready is False
    indicators.update_from_bar(_bar(start + timedelta(minutes=1), "102"))

    assert sma.ready is True
    assert sma.value == Decimal("101")
