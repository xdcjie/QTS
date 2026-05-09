from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.domain.market_data import Bar


def _bar(start: datetime, close: str) -> Bar:
    from qts.core.ids import InstrumentId

    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_historical_data_portal_returns_time_sliced_dataview() -> None:
    from qts.backtest.historical_data_portal import HistoricalDataPortal
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    portal = HistoricalDataPortal(
        {asset.instrument_id: [_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")]}
    )

    view = portal.data_view(as_of=start + timedelta(minutes=1))

    assert view.close(asset) == Decimal("100")
    assert len(view.history(asset, bars=10, timeframe="1m")) == 1


def test_historical_data_portal_history_does_not_expose_future_bars() -> None:
    from qts.backtest.historical_data_portal import HistoricalDataPortal
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    portal = HistoricalDataPortal(
        {asset.instrument_id: [_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")]}
    )

    history = portal.history(asset, as_of=start + timedelta(minutes=1), bars=10, timeframe="1m")

    assert [bar.close for bar in history] == [Decimal("100")]
