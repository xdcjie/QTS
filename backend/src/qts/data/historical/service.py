"""Backward-compatible historical market data service import surface."""

from qts.data.historical.adapter import HistoricalMarketDataAdapter

HistoricalMarketDataService = HistoricalMarketDataAdapter
ReplayMarketDataAdapter = HistoricalMarketDataAdapter


__all__ = [
    "HistoricalMarketDataAdapter",
    "HistoricalMarketDataService",
    "ReplayMarketDataAdapter",
]
