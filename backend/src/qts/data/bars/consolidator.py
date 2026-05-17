"""Cross-timeframe bar consolidators that emit only complete derived bars."""

from __future__ import annotations

from datetime import timedelta, tzinfo
from decimal import Decimal
from typing import Protocol

from qts.core.time import TimeInterval
from qts.data.bars.alignment import clock_bucket_for
from qts.data.bars.timeframe import AlignmentMode, Timeframe
from qts.domain.market_data import Bar


class Consolidator(Protocol):
    """Incremental primitive for deriving bars from completed source data."""

    def update(self, bar: Bar) -> tuple[Bar, ...]:
        """Process one source bar and return newly completed derived bars."""
        ...


class NMinuteConsolidator:
    """Consolidate completed lower-timeframe clock bars into larger clock bars."""

    def __init__(
        self,
        *,
        source_timeframe: Timeframe,
        target_timeframe: Timeframe,
        exchange_timezone: str | tzinfo,
    ) -> None:
        if source_timeframe.alignment is not AlignmentMode.CLOCK:
            raise ValueError("source timeframe must be clock-aligned")
        if target_timeframe.alignment is not AlignmentMode.CLOCK:
            raise ValueError("target timeframe must be clock-aligned")
        if source_timeframe.duration is None or target_timeframe.duration is None:
            raise ValueError("source and target timeframes must have durations")
        if target_timeframe.duration <= source_timeframe.duration:
            raise ValueError("target timeframe must be larger than source timeframe")
        if target_timeframe.duration % source_timeframe.duration != timedelta(0):
            raise ValueError("target timeframe must be an even multiple of source timeframe")

        self._source_timeframe = source_timeframe
        self._target_timeframe = target_timeframe
        self._exchange_timezone = exchange_timezone
        self._bucket: TimeInterval | None = None
        self._bars: tuple[Bar, ...] = ()

    def update(self, bar: Bar) -> tuple[Bar, ...]:
        """Process one completed source bar and emit complete derived bars."""

        self._validate_source_bar(bar)
        bucket = self._bucket_for(bar)

        if self._bucket is None or not self._same_bucket_stream(bucket, bar):
            self._bucket = bucket
            self._bars = (bar,)
        else:
            self._bars = (*self._bars, bar)

        if self._state_is_complete():
            completed = self._aggregate()
            self._bucket = None
            self._bars = ()
            return (completed,)

        return ()

    def _validate_source_bar(self, bar: Bar) -> None:
        if not bar.is_complete:
            raise ValueError("source bar must be complete")
        if bar.is_partial:
            raise ValueError("source bar must not be partial")
        if bar.timeframe != str(self._source_timeframe):
            raise ValueError("source bar timeframe does not match consolidator source timeframe")
        if bar.end_time - bar.start_time != self._source_timeframe.duration:
            raise ValueError("source bar interval does not match source timeframe")

    def _bucket_for(self, bar: Bar) -> TimeInterval:
        return clock_bucket_for(bar.start_time, self._target_timeframe, self._exchange_timezone)

    def _same_bucket_stream(self, bucket: TimeInterval, bar: Bar) -> bool:
        if self._bucket is None or not self._bars:
            return False
        return (
            self._bucket == bucket
            and self._bars[-1].instrument_id == bar.instrument_id
            and self._bars[-1].session_id == bar.session_id
        )

    def _state_is_complete(self) -> bool:
        if self._bucket is None or not self._bars:
            return False
        if self._bars[0].start_time != self._bucket.start:
            return False
        if self._bars[-1].end_time != self._bucket.end:
            return False
        return all(
            current.end_time == following.start_time
            for current, following in zip(self._bars, self._bars[1:], strict=False)
        )

    def _aggregate(self) -> Bar:
        if self._bucket is None or not self._bars:
            raise RuntimeError("cannot aggregate an empty consolidation state")
        first = self._bars[0]
        last = self._bars[-1]
        total_volume = sum((bar.volume for bar in self._bars), Decimal("0"))

        return Bar(
            instrument_id=first.instrument_id,
            start_time=self._bucket.start,
            end_time=self._bucket.end,
            timeframe=str(self._target_timeframe),
            session_id=first.session_id,
            open=first.open,
            high=max(bar.high for bar in self._bars),
            low=min(bar.low for bar in self._bars),
            close=last.close,
            volume=total_volume,
            vwap=self._aggregate_vwap(self._bars, total_volume),
            open_interest=self._last_open_interest(self._bars),
            trade_count=self._sum_trade_count(self._bars),
            is_complete=True,
            is_partial=False,
        )

    def _aggregate_vwap(self, bars: tuple[Bar, ...], total_volume: Decimal) -> Decimal | None:
        weighted = [
            bar.vwap * bar.volume
            for bar in bars
            if bar.vwap is not None and bar.volume > Decimal("0")
        ]
        if not weighted or total_volume <= Decimal("0"):
            return None
        return sum(weighted, Decimal("0")) / total_volume

    def _last_open_interest(self, bars: tuple[Bar, ...]) -> Decimal | None:
        for bar in reversed(bars):
            if bar.open_interest is not None:
                return bar.open_interest
        return None

    def _sum_trade_count(self, bars: tuple[Bar, ...]) -> int | None:
        counts = [bar.trade_count for bar in bars if bar.trade_count is not None]
        if not counts:
            return None
        return sum(counts)


__all__ = ["Consolidator", "NMinuteConsolidator"]
