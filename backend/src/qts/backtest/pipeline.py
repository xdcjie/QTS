"""Thin orchestration facade for the shared backtest pipeline.

``BacktestPipeline`` is the single place a ``BacktestRuntimeConfig`` becomes a
runnable ``BacktestEngine`` + ``ReplayMarketDataBundle`` for both single-run and
sweep paths. It delegates: strategy loading to ``StrategyLoader``, replay input
assembly (cached catalog + replay source + materialized cache) to
``BacktestReplayInputProvider``, and engine wiring to ``BacktestRunAssembler``.
Sweep siblings share the provider's already-loaded catalog.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.backtest.assembly import BacktestRunAssembler
from qts.backtest.engine import BacktestEngine
from qts.backtest.replay_input import BacktestReplayInputProvider
from qts.data.historical.catalog import HistoricalCatalog
from qts.data.sources.replay_market_data_source import ReplayMarketDataBundle
from qts.runtime.config import BacktestRuntimeConfig, BacktestStrategyConfig
from qts.runtime.config_loader import BacktestConfigLoader
from qts.strategy_sdk import Strategy
from qts.strategy_sdk.loading import StrategyLoader


class BacktestPipeline:
    """Construct catalog + engine + strategy for a single backtest config."""

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
        self._input_provider = BacktestReplayInputProvider(
            config,
            materialized_replay_cache_dir=self._materialized_replay_cache_dir,
            catalog=catalog,
        )
        self._strategy_loader = StrategyLoader()
        self._run_assembler = BacktestRunAssembler(config)

    @classmethod
    def from_yaml(cls, config_path: Path) -> BacktestPipeline:
        """Load a config file via the config loader and wrap it in a pipeline."""
        return cls(BacktestConfigLoader.from_path(config_path))

    @property
    def config(self) -> BacktestRuntimeConfig:
        """Return the underlying backtest runtime config."""
        return self._config

    def catalog(self) -> HistoricalCatalog:
        """Return the catalog for this config, loading it on first access."""
        return self._input_provider.catalog()

    def build_engine(self) -> tuple[BacktestEngine, ReplayMarketDataBundle]:
        """Build a fresh engine + replay bundle for one run.

        The bundle's ``bars`` iterator is consumed by the engine; callers that
        need to drive multiple runs from the same config should call this once
        per run to obtain a fresh bars iterator and strategy instances.
        """
        inputs = self._input_provider.build_inputs()
        engine = self._run_assembler.assemble(inputs=inputs, strategies=self.load_strategy_set())
        return engine, inputs

    @classmethod
    def load_strategy(cls, strategy_class: str, params: Mapping[str, Any]) -> Strategy:
        """Load a Strategy by its config-encoded class path (delegates to StrategyLoader)."""
        return StrategyLoader().load(strategy_class, params)

    def load_strategy_set(self) -> tuple[Strategy, ...]:
        """Load every strategy instance declared by this backtest config."""
        return tuple(
            self._strategy_loader.load(strategy.class_path, strategy.params)
            for strategy in self._strategy_configs()
        )

    def with_strategy_params(self, params: Mapping[str, Any]) -> BacktestPipeline:
        """Return a sibling pipeline whose strategy_params merge ``params`` on top.

        The new pipeline shares the cached catalog with this one — used by
        sweeps that vary only ``strategy_params`` across runs.
        """
        merged = {**self._config.strategy_params, **params}
        strategy = self._config.strategy
        if strategy is not None:
            strategy = dataclasses.replace(strategy, params=merged)
        return self._sibling(
            dataclasses.replace(self._config, strategy=strategy, strategy_params=merged),
            materialized_replay_cache_dir=self._materialized_replay_cache_dir,
        )

    def with_date_range(self, *, start: datetime, end: datetime) -> BacktestPipeline:
        """Return a sibling pipeline with a different backtest date range."""
        return self._sibling(
            dataclasses.replace(self._config, start=start, end=end),
            materialized_replay_cache_dir=self._materialized_replay_cache_dir,
        )

    def with_materialized_replay_cache(self, cache_dir: Path | None) -> BacktestPipeline:
        """Return a sibling pipeline that reuses materialized strategy-facing bars."""
        return self._sibling(
            self._config,
            materialized_replay_cache_dir=None if cache_dir is None else Path(cache_dir),
        )

    def _sibling(
        self,
        config: BacktestRuntimeConfig,
        *,
        materialized_replay_cache_dir: Path | None,
    ) -> BacktestPipeline:
        """Build a sibling pipeline sharing this one's already-loaded catalog."""
        return BacktestPipeline(
            config,
            materialized_replay_cache_dir=materialized_replay_cache_dir,
            catalog=self._input_provider.cached_catalog(),
        )

    def _strategy_configs(self) -> tuple[BacktestStrategyConfig, ...]:
        if self._config.strategies:
            return self._config.strategies
        return (
            BacktestStrategyConfig(
                class_path=self._config.strategy_class,
                params=self._config.strategy_params,
                strategy_id=(
                    None if self._config.strategy is None else self._config.strategy.strategy_id
                ),
                account_id=None
                if self._config.strategy is None
                else self._config.strategy.account_id,
                allocation=(
                    Decimal("1")
                    if self._config.strategy is None
                    else self._config.strategy.allocation
                ),
                enabled=True if self._config.strategy is None else self._config.strategy.enabled,
            ),
        )


__all__ = ["BacktestPipeline"]
