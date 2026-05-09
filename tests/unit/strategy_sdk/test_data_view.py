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
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
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
