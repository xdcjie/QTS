"""Backtest run assembly.

Combines a ``BacktestRuntimeConfig``, a loaded strategy set, and a replay input
bundle into a runnable ``BacktestEngine``. Centralizing the engine wiring keeps
``BacktestPipeline`` a thin orchestration facade and gives both single-run and
sweep paths byte-identical engine construction for identical inputs.
"""

from __future__ import annotations

from qts.backtest.engine import BacktestEngine
from qts.data.sources.replay_market_data_source import ReplayMarketDataBundle
from qts.runtime.config import BacktestRuntimeConfig
from qts.strategy_sdk import Strategy


class BacktestRunAssembler:
    """Assemble a ``BacktestEngine`` for one run from config + strategies + inputs."""

    def __init__(self, config: BacktestRuntimeConfig) -> None:
        self._config = config

    def assemble(
        self,
        *,
        inputs: ReplayMarketDataBundle,
        strategies: tuple[Strategy, ...],
    ) -> BacktestEngine:
        """Build a fresh engine bound to the replay bundle's inputs."""
        return BacktestEngine.from_config(
            self._config,
            bars=inputs.bars,
            strategies=strategies,
            instrument_registry=inputs.instrument_registry,
            dataset_metadata=inputs.dataset_metadata,
            future_roll_registry=inputs.future_roll_registry,
            exchange_timezone_by_instrument=inputs.exchange_timezone_by_instrument,
            session_window_by_instrument=inputs.session_window_by_instrument,
            contract_multipliers=inputs.contract_multipliers,
        )


__all__ = ["BacktestRunAssembler"]
