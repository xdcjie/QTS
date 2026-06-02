"""Backtest engine collaborator assembly.

Owns construction of the runtime collaborators the backtest engine orchestrates
(execution adapter, instrument context, portfolio projector, intent processor,
dataset manifest builder) and the translation of a serialized
``BacktestRuntimeConfig`` into engine config + dependencies. Keeping this wiring
here lets ``BacktestEngine`` stay a thin orchestrator that validates its inputs
and delegates, rather than owning collaborator construction and risk-policy
resolution inline.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import tzinfo
from decimal import Decimal
from typing import TYPE_CHECKING

from qts.backtest.dependencies import BacktestEngineDependencies
from qts.backtest.instrument_context import BacktestInstrumentContext
from qts.backtest.portfolio_projection import BacktestPortfolioProjector
from qts.backtest.provenance import BacktestDatasetManifestBuilder
from qts.backtest.risk_policy import BacktestRiskPolicyFactory
from qts.core.ids import BrokerId, InstrumentId
from qts.data.provenance import DatasetMetadata
from qts.data.sessions import RegularSessionWindow
from qts.domain.execution_costs import SimulatedExecutionCostModel
from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar
from qts.execution.adapters.brokerage_capabilities import broker_capabilities_for_model
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.config import BacktestEngineConfig, BacktestRuntimeConfig
from qts.runtime.intent_processing import TargetIntentProcessor

if TYPE_CHECKING:
    from qts.execution.execution_adapter import ExecutionEvidenceProvider


@dataclass(frozen=True, slots=True)
class BacktestEngineCollaborators:
    """Runtime collaborators the backtest engine orchestrates over replay bars."""

    execution_adapter: ExecutionEvidenceProvider
    execution_timing: ExecutionTimingModel
    instrument_context: BacktestInstrumentContext
    portfolio_projector: BacktestPortfolioProjector
    intent_processor: TargetIntentProcessor
    dataset_manifest_builder: BacktestDatasetManifestBuilder


class BacktestEngineAssembler:
    """Build the engine's collaborators and translate runtime config into inputs."""

    def collaborators(
        self,
        *,
        engine_config: BacktestEngineConfig,
        dependencies: BacktestEngineDependencies,
        registry_bars: tuple[Bar, ...],
        backtest_runtime_config: BacktestRuntimeConfig | None,
        execution_timing: ExecutionTimingModel | None,
    ) -> BacktestEngineCollaborators:
        """Construct the runtime collaborators bound to one engine's config."""
        brokerage_model = (
            backtest_runtime_config.brokerage_model
            if backtest_runtime_config is not None
            else "CUSTOM"
        )
        execution_adapter: ExecutionEvidenceProvider = (
            dependencies.execution_adapter
            or SimulatedExecutionAdapter(
                engine_config.cost_model,
                capabilities=broker_capabilities_for_model(brokerage_model),
            )
        )
        resolved_timing = execution_timing or ExecutionTimingModel()
        contract_multipliers = dict(dependencies.contract_multipliers)
        instrument_context = BacktestInstrumentContext(
            future_roll_registry=dependencies.future_roll_registry,
            instrument_registry=dependencies.instrument_registry,
            registry_bars=registry_bars,
            contract_multipliers=contract_multipliers,
            execution_timing=resolved_timing,
        )
        portfolio_projector = BacktestPortfolioProjector(contract_multipliers=contract_multipliers)
        broker_id = self._broker_id(execution_adapter)
        intent_processor = TargetIntentProcessor(
            risk_engine=dependencies.risk_engine,
            instrument_context=instrument_context,
            multiplier_for=portfolio_projector.multiplier_for,
            broker_id=broker_id,
            margin_calculator=dependencies.margin_calculator,
        )
        dataset_manifest_builder = BacktestDatasetManifestBuilder(
            dataset_metadata=engine_config.dataset_metadata,
            registry_bars=registry_bars,
            config_hash_payload=engine_config.config_payload,
            target_timeframe=engine_config.target_timeframe,
        )
        return BacktestEngineCollaborators(
            execution_adapter=execution_adapter,
            execution_timing=resolved_timing,
            instrument_context=instrument_context,
            portfolio_projector=portfolio_projector,
            intent_processor=intent_processor,
            dataset_manifest_builder=dataset_manifest_builder,
        )

    def runtime_config_inputs(
        self,
        config: BacktestRuntimeConfig,
        *,
        dataset_metadata: Iterable[DatasetMetadata],
        instrument_registry: InstrumentRegistry | None,
        future_roll_registry: FutureRollRegistry | None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None,
        session_window_by_instrument: Mapping[InstrumentId, RegularSessionWindow] | None,
        execution_timing: ExecutionTimingModel | None,
    ) -> tuple[BacktestEngineConfig, BacktestEngineDependencies, ExecutionTimingModel]:
        """Translate a serialized run config into engine config + dependencies.

        The fill-timing policy is derived from the config's ``fill_policy`` /
        ``optimistic_fill_waiver`` fields (default promotion-grade
        ``next_bar_open``) unless an explicit ``execution_timing`` wins.
        """
        cost_model = SimulatedExecutionCostModel(
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
        risk_engine, margin_calculator = BacktestRiskPolicyFactory().build(
            max_notional=config.risk_config.max_notional,
            instrument_registry=instrument_registry,
        )
        dependencies = BacktestEngineDependencies.with_defaults(
            initial_cash=config.initial_cash,
            risk_engine=risk_engine,
            instrument_registry=instrument_registry,
            future_roll_registry=future_roll_registry,
            contract_multipliers=contract_multipliers,
            exchange_timezone_by_instrument=exchange_timezone_by_instrument,
            session_window_by_instrument=session_window_by_instrument,
            margin_calculator=margin_calculator,
        )
        resolved_timing = execution_timing or ExecutionTimingModel.from_value(
            config.fill_policy,
            optimistic_waiver=config.optimistic_fill_waiver,
        )
        return engine_config, dependencies, resolved_timing

    @staticmethod
    def _broker_id(execution_adapter: ExecutionEvidenceProvider) -> BrokerId:
        capabilities = execution_adapter.capabilities
        broker_id = capabilities.broker_id
        if isinstance(broker_id, BrokerId):
            return broker_id
        return BrokerId(str(broker_id))


__all__ = ["BacktestEngineAssembler", "BacktestEngineCollaborators"]
