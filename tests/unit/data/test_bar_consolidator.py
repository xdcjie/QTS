from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.data.sessions import RegularSessionWindow
from qts.domain.market_data import Bar


def _bar(
    start: datetime,
    *,
    open_price: str,
    high: str,
    low: str,
    close: str,
    volume: str,
    session_id: str = "2026-01-02",
    is_complete: bool = True,
) -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id=session_id,
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


def test_consolidator_derived_five_minute_bar_matches_historical_fixture() -> None:
    from qts.data.bars.consolidator import NMinuteConsolidator
    from qts.data.bars.timeframe import Timeframe

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    consolidator = NMinuteConsolidator(
        source_timeframe=Timeframe.parse("1m"),
        target_timeframe=Timeframe.parse("5m"),
        exchange_timezone=UTC,
    )
    source = (
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
    )
    expected = Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=5),
        timeframe="5m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("103"),
        low=Decimal("97"),
        close=Decimal("98"),
        volume=Decimal("150"),
        trade_count=5,
        is_complete=True,
        is_partial=False,
    )

    emitted: list[Bar] = []
    for bar in source:
        emitted.extend(consolidator.update(bar))

    assert tuple(emitted) == (expected,)


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


def test_session_daily_consolidator_emits_at_configured_session_close() -> None:
    from qts.data.bars.consolidator import NMinuteConsolidator
    from qts.data.bars.timeframe import Timeframe

    start = datetime(2026, 5, 19, 22, 0, tzinfo=UTC)
    session_window = RegularSessionWindow(
        exchange_timezone="UTC",
        open_time=datetime.strptime("22:00", "%H:%M").time(),
        close_time=datetime.strptime("22:03", "%H:%M").time(),
    )
    consolidator = NMinuteConsolidator(
        source_timeframe=Timeframe.parse("1m"),
        target_timeframe=Timeframe.parse("1d"),
        exchange_timezone=UTC,
        session_window=session_window,
    )

    emitted: list[Bar] = []
    emitted.extend(
        consolidator.update(
            _bar(
                start,
                open_price="4486.6",
                high="4486.6",
                low="4486.6",
                close="4486.6",
                volume="10",
                session_id="2026-05-19",
            )
        )
    )
    emitted.extend(
        consolidator.update(
            _bar(
                start + timedelta(minutes=1),
                open_price="4486.6",
                high="4558.4",
                low="4455.0",
                close="4546.2",
                volume="20",
                session_id="2026-05-19",
            )
        )
    )
    emitted.extend(
        consolidator.update(
            _bar(
                start + timedelta(minutes=2),
                open_price="4546.2",
                high="4546.2",
                low="4546.2",
                close="4546.2",
                volume="30",
                session_id="2026-05-19",
            )
        )
    )

    assert len(emitted) == 1
    [daily] = emitted
    assert daily.start_time == datetime(2026, 5, 19, 22, 0, tzinfo=UTC)
    assert daily.end_time == datetime(2026, 5, 19, 22, 3, tzinfo=UTC)
    assert daily.timeframe == "1d"
    assert daily.session_id == "2026-05-19"
    assert daily.open == Decimal("4486.6")
    assert daily.high == Decimal("4558.4")
    assert daily.low == Decimal("4455.0")
    assert daily.close == Decimal("4546.2")
    assert daily.volume == Decimal("60")
    assert daily.is_complete
    assert not daily.is_partial
