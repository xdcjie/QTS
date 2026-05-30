"""Backtest engine."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import tzinfo
from decimal import Decimal
from typing import Any, cast

from qts.backtest.actor_loop import BacktestActorLoop
from qts.backtest.dependencies import (
    BacktestActorLoopConfig,
    BacktestActorLoopDependencies,
    BacktestEngineDependencies,
)
from qts.backtest.instrument_context import BacktestInstrumentContext
from qts.backtest.portfolio_projection import BacktestPortfolioProjector
from qts.core.hashing import stable_json_hash
from qts.core.ids import (
    AccountId,
    BrokerId,
    InstrumentId,
    RuntimeRunId,
    StrategyId,
)
from qts.data.provenance import DatasetMetadata
from qts.data.sessions import RegularSessionWindow
from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar
from qts.execution.adapters.brokerage_capabilities import broker_capabilities_for_model
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.observability.metrics import MetricsRegistry
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.reporting.backtest import (
    BacktestArtifactWriter,
    EquityCurvePoint,
    dataset_metadata_payload,
    zero_time,
)
from qts.risk.config import RiskRuleConfig, RiskRuleName
from qts.risk.margin.calculator import MarginCalculator
from qts.risk.risk_engine import RiskEngine
from qts.risk.rule_registry import RiskRuleRegistry
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.config import BacktestCostModel, BacktestEngineConfig, BacktestRuntimeConfig
from qts.runtime.intent_processing import TargetIntentProcessor
from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
from qts.runtime.sinks.base import RuntimeEventContext
from qts.runtime.topology import RuntimeTopologyBuilder
from qts.strategy_sdk import Strategy


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

    def __init__(
        self,
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
        cost_model: BacktestCostModel | None = None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None = None,
        future_roll_registry: FutureRollRegistry | None = None,
        warmup_bars: int = 0,
        target_timeframe: str | None = None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None,
        session_window_by_instrument: Mapping[InstrumentId, RegularSessionWindow] | None = None,
        instrument_registry: InstrumentRegistry | None = None,
        backtest_runtime_config: BacktestRuntimeConfig | None = None,
        execution_timing: ExecutionTimingModel | None = None,
    ) -> None:
        """Create an engine from explicit config and dependency objects.

        Keyword arguments are normalized into ``BacktestEngineConfig`` and
        ``BacktestEngineDependencies`` when explicit objects are not supplied.

        ``execution_timing`` selects the fill-timing policy. It defaults to the
        promotion-grade next-obtainable (``next_bar_open``) model. Supply
        ``ExecutionTimingModel.research_only()`` for the optimistic look-ahead
        ``same_bar_close`` model, which requires an explicit optimistic waiver
        and is never promotion-grade.
        """
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
        self._strategies = strategy_set
        self._strategy = strategy_set[0]
        self._backtest_runtime_config = backtest_runtime_config
        if instrument_registry is None and isinstance(bars, Sequence):
            self._registry_bars = tuple(bars)
            self._bars = iter(self._registry_bars)
        else:
            self._registry_bars = ()
            self._bars = iter(bars)

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
                cost_model=cost_model or BacktestCostModel(),
            )
        elif initial_cash is not None and Decimal(str(initial_cash)) != engine_config.initial_cash:
            raise ValueError("initial_cash must match engine_config.initial_cash")

        if not engine_config.strategy_version:
            engine_config = BacktestEngineConfig(
                initial_cash=engine_config.initial_cash,
                warmup_bars=engine_config.warmup_bars,
                target_timeframe=engine_config.target_timeframe,
                strategy_version=self._strategy.__class__.__qualname__,
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
                session_window_by_instrument=session_window_by_instrument,
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
        self._session_window_by_instrument = dict(dependencies.session_window_by_instrument)
        self._risk_engine = dependencies.risk_engine
        self._execution_adapter = dependencies.execution_adapter or SimulatedExecutionAdapter(
            self._cost_model,
            capabilities=broker_capabilities_for_model(
                self._backtest_runtime_config.brokerage_model
                if self._backtest_runtime_config is not None
                else "CUSTOM"
            ),
        )
        self._execution_timing = execution_timing or ExecutionTimingModel()
        self._instrument_context = BacktestInstrumentContext(
            future_roll_registry=self._future_roll_registry,
            instrument_registry=dependencies.instrument_registry,
            registry_bars=self._registry_bars,
            contract_multipliers=self._contract_multipliers,
            execution_timing=self._execution_timing,
        )
        self._portfolio_projector = BacktestPortfolioProjector(
            contract_multipliers=self._contract_multipliers
        )
        self._intent_processor = TargetIntentProcessor(
            risk_engine=self._risk_engine,
            instrument_context=self._instrument_context,
            multiplier_for=self._portfolio_projector.multiplier_for,
            broker_id=self._backtest_broker_id(),
            margin_calculator=dependencies.margin_calculator,
        )

    def _backtest_broker_id(self) -> BrokerId:
        capabilities = getattr(self._execution_adapter, "capabilities", None)
        if capabilities is None:
            return BrokerId("simulated")
        broker_id = capabilities.broker_id
        if isinstance(broker_id, BrokerId):
            return broker_id
        return BrokerId(str(broker_id))

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
        margin_rate = cls._resolved_initial_margin_rate(instrument_registry)
        risk_engine = RiskEngine(
            list(
                RiskRuleRegistry().build_all(
                    cls._risk_rule_configs(
                        max_notional=config.risk_config.max_notional,
                        margin_enabled=margin_rate is not None,
                    )
                )
            )
        )
        margin_calculator = (
            MarginCalculator(initial_margin_rate=margin_rate, maintenance_margin_rate=margin_rate)
            if margin_rate is not None
            else None
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
        if execution_timing is None:
            execution_timing = ExecutionTimingModel.from_value(
                config.fill_policy,
                optimistic_waiver=config.optimistic_fill_waiver,
            )
        return cls(
            strategy=strategy,
            strategies=strategies,
            bars=bars,
            engine_config=engine_config,
            dependencies=dependencies,
            backtest_runtime_config=config,
            execution_timing=execution_timing,
        )

    @staticmethod
    def _risk_rule_configs(
        *,
        max_notional: Decimal,
        margin_enabled: bool,
    ) -> tuple[RiskRuleConfig, ...]:
        """Return the config-driven risk rule set for a backtest run.

        ``MaxNotionalRule`` is always present (the historical default). The
        per-contract margin gate is appended only when a margin rate is
        resolvable from the instrument registry, so runs without a configured
        margin rate behave exactly as before (no fail-closed margin rejection).
        """
        configs = [
            RiskRuleConfig(
                rule_id="max_notional",
                name=RiskRuleName.MAX_NOTIONAL,
                params={"max_notional": max_notional},
            )
        ]
        if margin_enabled:
            configs.append(
                RiskRuleConfig(rule_id="margin_limit", name=RiskRuleName.MARGIN_LIMIT, params={})
            )
        return tuple(configs)

    @staticmethod
    def _resolved_initial_margin_rate(
        instrument_registry: InstrumentRegistry | None,
    ) -> Decimal | None:
        """Resolve a single account-wide initial-margin rate from the registry.

        The margin rate is a per-contract product fact owned by ``ContractSpec``.
        Returns ``None`` when no registered instrument configures a rate (margin
        enforcement stays disabled). When more than one distinct rate is
        configured the run is rejected, because the account-wide
        ``MarginCalculator`` cannot represent conflicting per-contract rates;
        this fails closed on misconfiguration rather than silently picking one.
        """
        if instrument_registry is None:
            return None
        rates = {
            spec.initial_margin_rate
            for spec in instrument_registry.contract_specs()
            if spec.initial_margin_rate is not None
        }
        if not rates:
            return None
        if len(rates) > 1:
            raise ValueError(
                "multiple distinct initial_margin_rate values configured; "
                "the account-wide margin gate requires a single rate"
            )
        return rates.pop()

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
        strategy_id: StrategyId | None = StrategyId("strategy")
        account_id = AccountId("acct-backtest")
        strategy_specs = None
        if self._backtest_runtime_config is not None:
            runtime_topology = RuntimeTopologyBuilder.from_backtest_config(
                self._backtest_runtime_config,
                runtime_run_id,
            )
            runtime_topology_payload = runtime_topology.to_manifest_payload()
            strategy_specs = runtime_topology.strategies
            if runtime_topology.accounts:
                account_id = runtime_topology.accounts[0].account_id
            if len(runtime_topology.strategies) == 1:
                strategy_id = runtime_topology.strategies[0].strategy_id
            elif runtime_topology.strategies:
                strategy_id = None
        else:
            runtime_topology_payload = self._default_runtime_topology_payload(
                runtime_run_id=runtime_run_id,
                account_id=account_id,
                strategy_id=strategy_id or StrategyId("strategy"),
            )
        writer = BacktestArtifactWriter(
            output_dir,
            run_id=runtime_run_id,
            compact_events=compact_events,
        )
        sink = BacktestRuntimeEventSink(
            writer,
            context=RuntimeEventContext(
                run_id=runtime_run_id,
                mode="backtest",
                execution_environment="simulated",
                account_id=account_id,
                strategy_id=strategy_id,
            ),
            metrics=metrics,
        )
        actor_loop = BacktestActorLoop(
            strategies=self._strategies,
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
                session_window_by_instrument=self._session_window_by_instrument,
                execution_adapter=self._execution_adapter,
                process_intent=self._intent_processor.process_intent,
                portfolio_view=self._portfolio_projector.portfolio_view,
                equity_point=self._portfolio_projector.equity_point,
                update_rolling_prices=self._instrument_context.update_rolling_prices,
                market_data_provenance_for=self._market_data_provenance_for,
                execution_timing=self._execution_timing,
            ),
            strategy_id=strategy_id,
            account_id=account_id,
            strategy_specs=strategy_specs,
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
        brokerage_model = (
            self._backtest_runtime_config.brokerage_model
            if self._backtest_runtime_config is not None
            else "CUSTOM"
        )
        run_id_value, report_hash, _, artifacts = writer.finalize(
            config_hash=config_hash,
            dataset_metadata=self._manifest_dataset_metadata_payloads(),
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
        payload = getattr(self._execution_adapter, "execution_assumptions_payload", None)
        if payload is None:
            return dict(timing_payload)
        assumptions = cast(dict[str, Any], payload())
        assumptions.update(timing_payload)
        return assumptions

    def _manifest_dataset_metadata_payloads(self) -> tuple[dict[str, Any], ...]:
        """Return dataset provenance rows with the M1 manifest aliases."""
        first_ts, last_ts = self._dataset_time_bounds()
        if self._dataset_metadata:
            return tuple(
                self._enrich_dataset_manifest_payload(
                    dataset_metadata_payload(item),
                    first_ts=first_ts,
                    last_ts=last_ts,
                )
                for item in self._dataset_metadata
            )
        return (self._inline_dataset_manifest_payload(first_ts=first_ts, last_ts=last_ts),)

    def _dataset_time_bounds(self) -> tuple[str | None, str | None]:
        start = self._config_hash_payload.get("start")
        end = self._config_hash_payload.get("end")
        if isinstance(start, str) and isinstance(end, str):
            return start, end
        if self._registry_bars:
            return (
                min(bar.start_time for bar in self._registry_bars).isoformat(),
                max(bar.end_time for bar in self._registry_bars).isoformat(),
            )
        return None, None

    @staticmethod
    def _enrich_dataset_manifest_payload(
        payload: dict[str, Any],
        *,
        first_ts: str | None,
        last_ts: str | None,
    ) -> dict[str, Any]:
        enriched = dict(payload)
        if first_ts is not None:
            enriched.setdefault("first_ts", first_ts)
        if last_ts is not None:
            enriched.setdefault("last_ts", last_ts)
        return enriched

    def _inline_dataset_manifest_payload(
        self,
        *,
        first_ts: str | None,
        last_ts: str | None,
    ) -> dict[str, Any]:
        row_count = len(self._registry_bars)
        source_payload = [
            {
                "instrument_id": bar.instrument_id.value,
                "timeframe": bar.timeframe,
                "start_time": bar.start_time.isoformat(),
                "end_time": bar.end_time.isoformat(),
                "open": str(bar.open),
                "high": str(bar.high),
                "low": str(bar.low),
                "close": str(bar.close),
                "volume": str(bar.volume) if bar.volume is not None else None,
            }
            for bar in self._registry_bars
        ]
        file_hash = stable_json_hash(source_payload)
        return {
            "dataset_id": "inline-bars",
            "source": "inline",
            "instrument_id": "MULTI",
            "timeframe": self._target_timeframe or "source",
            "timezone": "UTC",
            "timezone_policy": "UTC",
            "adjustment_mode": "none",
            "adjustment_policy": "none",
            "normalization_version": "inline-bars-v1",
            "created_at": first_ts or zero_time().isoformat(),
            "content_hash": file_hash,
            "file_hash": file_hash,
            "row_count": row_count,
            "first_ts": first_ts or zero_time().isoformat(),
            "last_ts": last_ts or zero_time().isoformat(),
        }

    @staticmethod
    def _default_runtime_topology_payload(
        *,
        runtime_run_id: RuntimeRunId,
        account_id: AccountId,
        strategy_id: StrategyId,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "run_id": runtime_run_id.value,
            "mode": "backtest",
            "accounts": [{"account_id": account_id.value}],
            "strategies": [{"strategy_id": strategy_id.value, "account_id": account_id.value}],
            "broker_routes": [],
            "market_data_routes": [],
        }
        payload["topology_hash"] = stable_json_hash(payload)
        return payload

    def _market_data_provenance_for(self, bar: Bar) -> dict[str, str | int | None]:
        """Return replay provenance for a market-data runtime event."""
        candidates = [
            metadata for metadata in self._dataset_metadata if metadata.timeframe == bar.timeframe
        ]
        for metadata in candidates:
            if metadata.instrument_id == bar.instrument_id and metadata.timeframe == bar.timeframe:
                return self._dataset_provenance_payload(metadata)
        if len(candidates) == 1:
            return self._dataset_provenance_payload(candidates[0])
        return {}

    @staticmethod
    def _dataset_provenance_payload(metadata: DatasetMetadata) -> dict[str, str | int | None]:
        """Serialize dataset metadata for a runtime market-data event."""
        return {
            "source_id": metadata.source,
            "dataset_id": metadata.dataset_id,
            "provider": metadata.source,
            "permission_state": None,
            "adjustment_mode": metadata.adjustment_policy,
            "content_hash": metadata.content_hash,
            "row_count": metadata.row_count,
        }


__all__ = [
    "BacktestCostModel",
    "BacktestEngine",
    "BacktestStreamResult",
]
