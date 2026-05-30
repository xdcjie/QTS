"""Replay input assembly for a backtest run.

Owns turning a ``BacktestRuntimeConfig`` into a runnable
``ReplayMarketDataBundle``: loading the historical catalog (cached, since it is
expensive and read-only), building the replay source, and optionally
materializing strategy-facing bars to a cache. The catalog is independent of
``strategy_params`` and the date range, so sweep siblings can share one loaded
catalog via :meth:`cached_catalog`.
"""

from __future__ import annotations

from pathlib import Path

from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig
from qts.data.sources.materialized_replay_cache import materialized_replay_inputs
from qts.data.sources.replay_market_data_source import (
    ReplayMarketDataBundle,
    ReplayMarketDataSource,
)
from qts.runtime.config import BacktestRuntimeConfig


class BacktestReplayInputProvider:
    """Build (and cache) the replay market-data inputs for one backtest config."""

    def __init__(
        self,
        config: BacktestRuntimeConfig,
        *,
        materialized_replay_cache_dir: Path | None = None,
        catalog: HistoricalCatalog | None = None,
    ) -> None:
        self._config = config
        self._materialized_replay_cache_dir = (
            None if materialized_replay_cache_dir is None else Path(materialized_replay_cache_dir)
        )
        self._catalog = catalog

    def catalog(self) -> HistoricalCatalog:
        """Return the catalog for this config, loading it on first access."""
        if self._catalog is None:
            self._catalog = HistoricalCatalog.load(self._catalog_load_config())
        return self._catalog

    def cached_catalog(self) -> HistoricalCatalog | None:
        """Return the already-loaded catalog without forcing a load.

        Used to share one loaded catalog across sweep sibling providers whose
        configs differ only in fields the catalog does not depend on.
        """
        return self._catalog

    def build_inputs(self) -> ReplayMarketDataBundle:
        """Build a fresh replay bundle (with a fresh bars iterator) for one run."""
        catalog = self.catalog()
        inputs = ReplayMarketDataSource(self._config, catalog).build()
        if self._materialized_replay_cache_dir is not None:
            inputs = materialized_replay_inputs(
                config=self._config,
                catalog=catalog,
                inputs=inputs,
                cache_dir=self._materialized_replay_cache_dir,
            )
        return inputs

    def _catalog_load_config(self) -> HistoricalCatalogLoadConfig:
        market_data = self._config.market_data
        if market_data.config_path is None or market_data.catalog is None:
            raise RuntimeError("market data reference is partially configured")
        return HistoricalCatalogLoadConfig.from_historical_market_data_config(
            market_data.config_path,
            catalog=market_data.catalog,
            roots=self._config.roots,
            instrument_ids=self._config.instrument_ids,
            requested_timeframe=self._config.timeframe,
        )


__all__ = ["BacktestReplayInputProvider"]
