"""Bar aggregation pipelines owned by runtime and configured by data semantics."""

from __future__ import annotations

from datetime import tzinfo
from typing import TYPE_CHECKING

from qts.data.bars.aggregator import BarAggregator
from qts.data.bars.timeframe import Timeframe

if TYPE_CHECKING:
    from qts.domain.market_data import Bar


class BarAggregationPipeline:
    """Own incremental aggregation state for bar streams in memory."""

    def __init__(self, exchange_timezone: str | tzinfo) -> None:
        """Perform __init__."""
        self._exchange_timezone = exchange_timezone
        self._aggregators: dict[tuple[object, ...], BarAggregator] = {}

    def aggregate(self, bar: Bar, target_timeframe: Timeframe) -> tuple[Bar, ...]:
        """Aggregate one 1+ minute bar into an explicit target timeframe."""

        key = self._aggregation_key(bar, target_timeframe)
        return self._aggregator_for(key, target_timeframe).update(bar).completed

    def aggregate_logical(
        self,
        bar: Bar,
        *,
        source_timeframe: str,
        target_timeframe: str,
    ) -> tuple[Bar, ...]:
        """Aggregate bars from one source timeframe into a logical subscriber target."""

        target = Timeframe.parse(target_timeframe)
        key = self._logical_key(bar, source_timeframe, target_timeframe)
        return self._aggregator_for(key, target).update(bar).completed

    def _aggregator_for(
        self, key: tuple[object, ...], target_timeframe: Timeframe
    ) -> BarAggregator:
        """Perform _aggregator_for."""
        aggregator = self._aggregators.get(key)
        if aggregator is None:
            aggregator = BarAggregator(
                target_timeframe=target_timeframe,
                exchange_timezone=self._exchange_timezone,
            )
            self._aggregators[key] = aggregator
        return aggregator

    @staticmethod
    def _aggregation_key(bar: Bar, timeframe: Timeframe) -> tuple[object, ...]:
        """Perform _aggregation_key."""
        return (bar.instrument_id, bar.session_id, str(timeframe))

    @staticmethod
    def _logical_key(bar: Bar, source_timeframe: str, target_timeframe: str) -> tuple[object, ...]:
        """Perform _logical_key."""
        return (bar.instrument_id, source_timeframe, target_timeframe, bar.session_id)


__all__ = ["BarAggregationPipeline"]
