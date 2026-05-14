"""Shared paper/live runtime session orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from qts.core.ids import AccountId, CausationId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.data.permissions import MarketDataPermissionEvent
from qts.data.sources.streaming_market_data_source import (
    StreamingMarketDataDegradation,
    StreamingMarketDataSubscriptionEvent,
)
from qts.domain.market_data import Bar
from qts.domain.orders import CancelIntent
from qts.execution.order_manager import Order, OrderFill
from qts.execution.order_state_machine import OrderState
from qts.risk.kill_switch import RuntimeKillSwitchCommand
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.actors.order_manager_actor import CancelOrder
from qts.runtime.actors.signal_aggregator_actor import (
    AggregatedSignalBatch,
    SignalAggregatorActor,
    SignalContribution,
    StrategySignalEvent,
)
from qts.runtime.intent_processing import ProcessedIntent, TargetIntentProcessor
from qts.runtime.live import LiveRuntimeState, LiveRuntimeStateMachine
from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
from qts.runtime.live_runtime_topology import (
    AccountRuntimePartition,
    _LiveRuntimeTopologyBuilder,
    _StrategyRuntimeBinding,
)
from qts.runtime.mailbox import Mailbox
from qts.runtime.market_data_flow import MarketDataFlow
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext
from qts.runtime.topology import RuntimeTopology
from qts.strategy_sdk import TargetIntent


@dataclass(frozen=True, slots=True)
class LiveRuntimeSessionResult:
    """Observable result from one paper/live market-data event."""

    market_data: tuple[Bar, ...] = ()
    orders: tuple[Order, ...] = ()
    fills: tuple[OrderFill, ...] = ()
    account_snapshot: AccountSnapshot | None = None
    account_snapshots: tuple[tuple[AccountId | None, AccountSnapshot], ...] = ()
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class LiveKillSwitchEvidence:
    """Evidence emitted when a runtime kill switch is activated."""

    operator_id: str
    reason: str
    runtime_state: str
    active_order_ids: tuple[str, ...]
    cancelled_order_ids: tuple[str, ...]
    account_snapshot: AccountSnapshot


@dataclass(frozen=True, slots=True)
class RuntimeRollbackCommand:
    """Operator command to preserve state and stop new orders for rollback."""

    operator_id: str
    reason: str
    event_store_paths: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        """Validate rollback evidence fields."""
        if not self.operator_id.strip():
            raise ValueError("operator_id must not be empty")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")


@dataclass(frozen=True, slots=True)
class RuntimeRollbackEvidence:
    """Evidence captured during a runtime rollback drill."""

    operator_id: str
    reason: str
    runtime_state: str
    event_store_paths: tuple[str, ...]
    account_snapshot: AccountSnapshot


class LiveRuntimeSession:
    """Run paper/live market data through the shared strategy/order actor chain."""

    def __init__(self, dependencies: LiveRuntimeDependencies) -> None:
        """Create the runtime session and its actor graph."""
        self._dependencies = dependencies
        self._topology = dependencies.runtime_topology
        self._resolved_account_id = dependencies.account_id
        self._resolved_strategy_id = dependencies.strategy_id
        self._strategy_bindings: tuple[_StrategyRuntimeBinding, ...] = ()
        self._strategy_subscriptions: tuple[InstrumentId, ...] = ()
        self._account_partitions: dict[AccountId | None, AccountRuntimePartition] = {}
        self._latest_prices: dict[InstrumentId, Decimal] = {}
        self._event_index = 0
        self._runtime_event_sequence = 0
        self._order_sequence = 0
        self._kill_switch_active = False
        resolved_topology = _LiveRuntimeTopologyBuilder(dependencies).build()
        self._strategy_bindings = resolved_topology.strategy_bindings
        self._strategy_subscriptions = resolved_topology.strategy_subscriptions
        self._account_partitions = resolved_topology.account_partitions
        self._resolved_account_id = resolved_topology.resolved_account_id
        self._resolved_strategy_id = resolved_topology.resolved_strategy_id
        self._machine = LiveRuntimeStateMachine()
        self._intent_processor = TargetIntentProcessor(
            risk_engine=dependencies.risk_engine,
            instrument_context=dependencies.instrument_context,
            multiplier_for=dependencies.multiplier_for,
            order_id_prefix=dependencies.order_id_prefix,
            broker_order_id_prefix=dependencies.order_id_prefix,
        )
        self._signal_result_mailbox = Mailbox()
        self._signal_aggregator_ref = ActorRef(
            actor=SignalAggregatorActor(
                result_ref=ActorRef(mailbox=self._signal_result_mailbox),
            ),
            mailbox=Mailbox(),
        )
        self._market_data_flow = MarketDataFlow(
            target_timeframe=dependencies.target_timeframe,
            exchange_timezone_by_instrument=dependencies.exchange_timezones,
        )
        primary_account_id = (
            self._primary_partition_id if len(self._account_partitions) == 1 else None
        )
        self._event_context = RuntimeEventContext(
            run_id=dependencies.run_id,
            mode=dependencies.mode,
            execution_environment=dependencies.execution_environment,
            account_id=primary_account_id,
            strategy_id=(
                self._strategy_bindings[0].strategy_id
                if len(self._strategy_bindings) == 1
                else None
            ),
        )

    @property
    def _primary_partition_id(self) -> AccountId | None:
        """Return canonical account ID when single partition topology is used."""
        if len(self._account_partitions) == 1:
            return next(iter(self._account_partitions))
        return None

    def _resolve_partition(self, account_id: AccountId | None) -> AccountRuntimePartition:
        if len(self._account_partitions) == 1:
            return next(iter(self._account_partitions.values()))
        if account_id is None:
            raise ValueError("strategy account_id required for multi-account topology")
        partition = self._account_partitions.get(account_id)
        if partition is None:
            raise ValueError(f"unknown account partition for strategy: {account_id}")
        return partition

    @property
    def _primary_partition(self) -> AccountRuntimePartition:
        if self._primary_partition_id is not None:
            return self._account_partitions[self._primary_partition_id]
        return next(iter(self._account_partitions.values()))

    @property
    def topology(self) -> RuntimeTopology | None:
        """Return the runtime topology if one was injected."""
        return self._topology

    @property
    def state(self) -> LiveRuntimeState:
        """Return the current runtime lifecycle state."""
        return self._machine.state

    @property
    def account_snapshot(self) -> AccountSnapshot:
        """Return the actor-owned account snapshot."""
        return self._primary_partition.account_actor.snapshot()

    def start(self) -> LiveRuntimeState:
        """Start the session."""
        self._machine.apply("start")
        state = self._machine.apply("started")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def stop(self) -> LiveRuntimeState:
        """Stop the session."""
        state = self._machine.apply("stop")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def pause(self) -> LiveRuntimeState:
        """Pause new strategy intent processing."""
        state = self._machine.apply("pause")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def resume(self) -> LiveRuntimeState:
        """Resume new strategy intent processing."""
        state = self._machine.apply("resume")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def degrade(self) -> LiveRuntimeState:
        """Degrade the session while keeping observability alive."""
        state = self._machine.apply("degrade")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def recover(self) -> LiveRuntimeState:
        """Recover a degraded session."""
        state = self._machine.apply("recover")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def on_broker_disconnect(self, *, reason: str) -> LiveRuntimeState:
        """Mark the session degraded after broker connectivity is lost."""
        if not reason.strip():
            raise ValueError("reason must not be empty")
        self._write_event(
            "runtime.broker_disconnected",
            {"reason": reason, "state_before": self.state.value},
        )
        if self.state in {LiveRuntimeState.RUNNING, LiveRuntimeState.PAUSED}:
            return self.degrade()
        return self.state

    def on_broker_reconnect(
        self,
        *,
        reason: str,
        reconciliation_passed: bool,
    ) -> LiveRuntimeState:
        """Recover from broker reconnect only after reconciliation passes."""
        if not reason.strip():
            raise ValueError("reason must not be empty")
        self._write_event(
            "runtime.broker_reconnected",
            {
                "reason": reason,
                "reconciliation_passed": reconciliation_passed,
                "state_before": self.state.value,
            },
        )
        if reconciliation_passed:
            if self.state is LiveRuntimeState.DEGRADED:
                return self.recover()
            return self.state
        if self.state in {LiveRuntimeState.RUNNING, LiveRuntimeState.PAUSED}:
            return self.degrade()
        return self.state

    def on_market_data_source_event(
        self,
        event: Bar
        | StreamingMarketDataDegradation
        | StreamingMarketDataSubscriptionEvent
        | MarketDataPermissionEvent,
    ) -> LiveRuntimeSessionResult:
        """Handle a source market-data event, including degradation and permission signals."""
        if isinstance(event, Bar):
            return self.on_market_data(event)
        flow_result = self._market_data_flow.publish_source_event(event)
        reason_code: str | None = None
        for runtime_event in flow_result.runtime_events:
            self._write(runtime_event)
            if runtime_event.kind == "runtime.degraded":
                if self.state is not LiveRuntimeState.DEGRADED:
                    self.degrade()
                reason_code = "RUNTIME_DEGRADED"
        primary_snapshot = self._primary_partition.account_actor.snapshot()
        account_snapshots = tuple(
            (account_id, partition.account_actor.snapshot())
            for account_id, partition in self._account_partitions.items()
        )
        return LiveRuntimeSessionResult(
            market_data=(),
            orders=(),
            fills=(),
            account_snapshot=primary_snapshot,
            account_snapshots=account_snapshots,
            reason_code=reason_code,
        )

    def on_market_data(self, source_bar: Bar) -> LiveRuntimeSessionResult:
        """Handle one source bar through market-data, strategy, risk, and actors."""
        if (
            self._topology is not None
            and source_bar.instrument_id not in self._strategy_subscriptions
        ):
            snapshots = tuple(
                (account_id, partition.account_actor.snapshot())
                for account_id, partition in self._account_partitions.items()
            )
            return LiveRuntimeSessionResult(
                market_data=(),
                orders=(),
                fills=(),
                account_snapshot=self._primary_partition.account_actor.snapshot(),
                account_snapshots=snapshots,
                reason_code="INSTRUMENT_NOT_SUBSCRIBED",
            )

        flow_result = self._market_data_flow.publish_source_event(source_bar)
        for event in flow_result.runtime_events:
            self._write(event)
            if event.kind == "runtime.degraded" and self.state is not LiveRuntimeState.DEGRADED:
                self.degrade()

        bars = flow_result.market_data
        all_orders: list[Order] = []
        all_fills: list[OrderFill] = []
        reason_code: str | None = None
        account_snapshots: tuple[tuple[AccountId | None, AccountSnapshot], ...]
        for bar in bars:
            correlation_id = CorrelationId(
                f"md:{bar.instrument_id.value}:{bar.timeframe}:{bar.end_time.isoformat()}"
            )
            self._latest_prices[bar.instrument_id] = bar.close
            self._write_event(
                "runtime.market_data",
                {
                    "instrument_id": bar.instrument_id.value,
                    "timeframe": bar.timeframe,
                    "end_time": bar.end_time.isoformat(),
                },
                correlation_id=correlation_id,
                instrument_id=bar.instrument_id,
            )
            blocked_reason = self._blocked_reason()
            if blocked_reason is not None:
                reason_code = blocked_reason
                continue

            bindings_for_bar = [
                binding
                for binding in self._strategy_bindings
                if binding.enabled
                and (not binding.subscriptions or bar.instrument_id in binding.subscriptions)
            ]
            if self._topology is not None and not bindings_for_bar:
                reason_code = "INSTRUMENT_NOT_SUBSCRIBED"
                continue

            aggregate_signals = self._event_index >= self._dependencies.warmup_bars
            contributions_by_account: dict[AccountId | None, list[SignalContribution]] = {}
            for binding in bindings_for_bar:
                strategy_result = binding.pipeline.execute_bar(
                    bar,
                    account_snapshot=self._resolve_partition(
                        binding.account_id
                    ).account_actor.snapshot(),
                    latest_prices=self._latest_prices,
                    aggregate_signals=aggregate_signals,
                )
                for intent in strategy_result.raw_intents:
                    self._write_event(
                        "runtime.signal_received",
                        {
                            "instrument_id": intent.asset.instrument_id.value,
                            "intent_type": intent.intent_type.value,
                            "value": str(intent.value) if intent.value is not None else None,
                            "aggregation_policy": binding.signal_aggregation_policy.value,
                            "signal_weight": str(binding.signal_weight),
                            "signal_priority": binding.signal_priority,
                            "conflict_group": binding.conflict_group,
                        },
                        correlation_id=correlation_id,
                        instrument_id=intent.asset.instrument_id,
                        strategy_id=binding.strategy_id,
                        account_id=binding.account_id,
                    )
                    self._write_event(
                        "runtime.strategy_intent",
                        {
                            "instrument_id": intent.asset.instrument_id.value,
                            "intent_type": intent.intent_type.value,
                            "value": str(intent.value) if intent.value is not None else None,
                        },
                        correlation_id=correlation_id,
                        instrument_id=intent.asset.instrument_id,
                        strategy_id=binding.strategy_id,
                        account_id=binding.account_id,
                    )
                    if aggregate_signals:
                        contributions_by_account.setdefault(
                            binding.account_id,
                            [],
                        ).append(
                            SignalContribution(
                                strategy_id=binding.strategy_id,
                                intent=intent,
                                aggregation_policy=binding.signal_aggregation_policy,
                                priority=binding.signal_priority,
                                weight=binding.signal_weight,
                                conflict_group=binding.conflict_group,
                            )
                        )

            if aggregate_signals:
                for account_id, contributions in contributions_by_account.items():
                    partition = self._resolve_partition(account_id)
                    aggregated_batches = self._aggregate_signal_batches(
                        bar,
                        tuple(contributions),
                    )
                    for batch in aggregated_batches:
                        if batch.conflict_reason:
                            self._write_event(
                                "runtime.signal_conflict_detected",
                                {
                                    "conflict_reason": batch.conflict_reason,
                                    "rejected_strategy_ids": [
                                        strategy_id.value
                                        for strategy_id in batch.rejected_strategy_ids
                                    ],
                                    "conflict_group": batch.conflict_group,
                                    "aggregation_policy": batch.aggregation_policy.value,
                                },
                                correlation_id=correlation_id,
                                account_id=partition.account_id,
                                instrument_id=bar.instrument_id,
                            )
                            self._write_event(
                                "runtime.signal_rejected",
                                {
                                    "conflict_reason": batch.conflict_reason,
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
                                account_id=partition.account_id,
                                instrument_id=bar.instrument_id,
                            )
                        self._write_event(
                            "runtime.signal_aggregated",
                            {
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
                            account_id=partition.account_id,
                            instrument_id=bar.instrument_id,
                        )
                        if not batch.intents:
                            continue
                        if not self._dependencies.order_submission_enabled:
                            reason_code = "ORDER_SUBMISSION_DISABLED"
                            continue
                        for intent in batch.intents:
                            strategy_id = (
                                batch.contributing_strategy_ids[0]
                                if batch.contributing_strategy_ids
                                else self._resolved_strategy_id
                            )
                            if strategy_id is None:
                                raise ValueError("strategy_id is required")
                            processed = self._process_intent(
                                intent,
                                bar=bar,
                                account_id=account_id,
                                strategy_id=strategy_id,
                                correlation_id=correlation_id,
                                partition=partition,
                                contributing_strategy_ids=batch.contributing_strategy_ids,
                            )
                            all_orders.extend(processed.orders)
                            all_fills.extend(processed.fills)
                            for order in processed.orders:
                                metadata = partition.order_manager_actor.route_metadata(
                                    order.order_id
                                )
                                self._write_event(
                                    "runtime.order_submitted",
                                    {
                                        "order_id": order.order_id.value,
                                        "broker_order_id": order.broker_order_id,
                                        "client_order_id": metadata.client_order_id,
                                        "instrument_id": order.intent.instrument_id.value,
                                        "contributing_strategy_ids": [
                                            strategy_id.value
                                            for strategy_id in batch.contributing_strategy_ids
                                        ],
                                    },
                                    correlation_id=metadata.correlation_id,
                                    instrument_id=order.intent.instrument_id,
                                    strategy_id=metadata.strategy_id,
                                    account_id=metadata.account_id,
                                )
                                self._write_event(
                                    "runtime.broker_report",
                                    {
                                        "order_id": order.order_id.value,
                                        "state": order.state.value,
                                        "broker_order_id": order.broker_order_id,
                                        "client_order_id": metadata.client_order_id,
                                    },
                                    correlation_id=metadata.correlation_id,
                                    instrument_id=order.intent.instrument_id,
                                    strategy_id=metadata.strategy_id,
                                    account_id=metadata.account_id,
                                    causation_id=CausationId(
                                        f"{metadata.client_order_id}:order_submitted"
                                    ),
                                )
                            for fill in processed.fills:
                                metadata = partition.order_manager_actor.route_metadata(
                                    fill.order_id
                                )
                                order = partition.order_manager_actor.get_order(fill.order_id)
                                self._write_event(
                                    "runtime.fill_applied",
                                    {
                                        "fill_id": fill.fill_id,
                                        "order_id": fill.order_id.value,
                                        "broker_order_id": order.broker_order_id,
                                        "client_order_id": metadata.client_order_id,
                                        "instrument_id": fill.instrument_id.value,
                                        "side": fill.side.value,
                                        "quantity": str(fill.quantity),
                                        "price": str(fill.price),
                                        "commission": str(fill.commission),
                                        "slippage": str(fill.slippage),
                                    },
                                    correlation_id=metadata.correlation_id,
                                    instrument_id=fill.instrument_id,
                                    strategy_id=metadata.strategy_id,
                                    account_id=metadata.account_id,
                                    causation_id=CausationId(
                                        f"{metadata.client_order_id}:broker_report"
                                    ),
                                )

            self._event_index += 1

        primary_snapshot = self._primary_partition.account_actor.snapshot()
        account_snapshots = tuple(
            (account_id, partition.account_actor.snapshot())
            for account_id, partition in self._account_partitions.items()
        )
        if bars:
            for partition in self._account_partitions.values():
                snapshot = partition.account_actor.snapshot()
                self._write_event(
                    "runtime.account_snapshot",
                    {
                        "cash": {
                            currency: str(balance) for currency, balance in snapshot.cash.items()
                        },
                        "positions": {
                            instrument_id.value: str(position.quantity)
                            for instrument_id, position in snapshot.positions.items()
                        },
                    },
                    account_id=partition.account_id,
                )
        return LiveRuntimeSessionResult(
            market_data=bars,
            orders=tuple(all_orders),
            fills=tuple(all_fills),
            account_snapshot=primary_snapshot,
            account_snapshots=account_snapshots,
            reason_code=reason_code,
        )

    def activate_kill_switch(self, command: RuntimeKillSwitchCommand) -> LiveKillSwitchEvidence:
        """Block new orders and optionally cancel active orders through actors."""
        self._kill_switch_active = True
        active_order_ids = self._active_order_ids()
        cancelled_order_ids: list[str] = []
        if command.cancel_active_orders:
            active_orders_by_partition: list[tuple[str, AccountRuntimePartition]] = []
            for partition in self._account_partitions.values():
                for order in partition.order_manager_actor.snapshot().orders:
                    if order.state in {
                        OrderState.FILLED,
                        OrderState.CANCELLED,
                        OrderState.REJECTED,
                    }:
                        continue
                    active_orders_by_partition.append((order.order_id.value, partition))
            for order_id, partition in active_orders_by_partition:
                metadata = partition.order_manager_actor.route_metadata(OrderId(order_id))
                partition.order_manager_ref.tell(
                    CancelOrder(
                        CancelIntent(order_id=OrderId(order_id)),
                        account_id=metadata.account_id,
                        strategy_id=metadata.strategy_id,
                        client_order_id=metadata.client_order_id,
                        correlation_id=metadata.correlation_id,
                    )
                )
            for partition in self._account_partitions.values():
                partition.order_manager_ref.process_all()
                partition.execution_ref.process_all()
                partition.order_manager_ref.process_all()
                partition.account_ref.process_all()
            for order_id, partition in active_orders_by_partition:
                order = partition.order_manager_actor.get_order(OrderId(order_id))
                if order.state is OrderState.CANCELLED:
                    cancelled_order_ids.append(order_id)
            active_order_ids = tuple(order_id for order_id, _ in active_orders_by_partition)
        snapshot = self._primary_partition.account_actor.snapshot()
        evidence = LiveKillSwitchEvidence(
            operator_id=command.operator_id,
            reason=command.reason,
            runtime_state=self.state.value,
            active_order_ids=tuple(active_order_ids),
            cancelled_order_ids=tuple(cancelled_order_ids),
            account_snapshot=snapshot,
        )
        self._write_event(
            "runtime.kill_switch",
            {
                "operator_id": evidence.operator_id,
                "reason": evidence.reason,
                "runtime_state": evidence.runtime_state,
                "active_order_ids": list(evidence.active_order_ids),
                "cancelled_order_ids": list(evidence.cancelled_order_ids),
                "cash": {
                    currency: str(balance)
                    for currency, balance in evidence.account_snapshot.cash.items()
                },
            },
        )
        return evidence

    def rollback(self, command: RuntimeRollbackCommand) -> RuntimeRollbackEvidence:
        """Stop new orders and preserve rollback evidence."""
        self._kill_switch_active = True
        snapshot = self._primary_partition.account_actor.snapshot()
        evidence = RuntimeRollbackEvidence(
            operator_id=command.operator_id,
            reason=command.reason,
            runtime_state=self.state.value,
            event_store_paths=tuple(str(path) for path in command.event_store_paths),
            account_snapshot=snapshot,
        )
        self._write_event(
            "runtime.rollback",
            {
                "operator_id": evidence.operator_id,
                "reason": evidence.reason,
                "runtime_state": evidence.runtime_state,
                "event_store_paths": list(evidence.event_store_paths),
                "cash": {
                    currency: str(balance)
                    for currency, balance in evidence.account_snapshot.cash.items()
                },
            },
        )
        return evidence

    def _process_intent(
        self,
        intent: TargetIntent,
        *,
        bar: Bar,
        account_id: AccountId | None,
        strategy_id: StrategyId,
        correlation_id: CorrelationId,
        partition: AccountRuntimePartition,
        contributing_strategy_ids: tuple[StrategyId, ...] = (),
    ) -> ProcessedIntent:
        self._order_sequence += 1
        return self._intent_processor.process_intent(
            intent,
            bar=bar,
            account_actor=partition.account_actor,
            order_manager_actor=partition.order_manager_actor,
            order_manager_ref=partition.order_manager_ref,
            execution_ref=partition.execution_ref,
            account_ref=partition.account_ref,
            account_id=account_id,
            strategy_id=strategy_id,
            correlation_id=correlation_id,
            contributing_strategy_ids=contributing_strategy_ids,
            order_number=self._order_sequence,
        )

    def _aggregate_signal_batches(
        self,
        bar: Bar,
        contributions: tuple[SignalContribution, ...],
    ) -> tuple[AggregatedSignalBatch, ...]:
        if not contributions:
            return ()
        self._signal_aggregator_ref.tell(StrategySignalEvent(bar=bar, contributions=contributions))
        self._signal_aggregator_ref.process_all()
        batches: list[AggregatedSignalBatch] = []
        while not self._signal_result_mailbox.empty():
            result = self._signal_result_mailbox.get()
            if not isinstance(result, AggregatedSignalBatch):
                raise TypeError(f"unexpected signal batch: {type(result).__name__}")
            batches.append(result)

        if not batches:
            raise RuntimeError("signal aggregator produced no batch")
        return tuple(batches)

    def _blocked_reason(self) -> str | None:
        if self._kill_switch_active:
            return "KILL_SWITCH_ACTIVE"
        if self.state is LiveRuntimeState.PAUSED:
            return "RUNTIME_PAUSED"
        if self.state is LiveRuntimeState.DEGRADED:
            return "RUNTIME_DEGRADED"
        if self.state is not LiveRuntimeState.RUNNING:
            return "RUNTIME_NOT_RUNNING"
        return None

    def _write_event(
        self,
        kind: str,
        payload: dict[str, object],
        *,
        correlation_id: CorrelationId | None = None,
        instrument_id: InstrumentId | None = None,
        account_id: AccountId | None = None,
        strategy_id: StrategyId | None = None,
        causation_id: CausationId | None = None,
    ) -> None:
        self._write(
            RuntimeEvent(
                kind=kind,
                payload=payload,
                correlation_id=correlation_id,
                instrument_id=instrument_id,
                account_id=account_id,
                strategy_id=strategy_id,
                causation_id=causation_id,
            )
        )

    def _write(self, event: RuntimeEvent) -> None:
        self._runtime_event_sequence += 1
        event = self._event_context.apply(event, sequence_no=self._runtime_event_sequence)
        sink = self._dependencies.sink
        if sink is not None:
            sink.write(event)

    def _active_order_ids(self) -> tuple[str, ...]:
        terminal = {OrderState.FILLED, OrderState.CANCELLED, OrderState.REJECTED}
        active_order_ids: list[str] = []
        for partition in self._account_partitions.values():
            for order in partition.order_manager_actor.snapshot().orders:
                if order.state not in terminal:
                    active_order_ids.append(order.order_id.value)
        return tuple(active_order_ids)


__all__ = [
    "LiveKillSwitchEvidence",
    "LiveRuntimeSession",
    "LiveRuntimeSessionResult",
    "RuntimeRollbackCommand",
    "RuntimeRollbackEvidence",
]
