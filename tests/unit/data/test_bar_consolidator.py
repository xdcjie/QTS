from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


def _bar(
    start: datetime,
    *,
    open_price: str,
    high: str,
    low: str,
    close: str,
    volume: str,
    is_complete: bool = True,
) -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(open_price),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        trade_count=1,
        is_complete=is_complete,
    )


def test_consolidator_emits_complete_five_minute_bar_from_one_minute_fixture() -> None:
    from qts.data.bars.consolidator import NMinuteConsolidator
    from qts.data.bars.timeframe import Timeframe

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    consolidator = NMinuteConsolidator(
        source_timeframe=Timeframe.parse("1m"),
        target_timeframe=Timeframe.parse("5m"),
        exchange_timezone=UTC,
    )
    source = [
        _bar(start, open_price="100", high="101", low="99", close="100.5", volume="10"),
        _bar(
            start + timedelta(minutes=1),
            open_price="100.5",
            high="102",
            low="100",
            close="101",
            volume="20",
        ),
        _bar(
            start + timedelta(minutes=2),
            open_price="101",
            high="103",
            low="100.5",
            close="102",
            volume="30",
        ),
        _bar(
            start + timedelta(minutes=3),
            open_price="102",
            high="102.5",
            low="98",
            close="99",
            volume="40",
        ),
        _bar(
            start + timedelta(minutes=4),
            open_price="99",
            high="100",
            low="97",
            close="98",
            volume="50",
        ),
    ]

    emitted: list[Bar] = []
    for bar in source:
        emitted.extend(consolidator.update(bar))

    assert len(emitted) == 1
    [consolidated] = emitted
    assert consolidated.start_time == start
    assert consolidated.end_time == start + timedelta(minutes=5)
    assert consolidated.timeframe == "5m"
    assert consolidated.open == Decimal("100")
    assert consolidated.high == Decimal("103")
    assert consolidated.low == Decimal("97")
    assert consolidated.close == Decimal("98")
    assert consolidated.volume == Decimal("150")
    assert consolidated.trade_count == 5
    assert consolidated.is_complete
    assert not consolidated.is_partial


def test_consolidator_does_not_emit_partial_bucket_when_next_bucket_starts() -> None:
    from qts.data.bars.consolidator import NMinuteConsolidator
    from qts.data.bars.timeframe import Timeframe

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    consolidator = NMinuteConsolidator(
        source_timeframe=Timeframe.parse("1m"),
        target_timeframe=Timeframe.parse("5m"),
        exchange_timezone=UTC,
    )

    assert (
        consolidator.update(
            _bar(start, open_price="100", high="101", low="99", close="100", volume="10")
        )
        == ()
    )
    assert (
        consolidator.update(
            _bar(
                start + timedelta(minutes=5),
                open_price="200",
                high="201",
                low="199",
                close="200",
                volume="20",
            )
        )
        == ()
    )


def test_consolidator_rejects_incomplete_source_bar() -> None:
    from qts.data.bars.consolidator import NMinuteConsolidator
    from qts.data.bars.timeframe import Timeframe

    consolidator = NMinuteConsolidator(
        source_timeframe=Timeframe.parse("1m"),
        target_timeframe=Timeframe.parse("5m"),
        exchange_timezone=UTC,
    )

    with pytest.raises(ValueError, match="source bar must be complete"):
        consolidator.update(
            _bar(
                datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
                open_price="100",
                high="101",
                low="99",
                close="100",
                volume="10",
                is_complete=False,
            )
        )
