"""Bar aggregation: 5s -> 1m -> 5m -> 15m -> 30m -> 1h -> 4h -> 1d."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, tzinfo
from decimal import Decimal

from qts.core.time import TimeInterval
from qts.data.bars.alignment import clock_bucket_for
from qts.data.bars.timeframe import AlignmentMode, Timeframe
from qts.domain.market_data import Bar
from qts.registry.calendar_registry import MarketSession


@dataclass(frozen=True, slots=True)
class AggregationState:
    """Current in-progress aggregation bucket."""

    bucket: TimeInterval
    natural_bucket_end: datetime
    target_timeframe: Timeframe
    bars: tuple[Bar, ...]

    @property
    def aggregate_end(self) -> datetime:
        return self.bucket.end


@dataclass(frozen=True, slots=True)
class AggregationResult:
    """Result returned by one incremental aggregator update."""

    completed: tuple[Bar, ...]
    state: AggregationState | None


class BarAggregator:
    """Stateful incremental bar aggregator for one ordered bar stream."""

    def __init__(
        self,
        *,
        target_timeframe: Timeframe,
        exchange_timezone: str | tzinfo,
        session: MarketSession | None = None,
    ) -> None:
        if target_timeframe.alignment is not AlignmentMode.CLOCK:
            raise ValueError("BarAggregator currently supports clock-aligned timeframes")
        self._target_timeframe = target_timeframe
        self._exchange_timezone = exchange_timezone
        self._session = session
        self.state: AggregationState | None = None

    def update(self, bar: Bar) -> AggregationResult:
        """Add a lower-timeframe bar and return any completed aggregate bars."""

        if self._session is not None and not _bar_inside_session(bar, self._session):
            return AggregationResult(completed=(), state=self.state)

        incoming_state = self._new_state_for(bar)
        completed: list[Bar] = []

        if self.state is not None and not _same_stream_bucket(self.state, incoming_state):
            completed.append(_aggregate_state(self.state))
            self.state = None

        if self.state is None:
            self.state = incoming_state
        else:
            self.state = AggregationState(
                bucket=self.state.bucket,
                natural_bucket_end=self.state.natural_bucket_end,
                target_timeframe=self.state.target_timeframe,
                bars=(*self.state.bars, bar),
            )

        if self.state.bars[-1].end_time >= self.state.aggregate_end:
            completed.append(_aggregate_state(self.state))
            self.state = None

        return AggregationResult(completed=tuple(completed), state=self.state)

    def finish(self) -> AggregationResult:
        """Flush the current bucket as a partial aggregate when present."""

        if self.state is None:
            return AggregationResult(completed=(), state=None)
        completed = _aggregate_state(self.state)
        self.state = None
        return AggregationResult(completed=(completed,), state=None)

    def _new_state_for(self, bar: Bar) -> AggregationState:
        bucket = clock_bucket_for(bar.start_time, self._target_timeframe, self._exchange_timezone)
        aggregate_end = bucket.end
        if self._session is not None and self._session.close_time < aggregate_end:
            aggregate_end = self._session.close_time
        return AggregationState(
            bucket=TimeInterval(start=bucket.start, end=aggregate_end),
            natural_bucket_end=bucket.end,
            target_timeframe=self._target_timeframe,
            bars=(bar,),
        )


def aggregate_bars(
    bars: Iterable[Bar],
    *,
    target_timeframe: Timeframe,
    exchange_timezone: str | tzinfo,
    session: MarketSession | None = None,
) -> list[Bar]:
    """Aggregate bars into a higher clock-aligned timeframe."""

    aggregated: list[Bar] = []
    aggregators: dict[object, BarAggregator] = {}
    ordered_bars = sorted(bars, key=lambda item: (item.instrument_id.value, item.start_time))
    for bar in ordered_bars:
        aggregator = aggregators.setdefault(
            bar.instrument_id,
            BarAggregator(
                target_timeframe=target_timeframe,
                exchange_timezone=exchange_timezone,
                session=session,
            ),
        )
        aggregated.extend(aggregator.update(bar).completed)

    for aggregator in aggregators.values():
        aggregated.extend(aggregator.finish().completed)

    return sorted(aggregated, key=lambda bar: (bar.instrument_id.value, bar.start_time))


def _bar_inside_session(bar: Bar, session: MarketSession) -> bool:
    return session.interval.contains(bar.start_time) and bar.end_time <= session.close_time


def _same_stream_bucket(left: AggregationState, right: AggregationState) -> bool:
    return (
        left.bucket == right.bucket
        and left.bars[-1].instrument_id == right.bars[-1].instrument_id
        and left.bars[-1].session_id == right.bars[-1].session_id
    )


def _aggregate_state(state: AggregationState) -> Bar:
    if not state.bars:
        raise ValueError("cannot aggregate an empty bucket")

    first = state.bars[0]
    last = state.bars[-1]
    instrument_id = first.instrument_id
    session_id = first.session_id
    for bar in state.bars:
        if bar.instrument_id != instrument_id:
            raise ValueError("cannot aggregate bars for different instruments")
        if bar.session_id != session_id:
            raise ValueError("cannot aggregate bars for different sessions")

    is_partial = (
        first.start_time != state.bucket.start
        or last.end_time < state.aggregate_end
        or state.aggregate_end != state.natural_bucket_end
        or not all(bar.is_complete for bar in state.bars)
    )
    total_volume = sum((bar.volume for bar in state.bars), Decimal("0"))
    return Bar(
        instrument_id=instrument_id,
        start_time=state.bucket.start,
        end_time=state.aggregate_end,
        timeframe=str(state.target_timeframe),
        session_id=session_id,
        open=first.open,
        high=max(bar.high for bar in state.bars),
        low=min(bar.low for bar in state.bars),
        close=last.close,
        volume=total_volume,
        vwap=_aggregate_vwap(state.bars, total_volume),
        open_interest=_last_open_interest(state.bars),
        trade_count=_sum_trade_count(state.bars),
        is_complete=not is_partial,
        is_partial=is_partial,
    )


def _aggregate_vwap(bars: tuple[Bar, ...], total_volume: Decimal) -> Decimal | None:
    weighted = [
        bar.vwap * bar.volume for bar in bars if bar.vwap is not None and bar.volume > Decimal("0")
    ]
    if not weighted or total_volume <= Decimal("0"):
        return None
    return sum(weighted, Decimal("0")) / total_volume


def _last_open_interest(bars: tuple[Bar, ...]) -> Decimal | None:
    for bar in reversed(bars):
        if bar.open_interest is not None:
            return bar.open_interest
    return None


def _sum_trade_count(bars: tuple[Bar, ...]) -> int | None:
    counts = [bar.trade_count for bar in bars if bar.trade_count is not None]
    if not counts:
        return None
    return sum(counts)


__all__ = ["AggregationResult", "AggregationState", "BarAggregator", "aggregate_bars"]
