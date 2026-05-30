"""Bar aggregation pipelines owned by runtime and configured by data semantics."""

from __future__ import annotations

from datetime import tzinfo
from typing import TYPE_CHECKING

from qts.data.bars.consolidator import Consolidator, NMinuteConsolidator
from qts.data.bars.timeframe import Timeframe
from qts.data.sessions import RegularSessionWindow

if TYPE_CHECKING:
    from qts.domain.market_data import Bar


class BarAggregationPipeline:
    """Own complete-bar consolidation state for runtime market-data streams."""

    def __init__(
        self,
        exchange_timezone: str | tzinfo,
        *,
        session_window: RegularSessionWindow | None = None,
    ) -> None:
        """Initialize the pipeline with an exchange timezone and session window."""
        self._exchange_timezone = exchange_timezone
        self._session_window = session_window
        self._consolidators: dict[tuple[object, ...], Consolidator] = {}

    def aggregate(self, bar: Bar, target_timeframe: Timeframe) -> tuple[Bar, ...]:
        """Aggregate one 1+ minute bar into an explicit target timeframe."""

        source_timeframe = Timeframe.parse(bar.timeframe)
        key = self._aggregation_key(bar, source_timeframe, target_timeframe)
        return self._consolidator_for(
            key,
            source_timeframe=source_timeframe,
            target_timeframe=target_timeframe,
        ).update(bar)

    def aggregate_logical(
        self,
        bar: Bar,
        *,
        source_timeframe: str,
        target_timeframe: str,
    ) -> tuple[Bar, ...]:
        """Aggregate bars from one source timeframe into a logical subscriber target."""

        target = Timeframe.parse(target_timeframe)
        source = Timeframe.parse(source_timeframe)
        key = self._logical_key(bar, source_timeframe, target_timeframe)
        return self._consolidator_for(
            key,
            source_timeframe=source,
            target_timeframe=target,
        ).update(bar)

    def _consolidator_for(
        self,
        key: tuple[object, ...],
        *,
        source_timeframe: Timeframe,
        target_timeframe: Timeframe,
    ) -> Consolidator:
        """Return the consolidator that owns one source/target stream."""
        consolidator = self._consolidators.get(key)
        if consolidator is None:
            consolidator = NMinuteConsolidator(
                source_timeframe=source_timeframe,
                target_timeframe=target_timeframe,
                exchange_timezone=self._exchange_timezone,
                session_window=self._session_window,
            )
            self._consolidators[key] = consolidator
        return consolidator

    @staticmethod
    def _aggregation_key(
        bar: Bar, source_timeframe: Timeframe, target_timeframe: Timeframe
    ) -> tuple[object, ...]:
        """Build the consolidator key from instrument, session, and timeframes."""
        return (bar.instrument_id, bar.session_id, str(source_timeframe), str(target_timeframe))

    @staticmethod
    def _logical_key(bar: Bar, source_timeframe: str, target_timeframe: str) -> tuple[object, ...]:
        """Build the consolidator key for a logical subscriber stream."""
        return (bar.instrument_id, source_timeframe, target_timeframe, bar.session_id)


__all__ = ["BarAggregationPipeline"]
