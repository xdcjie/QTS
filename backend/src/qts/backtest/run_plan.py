"""Backtest run plan construction.

``BacktestRunPlan`` is the canonical input to ``BacktestEngine``: it carries
the normalized strategies, bar source, engine config, dependency bundle, and
execution timing needed for one run. Legacy keyword construction remains as a
compatibility wrapper that immediately builds this plan.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import tzinfo
from decimal import Decimal
from typing import Any

from qts.backtest.dependencies import BacktestEngineDependencies
from qts.backtest.engine_assembly import BacktestEngineAssembler
from qts.core.ids import InstrumentId
from qts.data.provenance import DatasetMetadata
from qts.data.sessions import RegularSessionWindow
from qts.domain.execution_costs import SimulatedExecutionCostModel
from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.runtime.config import BacktestEngineConfig, BacktestRuntimeConfig
from qts.strategy_sdk import Strategy


@dataclass(frozen=True, slots=True)
class BacktestRunPlan:
    """Normalized inputs for constructing and running one backtest."""

    strategies: tuple[Strategy, ...]
    bars: Iterable[Bar]
    registry_bars: tuple[Bar, ...]
    engine_config: BacktestEngineConfig
    dependencies: BacktestEngineDependencies
    backtest_runtime_config: BacktestRuntimeConfig | None = None
    execution_timing: ExecutionTimingModel | None = None

    @classmethod
    def from_inputs(
        cls,
        *,
        strategy: Strategy | None = None,
        strategies: Sequence[Strategy] | None = None,
        bars: Iterable[Bar],
        initial_cash: Decimal | None = None,
        engine_config: BacktestEngineConfig | None = None,
        dependencies: BacktestEngineDependencies | None = None,
        risk_engine: RiskEngine | None = None,
        dataset_metadata: Iterable[DatasetMetadata] = (),
        config: dict[str, Any] | None = None,
        strategy_version: str | None = None,
        cost_model: SimulatedExecutionCostModel | None = None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None = None,
        future_roll_registry: FutureRollRegistry | None = None,
        warmup_bars: int = 0,
        target_timeframe: str | None = None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None,
        session_window_by_instrument: Mapping[InstrumentId, RegularSessionWindow] | None = None,
        instrument_registry: InstrumentRegistry | None = None,
        backtest_runtime_config: BacktestRuntimeConfig | None = None,
        execution_timing: ExecutionTimingModel | None = None,
    ) -> BacktestRunPlan:
        """Build a normalized plan from the legacy explicit inputs."""

        strategy_set = cls._strategy_set(strategy=strategy, strategies=strategies)
        if instrument_registry is None and isinstance(bars, Sequence):
            registry_bars = tuple(bars)
            run_bars: Iterable[Bar] = registry_bars
        else:
            registry_bars = ()
            run_bars = bars

        resolved_config = cls._engine_config(
            strategy_set=strategy_set,
            initial_cash=initial_cash,
            engine_config=engine_config,
            warmup_bars=warmup_bars,
            target_timeframe=target_timeframe,
            strategy_version=strategy_version,
            config=config,
            dataset_metadata=dataset_metadata,
            cost_model=cost_model,
        )
        resolved_dependencies = dependencies or BacktestEngineDependencies.with_defaults(
            initial_cash=resolved_config.initial_cash,
            risk_engine=risk_engine,
            instrument_registry=instrument_registry,
            future_roll_registry=future_roll_registry,
            contract_multipliers=contract_multipliers,
            exchange_timezone_by_instrument=exchange_timezone_by_instrument,
            session_window_by_instrument=session_window_by_instrument,
        )
        return cls(
            strategies=strategy_set,
            bars=run_bars,
            registry_bars=registry_bars,
            engine_config=resolved_config,
            dependencies=resolved_dependencies,
            backtest_runtime_config=backtest_runtime_config,
            execution_timing=execution_timing,
        )

    @classmethod
    def from_runtime_config(
        cls,
        config: BacktestRuntimeConfig,
        *,
        bars: Iterable[Bar],
        strategy: Strategy | None = None,
        strategies: Sequence[Strategy] | None = None,
        instrument_registry: InstrumentRegistry | None = None,
        dataset_metadata: Iterable[DatasetMetadata] = (),
        future_roll_registry: FutureRollRegistry | None = None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None,
        session_window_by_instrument: Mapping[InstrumentId, RegularSessionWindow] | None = None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None = None,
        execution_timing: ExecutionTimingModel | None = None,
    ) -> BacktestRunPlan:
        """Build a run plan from a serialized backtest runtime config."""

        engine_config, dependencies, resolved_timing = (
            BacktestEngineAssembler().runtime_config_inputs(
                config,
                dataset_metadata=dataset_metadata,
                instrument_registry=instrument_registry,
                future_roll_registry=future_roll_registry,
                contract_multipliers=contract_multipliers,
                exchange_timezone_by_instrument=exchange_timezone_by_instrument,
                session_window_by_instrument=session_window_by_instrument,
                execution_timing=execution_timing,
            )
        )
        return cls.from_inputs(
            strategy=strategy,
            strategies=strategies,
            bars=bars,
            engine_config=engine_config,
            dependencies=dependencies,
            backtest_runtime_config=config,
            execution_timing=resolved_timing,
            instrument_registry=instrument_registry,
        )

    @staticmethod
    def _strategy_set(
        *,
        strategy: Strategy | None,
        strategies: Sequence[Strategy] | None,
    ) -> tuple[Strategy, ...]:
        if strategies is not None:
            if strategy is not None:
                raise ValueError("provide either strategy or strategies, not both")
            strategy_set = tuple(strategies)
        elif strategy is not None:
            strategy_set = (strategy,)
        else:
            raise ValueError("strategy or strategies is required")
        if not strategy_set:
            raise ValueError("strategies must not be empty")
        return strategy_set

    @classmethod
    def _engine_config(
        cls,
        *,
        strategy_set: tuple[Strategy, ...],
        initial_cash: Decimal | None,
        engine_config: BacktestEngineConfig | None,
        warmup_bars: int,
        target_timeframe: str | None,
        strategy_version: str | None,
        config: dict[str, Any] | None,
        dataset_metadata: Iterable[DatasetMetadata],
        cost_model: SimulatedExecutionCostModel | None,
    ) -> BacktestEngineConfig:
        if engine_config is None:
            if initial_cash is None:
                raise ValueError("initial_cash is required when engine_config is not provided")
            engine_config = BacktestEngineConfig(
                initial_cash=initial_cash,
                warmup_bars=warmup_bars,
                target_timeframe=target_timeframe,
                strategy_version=strategy_version or "",
                config_payload=dict(config or {}),
                dataset_metadata=tuple(dataset_metadata),
                cost_model=cost_model or SimulatedExecutionCostModel(),
            )
        elif initial_cash is not None and Decimal(str(initial_cash)) != engine_config.initial_cash:
            raise ValueError("initial_cash must match engine_config.initial_cash")

        if engine_config.strategy_version:
            return engine_config
        return BacktestEngineConfig(
            initial_cash=engine_config.initial_cash,
            warmup_bars=engine_config.warmup_bars,
            target_timeframe=engine_config.target_timeframe,
            strategy_version=strategy_set[0].__class__.__qualname__,
            config_payload=engine_config.config_payload,
            dataset_metadata=engine_config.dataset_metadata,
            cost_model=engine_config.cost_model,
        )


__all__ = ["BacktestRunPlan"]
