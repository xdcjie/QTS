from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.domain.market_data import Bar


def _bar(
    start: datetime,
    *,
    open_price: str,
    high: str,
    low: str,
    close: str,
    volume: str,
) -> Bar:
    from qts.core.ids import InstrumentId

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
        is_complete=True,
    )


def test_aggregates_five_one_minute_bars_into_one_five_minute_bar() -> None:
    from qts.data.bars.aggregator import aggregate_bars
    from qts.data.bars.timeframe import Timeframe

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [
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

    [aggregated] = aggregate_bars(
        bars,
        target_timeframe=Timeframe.parse("5m"),
        exchange_timezone=UTC,
    )

    assert aggregated.start_time == start
    assert aggregated.end_time == start + timedelta(minutes=5)
    assert aggregated.timeframe == "5m"
    assert aggregated.open == Decimal("100")
    assert aggregated.high == Decimal("103")
    assert aggregated.low == Decimal("97")
    assert aggregated.close == Decimal("98")
    assert aggregated.volume == Decimal("150")
    assert aggregated.trade_count == 5
    assert aggregated.is_complete
    assert not aggregated.is_partial


def test_aggregator_marks_partial_and_excludes_session_outside_bars() -> None:
    from qts.core.time import TimeInterval
    from qts.data.bars.aggregator import aggregate_bars
    from qts.data.bars.timeframe import Timeframe
    from qts.registry.calendar_registry import MarketSession

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    session = MarketSession(
        calendar_id="XNYS",
        session_id="2026-01-02",
        interval=TimeInterval(start=start, end=start + timedelta(minutes=3)),
    )
    bars = [
        _bar(
            start - timedelta(minutes=1),
            open_price="90",
            high="91",
            low="89",
            close="90",
            volume="100",
        ),
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
    ]

    [aggregated] = aggregate_bars(
        bars,
        target_timeframe=Timeframe.parse("5m"),
        exchange_timezone=UTC,
        session=session,
    )

    assert aggregated.open == Decimal("100")
    assert aggregated.close == Decimal("102")
    assert aggregated.volume == Decimal("60")
    assert aggregated.is_partial
    assert not aggregated.is_complete


def test_bar_aggregator_updates_incrementally_and_returns_completed_bucket() -> None:
    from qts.data.bars.aggregator import AggregationResult, BarAggregator
    from qts.data.bars.timeframe import Timeframe

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    aggregator = BarAggregator(target_timeframe=Timeframe.parse("5m"), exchange_timezone=UTC)
    result: AggregationResult | None = None

    for offset in range(5):
        result = aggregator.update(
            _bar(
                start + timedelta(minutes=offset),
                open_price=str(100 + offset),
                high=str(101 + offset),
                low=str(99 + offset),
                close=str(100 + offset),
                volume="10",
            )
        )

    assert result is not None
    assert len(result.completed) == 1
    [completed] = result.completed
    assert completed.start_time == start
    assert completed.end_time == start + timedelta(minutes=5)
    assert completed.open == Decimal("100")
    assert completed.high == Decimal("105")
    assert completed.low == Decimal("99")
    assert completed.close == Decimal("104")
    assert completed.volume == Decimal("50")
    assert completed.is_complete
    assert aggregator.state is None


def test_bar_aggregator_completes_previous_bucket_when_next_bucket_starts() -> None:
    from qts.data.bars.aggregator import BarAggregator
    from qts.data.bars.timeframe import Timeframe

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    aggregator = BarAggregator(target_timeframe=Timeframe.parse("5m"), exchange_timezone=UTC)

    aggregator.update(
        _bar(start, open_price="100", high="101", low="99", close="100", volume="10")
    )
    result = aggregator.update(
        _bar(
            start + timedelta(minutes=5),
            open_price="200",
            high="201",
            low="199",
            close="200",
            volume="20",
        )
    )

    assert len(result.completed) == 1
    assert result.completed[0].start_time == start
    assert result.completed[0].is_partial
    assert aggregator.state is not None
    assert aggregator.state.bucket.start == start + timedelta(minutes=5)
