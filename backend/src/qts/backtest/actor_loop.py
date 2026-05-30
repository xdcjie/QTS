"""Streaming backtest actor loop."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Protocol, TypeAlias

from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
from qts.core.ids import AccountId, CorrelationId, InstrumentId, StrategyId
from qts.domain.market_data import Bar
from qts.domain.orders import Order, OrderFill
from qts.reporting.backtest import (
    EquityCurvePoint,
    broker_capability_payload,
    is_broker_capability_reject,
)
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import (
    AccountActor,
    AccountSnapshot,
    DrainPositionClosedEvents,
    GetAccountSnapshot,
)
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import (
    CompactForStreaming,
    OrderManagerActor,
)
from qts.runtime.actors.signal_aggregator_actor import (
    AggregatedSignalBatch,
    SignalContribution,
    StrategySignalEvent,
)
from qts.runtime.broker_runtime_topology import StrategyRuntimeBinding
from qts.runtime.intent_processing import ProcessedIntent
from qts.runtime.mailbox import Mailbox
from qts.runtime.market_data_flow import MarketDataFlow
from qts.runtime.order_lifecycle import CancelIntentRouter
from qts.runtime.runtime_event_writer import RuntimeEventWriter
from qts.runtime.signal_policy import SignalAggregationPolicy
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.strategy_execution_pipeline import (
    StrategyExecutionPipeline,
    StrategyExecutionResult,
)
from qts.runtime.topology import StrategyRuntimeSpec
from qts.strategy_sdk import PortfolioView, Strategy


class BacktestRuntimeSink(Protocol):
    """Minimal backtest sink contract used by the actor loop."""

    @property
    def order_count(self) -> int:
        """Return total processed orders."""

    def write(self, event: RuntimeEvent) -> object:
        """Write one normalized runtime event."""

    def write_processed(
        self,
        *,
        orders: tuple[Order, ...],
        fills: tuple[OrderFill, ...],
        bar: Bar,
    ) -> None:
        """Record processed orders and fills."""

    def write_equity_point(self, point: EquityCurvePoint) -> None:
        """Record per-bar equity point."""

    def write_holdings_snapshot(
        self,
        *,
        gross_notional: Decimal,
        net_notional: Decimal,
    ) -> None:
        """Record one per-bar holdings notional snapshot."""


ProcessIntentHandler = Callable[..., ProcessedIntent]
PortfolioViewBuilder = Callable[..., PortfolioView]
EquityPointBuilder = Callable[..., EquityCurvePoint]
RollingPriceUpdater = Callable[..., None]


@dataclass(frozen=True, slots=True)
class PendingFill:
    """An accepted intent whose fill is deferred to the next bar (next_bar_open).

    The decision was made at the close of ``decision_bar``; under the
    ``next_bar_open`` fill policy it must execute against the next strategy-
    facing bar for the same instrument. ``correlation_id`` and ``batch`` carry
    the originating decision's traceability so the deferred order/fill events
    still link back to the bar that produced the intent.
    """

    intent: Any
    batch: AggregatedSignalBatch
    correlation_id: CorrelationId
    decision_bar: Bar


@dataclass(frozen=True, slots=True)
class BacktestActorLoopResult:
    """Result summary produced by an actor loop run."""

    final_account: AccountSnapshot
    warmup_bars: int
    trading_bars: int
    last_bar: Bar | None

    @property
    def processed_bars(self) -> int:
        """Perform processed_bars."""
        return self.warmup_bars + self.trading_bars


BacktestActorLoopState: TypeAlias = SimpleNamespace
BacktestStrategyExecution: TypeAlias = tuple[StrategyRuntimeBinding, StrategyExecutionResult]
BacktestStrategyBarExecution: TypeAlias = tuple[BacktestStrategyExecution, ...]


class BacktestActorLoop:
    """Run backtest bars through strategy/order execution actors."""

    def __init__(
        self,
        *,
        strategy: Strategy | None = None,
        strategies: Sequence[Strategy] | None = None,
        bars: Iterable[Bar],
        config: BacktestActorLoopConfig,
        dependencies: BacktestActorLoopDependencies,
        strategy_id: StrategyId | None = None,
        account_id: AccountId | None = None,
        strategy_specs: Sequence[StrategyRuntimeSpec] | None = None,
        signal_aggregation_policy: str = "sum_targets",
        signal_priority: int = 0,
        signal_weight: Decimal = Decimal("1"),
        conflict_group: str = "default",
    ) -> None:
        """Perform __init__."""
        if account_id is None:
            raise ValueError("account_id is required")
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
        self._bars = bars
        self._initial_cash = config.initial_cash
        self._target_timeframe = config.target_timeframe
        self._exchange_timezone_by_instrument = dict(dependencies.exchange_timezone_by_instrument)
        self._session_window_by_instrument = dict(dependencies.session_window_by_instrument)
        self._warmup_bars = config.warmup_bars
        self._instrument_registry = dependencies.instrument_registry
        self._future_roll_registry = dependencies.future_roll_registry
        self._contract_multipliers = dict(dependencies.contract_multipliers)
        self._execution_adapter = dependencies.execution_adapter
        self._process_intent = dependencies.process_intent
        self._portfolio_view = dependencies.portfolio_view
        self._equity_point = dependencies.equity_point
        self._update_rolling_prices = dependencies.update_rolling_prices
        self._market_data_provenance_for = dependencies.market_data_provenance_for
        self._execution_timing = dependencies.execution_timing
        self._account_id = account_id
        self._strategy_specs = self.normalize_strategy_specs(
            strategy_specs,
            strategy_id=strategy_id,
            account_id=account_id,
            signal_aggregation_policy=signal_aggregation_policy,
            signal_priority=signal_priority,
            signal_weight=signal_weight,
            conflict_group=conflict_group,
        )
        if len(self._strategy_specs) != len(self._strategies):
            raise ValueError("strategy spec count must match strategy instance count")
        strategy_account_ids = {spec.account_id for spec in self._strategy_specs}
        if strategy_account_ids != {account_id}:
            raise ValueError("backtest actor loop supports one account")
        if len(self._strategy_specs) > 1 and strategy_id is not None:
            raise ValueError("strategy_id must be omitted for multi-strategy backtests")
        self._strategy_id = (
            strategy_id
            if strategy_id is not None
            else self._strategy_specs[0].strategy_id
            if len(self._strategy_specs) == 1
            else None
        )
        self._signal_aggregation_policy = signal_aggregation_policy
        self._signal_priority = signal_priority
        self._signal_weight = Decimal(signal_weight)
        self._conflict_group = conflict_group

    @staticmethod
    def _resolve_actor_classes() -> tuple[type, type]:
        """Perform _resolve_actor_classes."""
        from qts.backtest import engine as engine_module

        strategy_actor = engine_module.StrategyActor
        signal_aggregator_actor = engine_module.SignalAggregatorActor
        return strategy_actor, signal_aggregator_actor

    def normalize_strategy_specs(
        self,
        strategy_specs: Sequence[StrategyRuntimeSpec] | None,
        *,
        strategy_id: StrategyId | None,
        account_id: AccountId,
        signal_aggregation_policy: str,
        signal_priority: int,
        signal_weight: Decimal,
        conflict_group: str,
    ) -> tuple[StrategyRuntimeSpec, ...]:
        """Return validated specs matching the injected strategy instances."""
        if strategy_specs is not None:
            return tuple(strategy_specs)
        if strategy_id is None:
            raise ValueError("strategy_id is required")
        return (
            StrategyRuntimeSpec(
                strategy_id=strategy_id,
                strategy_class=self._strategies[0].__class__.__qualname__,
                account_id=account_id,
                subscriptions=(),
                signal_aggregation_policy=signal_aggregation_policy,
                signal_priority=signal_priority,
                signal_weight=Decimal(signal_weight),
                conflict_group=conflict_group,
            ),
        )

    def run(
        self,
        *,
        sink: BacktestRuntimeSink,
        prune_history: bool,
        compact_orders: bool,
    ) -> BacktestActorLoopResult:
        """Run all bars through explicit initialization, bar, and final phases."""
        state = self.initialize_run_phase(
            sink=sink,
            prune_history=prune_history,
            compact_orders=compact_orders,
        )
        for source_bar in self._bars:
            self.process_market_data_phase(state, source_bar)
        return self.finalize_run_phase(state)

    def initialize_run_phase(
        self,
        *,
        sink: BacktestRuntimeSink,
        prune_history: bool,
        compact_orders: bool,
    ) -> BacktestActorLoopState:
        """Initialize actors, pipeline, market-data flow, and run state."""
        account_actor = AccountActor(
            initial_cash={"USD": self._initial_cash},
            account_id=self._account_id,
        )
        account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
        execution_mailbox = Mailbox()
        order_manager_mailbox = Mailbox()
        order_manager_actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=execution_mailbox),
            account_ref=account_ref,
            multiplier_by_instrument=self._contract_multipliers,
            account_id=self._account_id,
        )
        order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
        execution_ref = ActorRef(
            actor=ExecutionActor(
                order_manager_ref=order_manager_ref,
                execution_adapter=self._execution_adapter,
            ),
            mailbox=execution_mailbox,
        )
        event_writer = RuntimeEventWriter(write=sink.write)

        strategy_actor, signal_aggregator_actor = self._resolve_actor_classes()
        strategy_bindings = self.build_strategy_bindings(
            prune_history=prune_history,
            strategy_actor=strategy_actor,
            signal_aggregator_actor=signal_aggregator_actor,
        )
        signal_result_mailbox = Mailbox()
        signal_aggregator_ref = ActorRef(
            actor=signal_aggregator_actor(
                result_ref=ActorRef(mailbox=signal_result_mailbox),
            ),
            mailbox=Mailbox(),
        )
        target_timeframe = _strategy_subscription_target_timeframe(
            tuple(binding.pipeline for binding in strategy_bindings),
            fallback=self._target_timeframe,
        )

        market_data_flow = MarketDataFlow(
            target_timeframe=target_timeframe,
            exchange_timezone_by_instrument=self._exchange_timezone_by_instrument,
            session_window_by_instrument=self._session_window_by_instrument,
        )
        return BacktestActorLoopState(
            sink=sink,
            compact_orders=compact_orders,
            account_ref=account_ref,
            order_manager_ref=order_manager_ref,
            execution_ref=execution_ref,
            event_writer=event_writer,
            strategy_bindings=strategy_bindings,
            signal_aggregator_ref=signal_aggregator_ref,
            signal_result_mailbox=signal_result_mailbox,
            market_data_flow=market_data_flow,
            latest_prices={},
            pending_fills={},
            warmup_processed=0,
            trading_processed=0,
            event_index=0,
            last_bar=None,
        )

    def build_strategy_bindings(
        self,
        *,
        prune_history: bool,
        strategy_actor: type,
        signal_aggregator_actor: type,
    ) -> tuple[StrategyRuntimeBinding, ...]:
        """Build strategy execution pipelines from normalized backtest specs."""
        bindings: list[StrategyRuntimeBinding] = []
        for strategy, spec in zip(self._strategies, self._strategy_specs, strict=True):
            pipeline = StrategyExecutionPipeline(
                strategy=strategy,
                instrument_registry=self._instrument_registry,
                future_chain_registry=self._future_roll_registry,
                portfolio_view=self._portfolio_view,
                prune_history=prune_history,
                strategy_actor_type=strategy_actor,
                signal_aggregator_actor_type=signal_aggregator_actor,
                strategy_id=spec.strategy_id,
                signal_aggregation_policy=spec.signal_aggregation_policy,
                signal_priority=spec.signal_priority,
                signal_weight=spec.signal_weight,
                conflict_group=spec.conflict_group,
            )
            bindings.append(
                StrategyRuntimeBinding(
                    strategy_id=spec.strategy_id,
                    account_id=spec.account_id,
                    strategy=strategy,
                    subscriptions=tuple(spec.subscriptions),
                    enabled=spec.enabled,
                    signal_aggregation_policy=SignalAggregationPolicy(
                        spec.signal_aggregation_policy
                    ),
                    signal_priority=spec.signal_priority,
                    signal_weight=spec.signal_weight,
                    conflict_group=spec.conflict_group,
                    pipeline=pipeline,
                )
            )
        return tuple(bindings)

    def process_market_data_phase(
        self,
        state: BacktestActorLoopState,
        source_bar: Bar,
    ) -> None:
        """Convert one source bar into strategy-facing bar phases."""
        for bar in state.market_data_flow.publish_bar(source_bar):
            state.last_bar = bar
            correlation_id = self.market_data_correlation_id(bar)
            self.write_market_data_event(state, bar, correlation_id)
            self._update_rolling_prices(bar, latest_prices=state.latest_prices)
            self.flush_pending_fills(state, bar)
            strategy_result = self.execute_strategy_bar(state, bar, correlation_id)
            self.write_strategy_signal_events(state, strategy_result, correlation_id)
            self.route_strategy_cancels(state, strategy_result)
            if state.event_index < self._warmup_bars:
                self.process_warmup_phase(state, bar)
                continue
            self.process_trading_phase(state, bar, strategy_result, correlation_id)

    def flush_pending_fills(self, state: BacktestActorLoopState, bar: Bar) -> None:
        """Execute intents deferred to this bar under the ``next_bar_open`` policy.

        Deferred intents fill against the current bar's open before its
        strategy runs, mirroring live execution where a market order placed at
        the prior bar's close is filled by the time the next bar is observed.
        """
        pending = state.pending_fills.pop(bar.instrument_id, None)
        if not pending:
            return
        for deferred in pending:
            self.process_strategy_intent(
                state,
                bar,
                deferred.batch,
                deferred.intent,
                deferred.correlation_id,
            )

    def process_warmup_phase(self, state: BacktestActorLoopState, bar: Bar) -> None:
        """Record warmup accounting without submitting aggregated intents."""
        state.warmup_processed += 1
        self.write_equity_and_account_snapshot(state, bar)
        state.event_index += 1

    def process_trading_phase(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
        strategy_result: BacktestStrategyBarExecution,
        correlation_id: CorrelationId,
    ) -> None:
        """Process aggregated signals, order flow, and end-of-bar accounting."""
        signal_batches = self.aggregate_strategy_results(
            state,
            bar,
            strategy_result,
            correlation_id,
        )
        for batch in signal_batches:
            self.write_signal_batch_events(state, batch, correlation_id)
        for batch in signal_batches:
            for intent in batch.intents:
                if self._execution_timing.defers_to_next_bar:
                    self.defer_strategy_intent(state, bar, batch, intent, correlation_id)
                else:
                    self.process_strategy_intent(
                        state,
                        bar,
                        batch,
                        intent,
                        correlation_id,
                    )
        state.trading_processed += 1
        self.write_equity_and_account_snapshot(state, bar)
        state.event_index += 1

    def finalize_run_phase(self, state: BacktestActorLoopState) -> BacktestActorLoopResult:
        """Finalize the strategy pipeline and return the run summary."""
        for binding in state.strategy_bindings:
            _ = binding.pipeline.finalize()
        return BacktestActorLoopResult(
            final_account=state.account_ref.ask(GetAccountSnapshot()),
            warmup_bars=state.warmup_processed,
            trading_bars=state.trading_processed,
            last_bar=state.last_bar,
        )

    def market_data_correlation_id(self, bar: Bar) -> CorrelationId:
        """Create the stable correlation id for one strategy-facing bar."""
        return CorrelationId(
            f"md:{bar.instrument_id.value}:{bar.timeframe}:{bar.end_time.isoformat()}"
        )

    def write_market_data_event(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
        correlation_id: CorrelationId,
    ) -> None:
        """Update latest price state and emit the normalized market-data event."""
        state.latest_prices[bar.instrument_id] = bar.close
        market_data_payload: dict[str, object] = {
            "instrument_id": bar.instrument_id.value,
            "timeframe": bar.timeframe,
            "end_time": bar.end_time.isoformat(),
        }
        market_data_payload.update(self._market_data_provenance_for(bar))
        state.sink.write(
            RuntimeEvent(
                kind="runtime.market_data",
                payload=market_data_payload,
                correlation_id=correlation_id,
                instrument_id=bar.instrument_id,
            )
        )

    def execute_strategy_bar(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
        correlation_id: CorrelationId,
    ) -> BacktestStrategyBarExecution:
        """Execute every enabled strategy pipeline for one bar."""
        executions: list[BacktestStrategyExecution] = []
        single_binding = len(state.strategy_bindings) == 1
        for binding in state.strategy_bindings:
            if not binding.enabled:
                continue
            if (
                not single_binding
                and binding.subscriptions
                and bar.instrument_id not in binding.subscriptions
            ):
                continue
            result = binding.pipeline.execute_bar(
                bar,
                account_snapshot=state.account_ref.ask(GetAccountSnapshot()),
                latest_prices=state.latest_prices,
                aggregate_signals=False,
                account_id=self._account_id,
                correlation_id=correlation_id,
            )
            executions.append((binding, result))
        return tuple(executions)

    def aggregate_strategy_results(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
        strategy_result: BacktestStrategyBarExecution,
        correlation_id: CorrelationId,
    ) -> tuple[AggregatedSignalBatch, ...]:
        """Aggregate raw strategy intents across all backtest bindings."""
        contributions: list[SignalContribution] = []
        for binding, result in strategy_result:
            for intent in result.raw_intents:
                contributions.append(
                    SignalContribution(
                        strategy_id=binding.strategy_id,
                        intent=intent,
                        aggregation_policy=binding.signal_aggregation_policy,
                        priority=binding.signal_priority,
                        weight=binding.signal_weight,
                        conflict_group=binding.conflict_group,
                    )
                )
        if not contributions:
            return ()
        state.signal_aggregator_ref.tell(
            StrategySignalEvent(
                bar=bar,
                intents=tuple(contribution.intent for contribution in contributions),
                contributions=tuple(contributions),
                account_id=self._account_id,
                correlation_id=correlation_id,
            )
        )
        state.signal_aggregator_ref.process_all()
        return self.take_signal_batches(state)

    def take_signal_batches(
        self,
        state: BacktestActorLoopState,
    ) -> tuple[AggregatedSignalBatch, ...]:
        """Return all centralized signal aggregation batches for one bar."""
        batches: list[AggregatedSignalBatch] = []
        while not state.signal_result_mailbox.empty():
            result = state.signal_result_mailbox.get()
            if not isinstance(result, AggregatedSignalBatch):
                raise TypeError(f"unexpected signal aggregator result: {type(result).__name__}")
            batches.append(result)
        if not batches:
            raise RuntimeError("signal aggregator actor did not emit a batch")
        return tuple(batches)

    def write_strategy_signal_events(
        self,
        state: BacktestActorLoopState,
        strategy_result: BacktestStrategyBarExecution,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit raw strategy signal and intent events."""
        for execution in strategy_result:
            self.write_strategy_binding_signal_events(
                state,
                execution,
                correlation_id,
            )

    def write_strategy_binding_signal_events(
        self,
        state: BacktestActorLoopState,
        execution: BacktestStrategyExecution,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit raw strategy signal and intent events for one binding."""
        binding, result = execution
        for intent in result.raw_intents:
            signal_payload = {
                "instrument_id": intent.asset.instrument_id.value,
                "intent_type": intent.intent_type.value,
                "value": str(intent.value) if intent.value is not None else None,
                "aggregation_policy": binding.signal_aggregation_policy.value,
                "signal_weight": str(binding.signal_weight),
                "signal_priority": binding.signal_priority,
                "conflict_group": binding.conflict_group,
                "order_spec": intent.order_spec.to_payload(),
            }
            intent_payload = {
                "instrument_id": intent.asset.instrument_id.value,
                "intent_type": intent.intent_type.value,
                "value": str(intent.value) if intent.value is not None else None,
                "order_spec": intent.order_spec.to_payload(),
            }
            if intent.metadata:
                signal_payload["metadata"] = dict(intent.metadata)
                intent_payload["metadata"] = dict(intent.metadata)
            state.sink.write(
                RuntimeEvent(
                    kind="runtime.signal_received",
                    payload=signal_payload,
                    correlation_id=correlation_id,
                    instrument_id=intent.asset.instrument_id,
                    account_id=binding.account_id,
                    strategy_id=binding.strategy_id,
                )
            )
            state.sink.write(
                RuntimeEvent(
                    kind="runtime.strategy_intent",
                    payload=intent_payload,
                    correlation_id=correlation_id,
                    instrument_id=intent.asset.instrument_id,
                    account_id=binding.account_id,
                    strategy_id=binding.strategy_id,
                )
            )

    def route_strategy_cancels(
        self,
        state: BacktestActorLoopState,
        strategy_result: BacktestStrategyBarExecution,
    ) -> None:
        """Route strategy-emitted cancel intents to the order manager actor."""
        router = CancelIntentRouter(
            order_manager_ref=state.order_manager_ref,
            execution_ref=state.execution_ref,
        )
        for _binding, result in strategy_result:
            if not result.cancel_intents:
                continue
            router.route(result.cancel_intents)

    def write_signal_batch_events(
        self,
        state: BacktestActorLoopState,
        batch: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit aggregation, conflict, and rejection events for a signal batch."""
        state.sink.write(
            RuntimeEvent(
                kind="runtime.signal_aggregated",
                payload={
                    "aggregation_decision_id": batch.aggregation_decision_id,
                    "aggregation_policy": batch.aggregation_policy.value,
                    "contributing_strategy_ids": [
                        strategy_id.value for strategy_id in batch.contributing_strategy_ids
                    ],
                    "conflict_group": batch.conflict_group,
                    "intent_count": len(batch.intents),
                    "target_before_risk": (
                        str(batch.target_before_risk)
                        if batch.target_before_risk is not None
                        else None
                    ),
                    "target_after_aggregation": (
                        str(batch.target_after_aggregation)
                        if batch.target_after_aggregation is not None
                        else None
                    ),
                },
                correlation_id=correlation_id,
                instrument_id=batch.instrument_id,
                account_id=self._account_id,
                strategy_id=(
                    batch.contributing_strategy_ids[0]
                    if len(batch.contributing_strategy_ids) == 1
                    else None
                ),
            )
        )
        if batch.conflict_reason:
            self.write_batch_conflict_events(state, batch, correlation_id)

    def write_batch_conflict_events(
        self,
        state: BacktestActorLoopState,
        batch: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit conflict and rejection evidence for a rejected signal batch."""
        state.sink.write(
            RuntimeEvent(
                kind="runtime.signal_conflict_detected",
                payload={
                    "conflict_reason": batch.conflict_reason,
                    "aggregation_decision_id": batch.aggregation_decision_id,
                    "rejected_strategy_ids": [
                        strategy_id.value for strategy_id in batch.rejected_strategy_ids
                    ],
                    "conflicts": [
                        {
                            "instrument_key": conflict.instrument_key,
                            "strategy_ids": [
                                strategy_id.value for strategy_id in conflict.strategy_ids
                            ],
                            "reason": conflict.reason,
                        }
                        for conflict in batch.conflicts
                    ],
                    "conflict_group": batch.conflict_group,
                    "aggregation_policy": batch.aggregation_policy.value,
                },
                correlation_id=correlation_id,
                instrument_id=batch.instrument_id,
                account_id=self._account_id,
                strategy_id=None,
            )
        )
        state.sink.write(
            RuntimeEvent(
                kind="runtime.signal_rejected",
                payload={
                    "conflict_reason": batch.conflict_reason,
                    "aggregation_decision_id": batch.aggregation_decision_id,
                    "rejected_strategy_ids": [
                        strategy_id.value for strategy_id in batch.rejected_strategy_ids
                    ],
                    "conflict_group": batch.conflict_group,
                    "aggregation_policy": batch.aggregation_policy.value,
                    "target_before_risk": (
                        str(batch.target_before_risk)
                        if batch.target_before_risk is not None
                        else None
                    ),
                    "target_after_aggregation": (
                        str(batch.target_after_aggregation)
                        if batch.target_after_aggregation is not None
                        else None
                    ),
                },
                correlation_id=correlation_id,
                instrument_id=batch.instrument_id,
                account_id=self._account_id,
                strategy_id=None,
            )
        )

    def defer_strategy_intent(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
        batch: AggregatedSignalBatch,
        intent: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Buffer an accepted intent to fill at the next bar's open (next_bar_open).

        The intent is keyed by its target instrument so it executes against the
        next strategy-facing bar for that instrument. Intents with no following
        bar never fill, which is correct: a decision at the final bar has no
        next obtainable price.
        """
        instrument_id = intent.asset.instrument_id
        state.pending_fills.setdefault(instrument_id, []).append(
            PendingFill(
                intent=intent,
                batch=batch,
                correlation_id=correlation_id,
                decision_bar=bar,
            )
        )

    def process_strategy_intent(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
        batch: AggregatedSignalBatch,
        intent: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Process one accepted strategy intent through risk/order/execution/account."""
        strategy_id = (
            batch.contributing_strategy_ids[0]
            if batch.contributing_strategy_ids
            else self._strategy_id
        )
        if strategy_id is None:
            raise ValueError("strategy_id is required")
        try:
            processed = self._process_intent(
                intent,
                bar=bar,
                account_ref=state.account_ref,
                order_manager_ref=state.order_manager_ref,
                execution_ref=state.execution_ref,
                account_id=self._account_id,
                strategy_id=strategy_id,
                correlation_id=correlation_id,
                order_number=state.sink.order_count + 1,
                contributing_strategy_ids=batch.contributing_strategy_ids,
                aggregation_decision_id=batch.aggregation_decision_id,
                conflict_reason=batch.conflict_reason if batch.conflict_reason else None,
            )
        except ValueError as exc:
            if not is_broker_capability_reject(exc):
                raise
            self.write_broker_reject_event(state, intent, correlation_id, exc, strategy_id)
            return
        order_payload = processed.orders
        fill_payload = processed.fills
        state.event_writer.write_risk_decision_events(
            processed.risk_decisions,
            correlation_id=correlation_id,
            account_id=self._account_id,
            instrument_id=intent.asset.instrument_id,
            strategy_id=strategy_id,
        )
        state.sink.write_processed(orders=order_payload, fills=fill_payload, bar=bar)
        state.event_writer.write_order_events(
            order_payload,
            state.order_manager_ref,
            fallback_contributing_strategy_ids=batch.contributing_strategy_ids,
        )
        state.event_writer.write_fill_events(fill_payload, state.order_manager_ref)
        self.deliver_fills_to_strategy(state, strategy_id, fill_payload)
        closed_events = state.account_ref.ask(DrainPositionClosedEvents())
        if closed_events:
            account_snapshot = state.account_ref.ask(GetAccountSnapshot())
            state.event_writer.write_position_closed_events(
                closed_events,
                account_id=account_snapshot.account_id,
                strategy_id=strategy_id,
                correlation_id=correlation_id,
            )
        if state.compact_orders:
            state.order_manager_ref.tell(
                CompactForStreaming(order_ids=tuple(order.order_id for order in order_payload))
            )

    def deliver_fills_to_strategy(
        self,
        state: BacktestActorLoopState,
        strategy_id: StrategyId,
        fills: tuple[OrderFill, ...],
    ) -> None:
        """Dispatch validated fills to the originating strategy's ``on_fill``."""
        if not fills:
            return
        for binding in state.strategy_bindings:
            if binding.strategy_id == strategy_id:
                binding.pipeline.deliver_fills(fills)
                return

    def write_broker_reject_event(
        self,
        state: BacktestActorLoopState,
        intent: Any,
        correlation_id: CorrelationId,
        exc: ValueError,
        strategy_id: StrategyId,
    ) -> None:
        """Emit a normalized broker capability rejection event."""
        state.sink.write(
            RuntimeEvent(
                kind="runtime.broker_rejected",
                payload={
                    "reason_code": "unsupported_order_type",
                    "reason": str(exc),
                    "broker_capability_model": broker_capability_payload(self._execution_adapter),
                },
                correlation_id=correlation_id,
                instrument_id=intent.asset.instrument_id,
                account_id=self._account_id,
                strategy_id=strategy_id,
            )
        )

    def write_equity_and_account_snapshot(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
    ) -> None:
        """Emit end-of-bar equity and account snapshot artifacts."""
        snapshot = state.account_ref.ask(GetAccountSnapshot())
        state.sink.write_equity_point(
            self._equity_point(bar, snapshot, latest_prices=state.latest_prices)
        )
        gross_notional, net_notional = _holdings_notional(
            snapshot,
            latest_prices=state.latest_prices,
            contract_multipliers=self._contract_multipliers,
        )
        state.sink.write_holdings_snapshot(
            gross_notional=gross_notional,
            net_notional=net_notional,
        )
        self._write_account_snapshot(state.sink, snapshot)

    @staticmethod
    def _write_account_snapshot(
        sink: BacktestRuntimeSink,
        snapshot: AccountSnapshot,
    ) -> None:
        """Emit a normalized account snapshot event."""
        sink.write(
            RuntimeEvent(
                kind="runtime.account_snapshot",
                payload={
                    "cash": {currency: str(balance) for currency, balance in snapshot.cash.items()},
                    "positions": {
                        instrument_id.value: str(position.quantity)
                        for instrument_id, position in snapshot.positions.items()
                    },
                    "holdings": {
                        instrument_id.value: {
                            "quantity": str(holding.quantity),
                            "average_cost": str(holding.average_cost),
                            "realized_pnl": str(holding.realized_pnl),
                        }
                        for instrument_id, holding in snapshot.holdings.items()
                    },
                },
            )
        )


def _strategy_subscription_target_timeframe(
    strategy_pipelines: Sequence[StrategyExecutionPipeline],
    *,
    fallback: str | None,
) -> str | None:
    """Resolve the single strategy-facing timeframe supported by this loop."""
    timeframes = tuple(
        dict.fromkeys(
            subscription.timeframe.strip()
            for strategy_pipeline in strategy_pipelines
            for subscription in strategy_pipeline.subscriptions
        )
    )
    if not timeframes:
        return fallback
    if len(timeframes) > 1:
        raise RuntimeError(
            "backtest actor loop requires one strategy subscription timeframe; got "
            + ", ".join(timeframes)
        )
    return timeframes[0]


def _holdings_notional(
    snapshot: AccountSnapshot,
    *,
    latest_prices: Mapping[InstrumentId, Decimal],
    contract_multipliers: Mapping[InstrumentId, Decimal],
) -> tuple[Decimal, Decimal]:
    """Return ``(gross, net)`` notional across the current holdings.

    Pure transformation shared between the equity/snapshot writer path and
    any future caller that needs the same valuation; intentionally module-
    private rather than a method on ``BacktestActorLoop`` so the loop stays
    within its private-helper budget.
    """
    gross = Decimal("0")
    net = Decimal("0")
    for instrument_id, position in snapshot.holdings.items():
        mark = latest_prices.get(instrument_id)
        if mark is None or position.quantity == Decimal("0"):
            continue
        multiplier = contract_multipliers.get(instrument_id, Decimal("1"))
        signed_notional = position.quantity * mark * multiplier
        gross += abs(signed_notional)
        net += signed_notional
    return gross, net


__all__ = ["BacktestActorLoop", "BacktestActorLoopResult"]
