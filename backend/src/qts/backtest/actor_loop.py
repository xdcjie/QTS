"""Streaming backtest actor loop."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
from qts.core.ids import AccountId, CorrelationId, InstrumentId, StrategyId
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
        """Perform run."""
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

        latest_prices: dict[InstrumentId, Decimal] = {}
        warmup_processed = 0
        trading_processed = 0
        event_index = 0
        last_bar: Bar | None = None

        market_data_flow = MarketDataFlow(
            target_timeframe=self._target_timeframe,
            exchange_timezone_by_instrument=self._exchange_timezone_by_instrument,
        )
        for source_bar in self._bars:
            for bar in market_data_flow.publish_bar(source_bar):
                last_bar = bar
                correlation_id = CorrelationId(
                    f"md:{bar.instrument_id.value}:{bar.timeframe}:{bar.end_time.isoformat()}"
                )
                latest_prices[bar.instrument_id] = bar.close
                market_data_payload: dict[str, object] = {
                    "instrument_id": bar.instrument_id.value,
                    "timeframe": bar.timeframe,
                    "end_time": bar.end_time.isoformat(),
                }
                market_data_payload.update(self._market_data_provenance_for(bar))
                sink.write(
                    RuntimeEvent(
                        kind="runtime.market_data",
                        payload=market_data_payload,
                        correlation_id=correlation_id,
                        instrument_id=bar.instrument_id,
                    )
                )
                self._update_rolling_prices(
                    bar,
                    latest_prices=latest_prices,
                )
                strategy_result = strategy_pipeline.execute_bar(
                    bar,
                    account_snapshot=account_actor.snapshot(),
                    latest_prices=latest_prices,
                    aggregate_signals=event_index >= self._warmup_bars,
                    account_id=self._account_id,
                    correlation_id=correlation_id,
                )
                for intent in strategy_result.raw_intents:
                    sink.write(
                        RuntimeEvent(
                            kind="runtime.signal_received",
                            payload={
                                "instrument_id": intent.asset.instrument_id.value,
                                "intent_type": intent.intent_type.value,
                                "value": str(intent.value) if intent.value is not None else None,
                            },
                            correlation_id=correlation_id,
                            instrument_id=intent.asset.instrument_id,
                            account_id=self._account_id,
                            strategy_id=self._strategy_id,
                        )
                    )
                    sink.write(
                        RuntimeEvent(
                            kind="runtime.strategy_intent",
                            payload={
                                "instrument_id": intent.asset.instrument_id.value,
                                "intent_type": intent.intent_type.value,
                                "value": str(intent.value) if intent.value is not None else None,
                            },
                            correlation_id=correlation_id,
                            instrument_id=intent.asset.instrument_id,
                            account_id=self._account_id,
                            strategy_id=self._strategy_id,
                        )
                    )
                if event_index < self._warmup_bars:
                    warmup_processed += 1
                    sink.write_equity_point(
                        self._equity_point(
                            bar,
                            account_actor.snapshot(),
                            latest_prices=latest_prices,
                        )
                    )
                    self._write_account_snapshot(sink, account_actor.snapshot())
                    event_index += 1
                    continue

                if strategy_result.signal_batches:
                    for batch in strategy_result.signal_batches:
                        sink.write(
                            RuntimeEvent(
                                kind="runtime.signal_aggregated",
                                payload={
                                    "aggregation_decision_id": batch.aggregation_decision_id,
                                    "aggregation_policy": batch.aggregation_policy.value,
                                    "contributing_strategy_ids": [
                                        strategy_id.value
                                        for strategy_id in batch.contributing_strategy_ids
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
                            sink.write(
                                RuntimeEvent(
                                    kind="runtime.signal_conflict_detected",
                                    payload={
                                        "conflict_reason": batch.conflict_reason,
                                        "aggregation_decision_id": batch.aggregation_decision_id,
                                        "rejected_strategy_ids": [
                                            strategy_id.value
                                            for strategy_id in batch.rejected_strategy_ids
                                        ],
                                        "conflicts": [
                                            {
                                                "instrument_key": conflict.instrument_key,
                                                "strategy_ids": [
                                                    strategy_id.value
                                                    for strategy_id in conflict.strategy_ids
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
                            sink.write(
                                RuntimeEvent(
                                    kind="runtime.signal_rejected",
                                    payload={
                                        "conflict_reason": batch.conflict_reason,
                                        "aggregation_decision_id": batch.aggregation_decision_id,
                                        "rejected_strategy_ids": [
                                            strategy_id.value
                                            for strategy_id in batch.rejected_strategy_ids
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

                for intent in strategy_result.intents:
                    try:
                        processed = self._process_intent(
                            intent,
                            bar=bar,
                            account_actor=account_actor,
                            order_manager_actor=order_manager_actor,
                            order_manager_ref=order_manager_ref,
                            execution_ref=execution_ref,
                            account_ref=account_ref,
                            account_id=self._account_id,
                            strategy_id=self._strategy_id,
                            correlation_id=correlation_id,
                            order_number=sink.order_count + 1,
                            contributing_strategy_ids=strategy_result.contributing_strategy_ids,
                            aggregation_decision_id=strategy_result.aggregation_decision_id,
                            conflict_reason=(
                                strategy_result.conflict_reason
                                if strategy_result.conflict_reason
                                else None
                            ),
                        )
                    except ValueError as exc:
                        if not is_broker_capability_reject(exc):
                            raise
                        sink.write(
                            RuntimeEvent(
                                kind="runtime.broker_rejected",
                                payload={
                                    "reason_code": "unsupported_order_type",
                                    "reason": str(exc),
                                    "broker_capability_model": broker_capability_payload(
                                        self._execution_adapter
                                    ),
                                },
                                correlation_id=correlation_id,
                                instrument_id=intent.asset.instrument_id,
                                account_id=self._account_id,
                                strategy_id=self._strategy_id,
                            )
                        )
                        continue
                    order_payload = processed.orders
                    fill_payload = processed.fills
                    event_writer.write_risk_decision_events(
                        processed.risk_decisions,
                        correlation_id=correlation_id,
                        account_id=self._account_id,
                        instrument_id=intent.asset.instrument_id,
                        strategy_id=self._strategy_id,
                    )
                    sink.write_processed(
                        orders=order_payload,
                        fills=fill_payload,
                        bar=bar,
                    )
                    event_writer.write_order_events(
                        order_payload,
                        order_manager_actor,
                        fallback_contributing_strategy_ids=strategy_result.contributing_strategy_ids,
                    )
                    event_writer.write_fill_events(fill_payload, order_manager_actor)
                    if compact_orders:
                        order_manager_actor.compact_for_streaming(
                            order.order_id for order in order_payload
                        )
                trading_processed += 1
                sink.write_equity_point(
                    self._equity_point(
                        bar,
                        account_actor.snapshot(),
                        latest_prices=latest_prices,
                    )
                )
                self._write_account_snapshot(sink, account_actor.snapshot())
                event_index += 1

        _ = strategy_pipeline.finalize()
        return BacktestActorLoopResult(
            final_account=account_actor.snapshot(),
            warmup_bars=warmup_processed,
            trading_bars=trading_processed,
            last_bar=last_bar,
        )

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
                },
            )
        )


__all__ = ["BacktestActorLoop", "BacktestActorLoopResult"]
