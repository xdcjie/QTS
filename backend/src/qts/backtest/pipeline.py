"""Owning class for the shared backtest pipeline.

``BacktestPipeline`` is the single place where a ``BacktestRuntimeConfig``
is turned into a runnable ``BacktestEngine`` plus its
``ReplayMarketDataBundle``. Both single-run backtests
(``qts.backtest.runner.run_backtest``) and parameter sweeps
(``qts.research.optimizer.pipeline.BacktestPipelineRunner``) go through
this class so the two code paths see byte-identical instance wiring
for identical configs.

Catalog loading is expensive and read-only; the instance caches it so
sweeps that build many engines against the same base config pay the
catalog cost once.
"""

from __future__ import annotations

import dataclasses
import importlib
import importlib.util
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.data.historical.catalog import (
    HistoricalCatalog,
    HistoricalCatalogLoadConfig,
)
from qts.data.sources.replay_market_data_source import (
    ReplayMarketDataBundle,
    ReplayMarketDataSource,
)
from qts.runtime.config import BacktestRuntimeConfig
from qts.strategy_sdk import Strategy


class BacktestPipeline:
    """Construct catalog + engine + strategy for a single backtest config."""

    def __init__(self, config: BacktestRuntimeConfig) -> None:
        self._config = config
        self._catalog: HistoricalCatalog | None = None

    @classmethod
    def from_yaml(cls, config_path: Path) -> BacktestPipeline:
        """Load a config file and wrap it in a pipeline."""
        return cls(BacktestRuntimeConfig.from_yaml(config_path))

    @property
    def config(self) -> BacktestRuntimeConfig:
        """Return the underlying backtest runtime config."""
        return self._config

    def catalog(self) -> HistoricalCatalog:
        """Return the catalog for this config, loading it on first access."""
        if self._catalog is None:
            self._catalog = HistoricalCatalog.load(self._catalog_load_config())
        return self._catalog

    def build_engine(self) -> tuple[BacktestEngine, ReplayMarketDataBundle]:
        """Build a fresh engine + replay bundle for one run.

        The bundle's ``bars`` iterator is consumed by the engine; callers
        that need to drive multiple runs from the same config should call
        this once per run to obtain a fresh bars iterator and strategy
        instance.
        """
        inputs = ReplayMarketDataSource(self._config, self.catalog()).build()
        strategy = self.load_strategy(self._config.strategy_class, self._config.strategy_params)
        engine = BacktestEngine.from_config(
            self._config,
            bars=inputs.bars,
            strategy=strategy,
            instrument_registry=inputs.instrument_registry,
            dataset_metadata=inputs.dataset_metadata,
            future_roll_registry=inputs.future_roll_registry,
            exchange_timezone_by_instrument=inputs.exchange_timezone_by_instrument,
            contract_multipliers=inputs.contract_multipliers,
        )
        return engine, inputs

    def with_strategy_params(self, params: Mapping[str, Any]) -> BacktestPipeline:
        """Return a sibling pipeline whose strategy_params merge ``params`` on top.

        The new pipeline shares the cached catalog with this one — used by
        sweeps that vary only ``strategy_params`` across runs.
        """
        merged = {**self._config.strategy_params, **params}
        sibling = BacktestPipeline(dataclasses.replace(self._config, strategy_params=merged))
        sibling._catalog = self._catalog
        return sibling

    @classmethod
    def load_strategy(cls, strategy_class: str, params: Mapping[str, Any]) -> Strategy:
        """Load a Strategy by its config-encoded class path and instantiate it.

        Accepts both ``module.path:ClassName`` and ``module.path.ClassName``
        spellings.
        """
        module_name, separator, class_name = strategy_class.partition(":")
        if not separator:
            module_name, _, class_name = strategy_class.rpartition(".")
        if not module_name or not class_name:
            raise ValueError("strategy_class must be 'module:Class' or 'module.Class'")
        module = cls._import_strategy_module(module_name)
        strategy_type = cls._strategy_type_from_module(module, class_name)
        return strategy_type(**dict(params))

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

    @staticmethod
    def _import_strategy_module(module_name: str) -> ModuleType:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError:
            module_path = Path(*module_name.split(".")).with_suffix(".py")
            if not module_path.exists():
                raise
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                raise
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    @staticmethod
    def _strategy_type_from_module(module: ModuleType, class_name: str) -> type[Strategy]:
        strategy_type = vars(module).get(class_name)
        if strategy_type is None:
            raise ValueError(
                f"strategy class '{class_name}' not found in module '{module.__name__}'"
            )
        if not isinstance(strategy_type, type):
            raise TypeError(f"{class_name} in module '{module.__name__}' is not a class")
        if not issubclass(strategy_type, Strategy):
            raise TypeError(
                f"{class_name} in module '{module.__name__}' must subclass "
                "qts.strategy_sdk.Strategy"
            )
        return strategy_type


__all__ = ["BacktestPipeline"]
