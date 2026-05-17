"""Streaming backtest actor loop."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Protocol, TypeAlias

from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
from qts.core.ids import AccountId, CorrelationId, StrategyId
from qts.domain.market_data import Bar
from qts.execution.order_manager import Order, OrderFill
from qts.reporting.backtest import (
    EquityCurvePoint,
    broker_capability_payload,
    is_broker_capability_reject,
)
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor, AccountSnapshot
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import OrderManagerActor
from qts.runtime.intent_processing import ProcessedIntent
from qts.runtime.mailbox import Mailbox
from qts.runtime.market_data_flow import MarketDataFlow
from qts.runtime.runtime_event_writer import RuntimeEventWriter
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline
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


ProcessIntentHandler = Callable[..., ProcessedIntent]
PortfolioViewBuilder = Callable[..., PortfolioView]
EquityPointBuilder = Callable[..., EquityCurvePoint]
RollingPriceUpdater = Callable[..., None]


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


class BacktestActorLoop:
    """Run backtest bars through strategy/order execution actors."""

    def __init__(
        self,
        *,
        strategy: Strategy,
        bars: Iterable[Bar],
        config: BacktestActorLoopConfig,
        dependencies: BacktestActorLoopDependencies,
        strategy_id: StrategyId | None = None,
        account_id: AccountId | None = None,
        signal_aggregation_policy: str = "sum_targets",
        signal_priority: int = 0,
        signal_weight: Decimal = Decimal("1"),
        conflict_group: str = "default",
    ) -> None:
        """Perform __init__."""
        if account_id is None:
            raise ValueError("account_id is required")
        if strategy_id is None:
            raise ValueError("strategy_id is required")
        self._strategy = strategy
        self._bars = bars
        self._initial_cash = config.initial_cash
        self._target_timeframe = config.target_timeframe
        self._exchange_timezone_by_instrument = dict(dependencies.exchange_timezone_by_instrument)
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
        self._strategy_id = strategy_id
        self._account_id = account_id
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
        strategy_pipeline = StrategyExecutionPipeline(
            strategy=self._strategy,
            instrument_registry=self._instrument_registry,
            future_chain_registry=self._future_roll_registry,
            portfolio_view=self._portfolio_view,
            prune_history=prune_history,
            strategy_actor_type=strategy_actor,
            signal_aggregator_actor_type=signal_aggregator_actor,
            strategy_id=self._strategy_id,
            signal_aggregation_policy=self._signal_aggregation_policy,
            signal_priority=self._signal_priority,
            signal_weight=self._signal_weight,
            conflict_group=self._conflict_group,
        )

        market_data_flow = MarketDataFlow(
            target_timeframe=self._target_timeframe,
            exchange_timezone_by_instrument=self._exchange_timezone_by_instrument,
        )
        return BacktestActorLoopState(
            sink=sink,
            compact_orders=compact_orders,
            account_actor=account_actor,
            account_ref=account_ref,
            order_manager_actor=order_manager_actor,
            order_manager_ref=order_manager_ref,
            execution_ref=execution_ref,
            event_writer=event_writer,
            strategy_pipeline=strategy_pipeline,
            market_data_flow=market_data_flow,
            latest_prices={},
            warmup_processed=0,
            trading_processed=0,
            event_index=0,
            last_bar=None,
        )

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
            strategy_result = self.execute_strategy_bar(state, bar, correlation_id)
            self.write_strategy_signal_events(state, strategy_result, correlation_id)
            if state.event_index < self._warmup_bars:
                self.process_warmup_phase(state, bar)
                continue
            self.process_trading_phase(state, bar, strategy_result, correlation_id)

    def process_warmup_phase(self, state: BacktestActorLoopState, bar: Bar) -> None:
        """Record warmup accounting without submitting aggregated intents."""
        state.warmup_processed += 1
        self.write_equity_and_account_snapshot(state, bar)
        state.event_index += 1

    def process_trading_phase(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
        strategy_result: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Process aggregated signals, order flow, and end-of-bar accounting."""
        for batch in strategy_result.signal_batches:
            self.write_signal_batch_events(state, bar, batch, correlation_id)
        for intent in strategy_result.intents:
            self.process_strategy_intent(
                state,
                bar,
                strategy_result,
                intent,
                correlation_id,
            )
        state.trading_processed += 1
        self.write_equity_and_account_snapshot(state, bar)
        state.event_index += 1

    def finalize_run_phase(self, state: BacktestActorLoopState) -> BacktestActorLoopResult:
        """Finalize the strategy pipeline and return the run summary."""
        _ = state.strategy_pipeline.finalize()
        return BacktestActorLoopResult(
            final_account=state.account_actor.snapshot(),
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
    ) -> Any:
        """Execute the strategy pipeline for one bar."""
        return state.strategy_pipeline.execute_bar(
            bar,
            account_snapshot=state.account_actor.snapshot(),
            latest_prices=state.latest_prices,
            aggregate_signals=state.event_index >= self._warmup_bars,
            account_id=self._account_id,
            correlation_id=correlation_id,
        )

    def write_strategy_signal_events(
        self,
        state: BacktestActorLoopState,
        strategy_result: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit raw strategy signal and intent events."""
        for intent in strategy_result.raw_intents:
            state.sink.write(
                RuntimeEvent(
                    kind="runtime.signal_received",
                    payload={
                        "instrument_id": intent.asset.instrument_id.value,
                        "intent_type": intent.intent_type.value,
                        "value": str(intent.value) if intent.value is not None else None,
                        "order_spec": intent.order_spec.to_payload(),
                    },
                    correlation_id=correlation_id,
                    instrument_id=intent.asset.instrument_id,
                    account_id=self._account_id,
                    strategy_id=self._strategy_id,
                )
            )
            state.sink.write(
                RuntimeEvent(
                    kind="runtime.strategy_intent",
                    payload={
                        "instrument_id": intent.asset.instrument_id.value,
                        "intent_type": intent.intent_type.value,
                        "value": str(intent.value) if intent.value is not None else None,
                        "order_spec": intent.order_spec.to_payload(),
                    },
                    correlation_id=correlation_id,
                    instrument_id=intent.asset.instrument_id,
                    account_id=self._account_id,
                    strategy_id=self._strategy_id,
                )
            )

    def write_signal_batch_events(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
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
                instrument_id=bar.instrument_id,
                account_id=self._account_id,
                strategy_id=self._strategy_id,
            )
        )
        if batch.conflict_reason:
            self.write_batch_conflict_events(state, bar, batch, correlation_id)

    def write_batch_conflict_events(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
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
                instrument_id=bar.instrument_id,
                account_id=self._account_id,
                strategy_id=self._strategy_id,
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
                instrument_id=bar.instrument_id,
                account_id=self._account_id,
                strategy_id=self._strategy_id,
            )
        )

    def process_strategy_intent(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
        strategy_result: Any,
        intent: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Process one accepted strategy intent through risk/order/execution/account."""
        try:
            processed = self._process_intent(
                intent,
                bar=bar,
                account_actor=state.account_actor,
                order_manager_actor=state.order_manager_actor,
                order_manager_ref=state.order_manager_ref,
                execution_ref=state.execution_ref,
                account_ref=state.account_ref,
                account_id=self._account_id,
                strategy_id=self._strategy_id,
                correlation_id=correlation_id,
                order_number=state.sink.order_count + 1,
                contributing_strategy_ids=strategy_result.contributing_strategy_ids,
                aggregation_decision_id=strategy_result.aggregation_decision_id,
                conflict_reason=(
                    strategy_result.conflict_reason if strategy_result.conflict_reason else None
                ),
            )
        except ValueError as exc:
            if not is_broker_capability_reject(exc):
                raise
            self.write_broker_reject_event(state, intent, correlation_id, exc)
            return
        order_payload = processed.orders
        fill_payload = processed.fills
        state.event_writer.write_risk_decision_events(
            processed.risk_decisions,
            correlation_id=correlation_id,
            account_id=self._account_id,
            instrument_id=intent.asset.instrument_id,
            strategy_id=self._strategy_id,
        )
        state.sink.write_processed(orders=order_payload, fills=fill_payload, bar=bar)
        state.event_writer.write_order_events(
            order_payload,
            state.order_manager_actor,
            fallback_contributing_strategy_ids=strategy_result.contributing_strategy_ids,
        )
        state.event_writer.write_fill_events(fill_payload, state.order_manager_actor)
        closed_events = state.account_actor.drain_position_closed_events()
        if closed_events:
            state.event_writer.write_position_closed_events(
                closed_events,
                account_id=getattr(state.account_actor.snapshot(), "account_id", None),
                strategy_id=None,
                correlation_id=None,
            )
        if state.compact_orders:
            state.order_manager_actor.compact_for_streaming(
                order.order_id for order in order_payload
            )

    def write_broker_reject_event(
        self,
        state: BacktestActorLoopState,
        intent: Any,
        correlation_id: CorrelationId,
        exc: ValueError,
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
                strategy_id=self._strategy_id,
            )
        )

    def write_equity_and_account_snapshot(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
    ) -> None:
        """Emit end-of-bar equity and account snapshot artifacts."""
        snapshot = state.account_actor.snapshot()
        state.sink.write_equity_point(
            self._equity_point(bar, snapshot, latest_prices=state.latest_prices)
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


__all__ = ["BacktestActorLoop", "BacktestActorLoopResult"]
