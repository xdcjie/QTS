"""Shared market data normalization and aggregation pipeline."""

from __future__ import annotations

from datetime import tzinfo

from qts.data.bars.pipeline import BarAggregationPipeline
from qts.data.bars.timeframe import Timeframe
from qts.domain.market_data import Bar


class MarketDataPipeline:
    """Process market data without owning runtime actor or queue orchestration."""

    def __init__(self, exchange_timezone: str | tzinfo | None = None) -> None:
        """Create a pipeline for optional bar aggregation."""
        self._exchange_timezone = exchange_timezone
        self._aggregation_pipeline = (
            BarAggregationPipeline(exchange_timezone) if exchange_timezone is not None else None
        )

    def process_bar(
        self,
        bar: Bar,
        *,
        target_timeframe: str | None,
    ) -> tuple[Bar, ...]:
        """Return strategy-facing bars for one source bar."""
        if target_timeframe is None or bar.timeframe == target_timeframe:
            return (bar,)
        if self._aggregation_pipeline is None:
            raise RuntimeError("exchange timezone is required to aggregate market data")
        return self._aggregation_pipeline.aggregate(bar, Timeframe.parse(target_timeframe))


__all__ = ["MarketDataPipeline"]
