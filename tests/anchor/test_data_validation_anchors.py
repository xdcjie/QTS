from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal


def test_market_data_validation_anchor_rejects_session_outside_bars() -> None:
    from qts.core.ids import InstrumentId
    from qts.core.time import TimeInterval
    from qts.data.validation_report import DataValidationIssueCode, validate_bars
    from qts.domain.market_data import Bar

    open_time = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    close_time = datetime(2026, 1, 2, 21, 0, tzinfo=UTC)
    outside = Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=close_time,
        end_time=close_time + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        is_complete=True,
    )

    report = validate_bars(
        (outside,),
        session_interval=TimeInterval(start=open_time, end=close_time),
    )

    assert not report.valid
    assert report.issues[0].code is DataValidationIssueCode.OUTSIDE_SESSION
