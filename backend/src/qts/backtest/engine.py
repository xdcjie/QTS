"""Backtest engine."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import tzinfo
from decimal import Decimal
from typing import Any

from qts.backtest.actor_loop import BacktestActorLoop
from qts.backtest.dependencies import (
    BacktestActorLoopConfig,
    BacktestActorLoopDependencies,
    BacktestEngineDependencies,
)
from qts.backtest.instrument_context import BacktestInstrumentContext
from qts.backtest.portfolio_projection import BacktestPortfolioProjector
from qts.core.hashing import stable_json_hash
from qts.core.ids import BacktestRunId, InstrumentId
from qts.data.provenance import DatasetMetadata
from qts.domain.market_data import Bar
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.reporting.backtest import (
    BacktestArtifactWriter,
    EquityCurvePoint,
    dataset_metadata_payload,
    zero_time,
)
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.actors.signal_aggregator_actor import (
    AggregatedSignalBatch,
    SignalAggregatorActor,
    StrategySignalEvent,
)
from qts.runtime.actors.strategy_actor import (
    StrategyActor,
    StrategyBarEvent,
    StrategyBarResult,
    StrategyFinalize,
    StrategyFinalized,
)
from qts.runtime.config import BacktestCostModel, BacktestEngineConfig, BacktestRuntimeConfig
from qts.runtime.intent_processing import TargetIntentProcessor
from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
from qts.runtime.sinks.base import RuntimeEventContext
from qts.strategy_sdk import Strategy


@dataclass(frozen=True, slots=True)
class BacktestStreamResult:
    """Backtest result written to partitioned streaming artifacts."""

    processed_bars: int
    warmup_bars: int
    trading_bars: int
    final_account: AccountSnapshot
    run_id: BacktestRunId
    strategy_version: str
    config_hash: str
    dataset_metadata: tuple[DatasetMetadata, ...]
    cost_model: BacktestCostModel
    report_hash: str
    manifest_path: Any
    artifact_paths: dict[str, Any]
    artifact_rows: dict[str, int]
    artifact_hashes: dict[str, str]


class BacktestEngine:
    """Single-process backtest engine using the Strategy SDK and actor order flow."""

    def __init__(
        self,
        *,
        strategy: Strategy,
        bars: Iterable[Bar],
        initial_cash: Decimal | None = None,
        engine_config: BacktestEngineConfig | None = None,
        dependencies: BacktestEngineDependencies | None = None,
        risk_engine: RiskEngine | None = None,
        dataset_metadata: Iterable[DatasetMetadata] = (),
        config: dict[str, Any] | None = None,
        strategy_version: str | None = None,
        cost_model: BacktestCostModel | None = None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None = None,
        future_roll_registry: FutureRollRegistry | None = None,
        warmup_bars: int = 0,
        target_timeframe: str | None = None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None,
        instrument_registry: InstrumentRegistry | None = None,
    ) -> None:
        """Create an engine from explicit config and dependency objects.

        Keyword arguments are normalized into ``BacktestEngineConfig`` and
        ``BacktestEngineDependencies`` when explicit objects are not supplied.
        """
        self._strategy = strategy
        if instrument_registry is None and isinstance(bars, Sequence):
            self._registry_bars = tuple(bars)
            self._bars = iter(self._registry_bars)
        else:
            self._registry_bars = ()
            self._bars = iter(bars)

        if engine_config is None:
            if initial_cash is None:
                raise ValueError("initial_cash is required when engine_config is not provided")
            engine_config = BacktestEngineConfig.from_legacy_kwargs(
                initial_cash=initial_cash,
                warmup_bars=warmup_bars,
                target_timeframe=target_timeframe,
                strategy_version=strategy_version or strategy.__class__.__qualname__,
                config=config,
                cost_model=cost_model,
                dataset_metadata=dataset_metadata,
            )
        elif initial_cash is not None and Decimal(str(initial_cash)) != engine_config.initial_cash:
            raise ValueError("initial_cash must match engine_config.initial_cash")

        if not engine_config.strategy_version:
            engine_config = BacktestEngineConfig(
                initial_cash=engine_config.initial_cash,
                warmup_bars=engine_config.warmup_bars,
                target_timeframe=engine_config.target_timeframe,
                strategy_version=strategy.__class__.__qualname__,
                config_payload=engine_config.config_payload,
                dataset_metadata=engine_config.dataset_metadata,
                cost_model=engine_config.cost_model,
            )

        if dependencies is None:
            dependencies = BacktestEngineDependencies.with_defaults(
                initial_cash=engine_config.initial_cash,
                risk_engine=risk_engine,
                instrument_registry=instrument_registry,
                future_roll_registry=future_roll_registry,
                contract_multipliers=contract_multipliers,
                exchange_timezone_by_instrument=exchange_timezone_by_instrument,
            )

        self._config = engine_config
        self._initial_cash = engine_config.initial_cash
        self._dataset_metadata = engine_config.dataset_metadata
        self._config_hash_payload = engine_config.config_payload
        self._strategy_version = engine_config.strategy_version
        self._cost_model = engine_config.cost_model
        self._contract_multipliers = dict(dependencies.contract_multipliers)
        self._future_roll_registry = dependencies.future_roll_registry
        self._warmup_bars = engine_config.warmup_bars
        self._target_timeframe = engine_config.target_timeframe
        self._exchange_timezone_by_instrument = dict(dependencies.exchange_timezone_by_instrument)
        self._risk_engine = dependencies.risk_engine
        self._execution_adapter = dependencies.execution_adapter or SimulatedExecutionAdapter(
            self._cost_model
        )
        self._instrument_context = BacktestInstrumentContext(
            future_roll_registry=self._future_roll_registry,
            instrument_registry=dependencies.instrument_registry,
            registry_bars=self._registry_bars,
            contract_multipliers=self._contract_multipliers,
        )
        self._portfolio_projector = BacktestPortfolioProjector(
            contract_multipliers=self._contract_multipliers
        )
        self._intent_processor = TargetIntentProcessor(
            risk_engine=self._risk_engine,
            instrument_context=self._instrument_context,
            multiplier_for=self._portfolio_projector.multiplier_for,
        )

    @classmethod
    def from_config(
        cls,
        config: BacktestRuntimeConfig,
        *,
        bars: Iterable[Bar],
        strategy: Strategy,
        instrument_registry: InstrumentRegistry | None = None,
        dataset_metadata: Iterable[DatasetMetadata] = (),
        future_roll_registry: FutureRollRegistry | None = None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None = None,
    ) -> BacktestEngine:
        """Build an engine from a serialized backtest run config."""
        cost_model = BacktestCostModel(
            fixed_commission_per_contract=config.cost_model.fixed_commission_per_contract,
            slippage_bps=config.cost_model.slippage_bps,
        )
        engine_config = BacktestEngineConfig(
            initial_cash=config.initial_cash,
            warmup_bars=config.warmup_bars,
            target_timeframe=config.timeframe,
            strategy_version=config.strategy_class,
            config_payload=config.to_payload(),
            dataset_metadata=tuple(dataset_metadata),
            cost_model=cost_model,
        )
        dependencies = BacktestEngineDependencies.with_defaults(
            initial_cash=config.initial_cash,
            risk_engine=RiskEngine([MaxNotionalRule(max_notional=config.risk_config.max_notional)]),
            instrument_registry=instrument_registry,
            future_roll_registry=future_roll_registry,
            contract_multipliers=contract_multipliers,
            exchange_timezone_by_instrument=exchange_timezone_by_instrument,
        )
        return cls(
            strategy=strategy,
            bars=bars,
            engine_config=engine_config,
            dependencies=dependencies,
        )

    def run_streaming(self, output_dir: Any) -> BacktestStreamResult:
        """Run the backtest and write streaming artifacts."""
        config_hash = stable_json_hash(self._config_hash_payload)
        runtime_run_id = BacktestRunId(f"bt-{config_hash.removeprefix('sha256:')[:12]}")
        writer = BacktestArtifactWriter(output_dir, run_id=runtime_run_id)
        sink = BacktestRuntimeEventSink(
            writer,
            context=RuntimeEventContext(
                run_id=runtime_run_id,
                mode="backtest",
                execution_environment="simulated",
            ),
        )
        actor_loop = BacktestActorLoop(
            strategy=self._strategy,
            bars=self._bars,
            config=BacktestActorLoopConfig(
                initial_cash=self._initial_cash,
                target_timeframe=self._target_timeframe,
                warmup_bars=self._warmup_bars,
            ),
            dependencies=BacktestActorLoopDependencies(
                instrument_registry=self._instrument_context.instrument_registry(),
                future_roll_registry=self._future_roll_registry,
                contract_multipliers=self._contract_multipliers,
                exchange_timezone_by_instrument=self._exchange_timezone_by_instrument,
                execution_adapter=self._execution_adapter,
                process_intent=self._intent_processor.process_intent,
                portfolio_view=self._portfolio_projector.portfolio_view,
                equity_point=self._portfolio_projector.equity_point,
                update_rolling_prices=self._instrument_context.update_rolling_prices,
            ),
        )
        runtime = actor_loop.run(
            sink=sink,
            prune_history=True,
            compact_orders=True,
        )

        if runtime.processed_bars == 0:
            sink.write_equity_point(
                EquityCurvePoint(
                    time=runtime.last_bar.end_time if runtime.last_bar is not None else zero_time(),
                    equity=self._initial_cash,
                )
            )
        processed_bar_count = runtime.processed_bars
        run_id_value, report_hash, _, artifacts = writer.finalize(
            config_hash=config_hash,
            dataset_metadata=tuple(
                dataset_metadata_payload(item) for item in self._dataset_metadata
            ),
            cost_model=self._cost_model.to_payload(),
            processed_bars=processed_bar_count,
            warmup_bars=runtime.warmup_bars,
            trading_bars=runtime.trading_bars,
            final_cash=runtime.final_account.cash["USD"],
            strategy_version=self._strategy_version,
        )
        return BacktestStreamResult(
            processed_bars=processed_bar_count,
            warmup_bars=runtime.warmup_bars,
            trading_bars=runtime.trading_bars,
            final_account=runtime.final_account,
            run_id=BacktestRunId(run_id_value),
            strategy_version=self._strategy_version,
            config_hash=config_hash,
            dataset_metadata=self._dataset_metadata,
            cost_model=self._cost_model,
            report_hash=report_hash,
            manifest_path=artifacts.manifest_path,
            artifact_paths=artifacts.artifact_paths,
            artifact_rows=artifacts.artifact_rows,
            artifact_hashes=artifacts.artifact_hashes,
        )


__all__ = [
    "BacktestCostModel",
    "BacktestEngine",
    "BacktestStreamResult",
    "SignalAggregatorActor",
    "StrategyActor",
    "StrategyBarEvent",
    "StrategyBarResult",
    "StrategyFinalize",
    "StrategyFinalized",
    "AggregatedSignalBatch",
    "StrategySignalEvent",
]
