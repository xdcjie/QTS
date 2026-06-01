"""Backtest engine."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import tzinfo
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from qts.backtest.actor_loop import BacktestActorLoop
from qts.backtest.artifacts import BacktestArtifactService
from qts.backtest.dependencies import (
    BacktestActorLoopConfig,
    BacktestActorLoopDependencies,
)
from qts.backtest.engine_assembly import BacktestEngineAssembler
from qts.backtest.run_plan import BacktestRunPlan
from qts.backtest.runtime_manifest import BacktestRuntimeTopologyManifestBuilder
from qts.core.hashing import stable_json_hash
from qts.core.ids import (
    AccountId,
    InstrumentId,
    RuntimeRunId,
    StrategyId,
)
from qts.data.provenance import DatasetMetadata
from qts.data.sessions import RegularSessionWindow
from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar
from qts.observability.metrics import MetricsRegistry
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.config import BacktestCostModel, BacktestRuntimeConfig
from qts.strategy_sdk import Strategy

if TYPE_CHECKING:
    from qts.runtime.actors.account_actor import AccountSnapshot


@dataclass(frozen=True, slots=True)
class BacktestStreamResult:
    """Backtest result written to partitioned streaming artifacts."""

    processed_bars: int
    warmup_bars: int
    trading_bars: int
    final_account: AccountSnapshot
    run_id: RuntimeRunId
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

    def __init__(self, plan: BacktestRunPlan) -> None:
        """Create an engine from a normalized run plan.

        Callers that still hold legacy keyword inputs must normalize them with
        ``BacktestRunPlan.from_inputs(...)`` before constructing the engine.

        ``execution_timing`` selects the fill-timing policy. It defaults to the
        promotion-grade next-obtainable (``next_bar_open``) model. Supply
        ``ExecutionTimingModel.research_only()`` for the optimistic look-ahead
        ``same_bar_close`` model, which requires an explicit optimistic waiver
        and is never promotion-grade.
        """
        self._strategies = plan.strategies
        self._strategy = plan.strategies[0]
        self._backtest_runtime_config = plan.backtest_runtime_config
        self._registry_bars = plan.registry_bars
        self._bars = iter(plan.bars)

        self._config = plan.engine_config
        self._initial_cash = plan.engine_config.initial_cash
        self._dataset_metadata = plan.engine_config.dataset_metadata
        self._config_hash_payload = plan.engine_config.config_payload
        self._strategy_version = plan.engine_config.strategy_version
        self._cost_model = plan.engine_config.cost_model
        self._contract_multipliers = dict(plan.dependencies.contract_multipliers)
        self._future_roll_registry = plan.dependencies.future_roll_registry
        self._warmup_bars = plan.engine_config.warmup_bars
        self._target_timeframe = plan.engine_config.target_timeframe
        self._exchange_timezone_by_instrument = dict(
            plan.dependencies.exchange_timezone_by_instrument
        )
        self._session_window_by_instrument = dict(plan.dependencies.session_window_by_instrument)
        self._risk_engine = plan.dependencies.risk_engine
        collaborators = BacktestEngineAssembler().collaborators(
            engine_config=plan.engine_config,
            dependencies=plan.dependencies,
            registry_bars=self._registry_bars,
            backtest_runtime_config=plan.backtest_runtime_config,
            execution_timing=plan.execution_timing,
        )
        self._execution_adapter = collaborators.execution_adapter
        self._execution_timing = collaborators.execution_timing
        self._instrument_context = collaborators.instrument_context
        self._portfolio_projector = collaborators.portfolio_projector
        self._intent_processor = collaborators.intent_processor
        self._dataset_manifest_builder = collaborators.dataset_manifest_builder

    @classmethod
    def from_config(
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
    ) -> BacktestEngine:
        """Build an engine from a serialized backtest run config.

        The fill-timing policy is recorded in the run manifest. An explicit
        ``execution_timing`` argument wins (used by direct callers). Otherwise
        it is derived from the config's ``fill_policy`` / ``optimistic_fill_waiver``
        fields, which default to the promotion-grade ``next_bar_open``. A config
        selecting the optimistic ``same_bar_close`` policy must set
        ``optimistic_fill_waiver: true``; the manifest's ``promotion_grade`` flag
        then records that such a run may not back paper/live evidence.
        """
        return cls.from_run_plan(
            BacktestRunPlan.from_runtime_config(
                config,
                bars=bars,
                strategy=strategy,
                strategies=strategies,
                instrument_registry=instrument_registry,
                dataset_metadata=dataset_metadata,
                future_roll_registry=future_roll_registry,
                exchange_timezone_by_instrument=exchange_timezone_by_instrument,
                session_window_by_instrument=session_window_by_instrument,
                contract_multipliers=contract_multipliers,
                execution_timing=execution_timing,
            )
        )

    @classmethod
    def from_run_plan(cls, run_plan: BacktestRunPlan) -> BacktestEngine:
        """Build an engine from a normalized backtest run plan."""

        return cls(run_plan)

    def run_streaming(
        self,
        output_dir: Any,
        *,
        metrics: MetricsRegistry | None = None,
        compact_events: bool = False,
    ) -> BacktestStreamResult:
        """Run the backtest and write streaming artifacts.

        When ``metrics`` is supplied, every event written through the
        backtest sink is classified into the canonical counter set so
        external Prometheus scrapes against the same registry see populated
        data without a separate poller.

        ``compact_events`` opts into dropping per-bar ``runtime.market_data``
        and ``runtime.account_snapshot`` events from ``events.ndjson`` to
        shrink long-run artifacts (~30x reduction on multi-year backtests).
        Default ``False`` for forensic completeness; CLI / pipeline entry
        points (``qts.backtest.runner.run_backtest`` and the optimizer
        runners) opt in.
        """
        config_hash = stable_json_hash(self._config_hash_payload)
        runtime_run_id = RuntimeRunId(f"bt-{config_hash.removeprefix('sha256:')[:12]}")
        resolved_topology = BacktestRuntimeTopologyManifestBuilder().resolve(
            backtest_runtime_config=self._backtest_runtime_config,
            runtime_run_id=runtime_run_id,
            default_account_id=AccountId("acct-backtest"),
            default_strategy_id=StrategyId("strategy"),
        )
        runtime_topology_payload = resolved_topology.payload
        account_id = resolved_topology.account_id
        strategy_id = resolved_topology.strategy_id
        strategy_specs = resolved_topology.strategy_specs
        artifact_service = BacktestArtifactService(
            output_dir,
            run_id=runtime_run_id,
            account_id=account_id,
            strategy_id=strategy_id,
            compact_events=compact_events,
            metrics=metrics,
        )
        actor_loop = BacktestActorLoop(
            strategies=self._strategies,
            bars=self._bars,
            config=BacktestActorLoopConfig(
                initial_cash=self._initial_cash,
                target_timeframe=self._target_timeframe,
                warmup_bars=self._warmup_bars,
                initial_cash_by_account=resolved_topology.initial_cash_by_account,
            ),
            dependencies=BacktestActorLoopDependencies(
                instrument_registry=self._instrument_context.instrument_registry(),
                future_roll_registry=self._future_roll_registry,
                contract_multipliers=self._contract_multipliers,
                exchange_timezone_by_instrument=self._exchange_timezone_by_instrument,
                session_window_by_instrument=self._session_window_by_instrument,
                execution_adapter=self._execution_adapter,
                process_intent=self._intent_processor.process_intent,
                portfolio_view=self._portfolio_projector.portfolio_view,
                equity_point=self._portfolio_projector.equity_point,
                update_rolling_prices=self._instrument_context.update_rolling_prices,
                market_data_provenance_for=self._dataset_manifest_builder.market_data_provenance_for,
                execution_timing=self._execution_timing,
            ),
            strategy_id=strategy_id,
            account_id=account_id,
            strategy_specs=strategy_specs,
        )
        runtime = actor_loop.run(
            sink=artifact_service.sink,
            prune_history=True,
            compact_orders=True,
        )

        if runtime.processed_bars == 0:
            artifact_service.record_empty_run_equity(
                equity=self._initial_cash,
                last_bar_end_time=(
                    runtime.last_bar.end_time if runtime.last_bar is not None else None
                ),
            )
        processed_bar_count = runtime.processed_bars
        brokerage_model = (
            self._backtest_runtime_config.brokerage_model
            if self._backtest_runtime_config is not None
            else "CUSTOM"
        )
        run_id_value, report_hash, _, artifacts = artifact_service.finalize(
            config_hash=config_hash,
            dataset_metadata=self._dataset_manifest_builder.manifest_dataset_metadata_payloads(),
            cost_model=self._cost_model.to_payload(),
            processed_bars=processed_bar_count,
            warmup_bars=runtime.warmup_bars,
            trading_bars=runtime.trading_bars,
            final_cash=runtime.final_account.cash["USD"],
            strategy_version=self._strategy_version,
            runtime_topology_payload=runtime_topology_payload,
            brokerage_model=brokerage_model,
            execution_assumptions=self._execution_assumptions_payload(),
            risk_config_hash=stable_json_hash(self._config_hash_payload.get("risk_config", {})),
        )
        return BacktestStreamResult(
            processed_bars=processed_bar_count,
            warmup_bars=runtime.warmup_bars,
            trading_bars=runtime.trading_bars,
            final_account=runtime.final_account,
            run_id=RuntimeRunId(run_id_value),
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

    def _execution_assumptions_payload(self) -> dict[str, Any] | None:
        """Return simulated execution assumptions enriched with the fill policy.

        The fill-timing model is always recorded so the manifest captures
        whether fills used the next-obtainable price (``next_bar_open``) or the
        optimistic same-bar close, and whether an optimistic waiver was set.
        """
        timing_payload = self._execution_timing.to_manifest_payload()
        assumptions = self._execution_adapter.execution_assumptions_payload()
        assumptions.update(timing_payload)
        return assumptions


__all__ = [
    "BacktestCostModel",
    "BacktestEngine",
    "BacktestRunPlan",
    "BacktestStreamResult",
]
