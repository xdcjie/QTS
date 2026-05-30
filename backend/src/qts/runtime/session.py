"""Shared paper/live runtime session orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from qts.core.ids import AccountId, BrokerId, CausationId, CorrelationId, InstrumentId, StrategyId
from qts.data.permissions import MarketDataPermissionEvent
from qts.data.sources.streaming_market_data_source import (
    StreamingMarketDataDegradation,
    StreamingMarketDataSubscriptionEvent,
)
from qts.domain.market_data import Bar
from qts.domain.orders import Order, OrderFill, OrderState, OrderStateSnapshot
from qts.risk.intraday_pnl import IntradayPnlCalculator
from qts.risk.kill_switch import RuntimeKillSwitchCommand
from qts.runtime.actor_events import ActorFailureEvent
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actor_supervisor import SupervisorDecision
from qts.runtime.actors.account_actor import (
    AccountSnapshot,
    GetAccountSnapshot,
)
from qts.runtime.actors.order_manager_actor import GetOrderManagerSnapshot
from qts.runtime.actors.signal_aggregator_actor import (
    AggregatedSignalBatch,
    SignalAggregatorActor,
    SignalContribution,
    StrategySignalEvent,
)
from qts.runtime.broker_runtime_topology import (
    AccountRuntimePartition,
    BrokerRuntimeTopologyResolver,
    StrategyRuntimeBinding,
)
from qts.runtime.dependencies import RuntimeSessionDependencies
from qts.runtime.intent_processing import ProcessedIntent, TargetIntentProcessor
from qts.runtime.mailbox import Mailbox
from qts.runtime.market_data_flow import MarketDataFlow
from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
from qts.runtime.order_result import RuntimeOrderResult
from qts.runtime.safety import RuntimeKillSwitchEvidence
from qts.runtime.safety_port import RuntimeSafetyState
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext
from qts.runtime.startup_gate import BrokerRuntimeStartupGate
from qts.runtime.state import RuntimeSessionState, RuntimeStateMachine
from qts.runtime.state_recovery import StateSnapshot
from qts.runtime.topology import RuntimeTopology
from qts.strategy_sdk import TargetIntent


@dataclass(frozen=True, slots=True)
class RuntimeSessionResult:
    """Observable result from one paper/live market-data event."""

    market_data: tuple[Bar, ...] = ()
    orders: tuple[Order, ...] = ()
    fills: tuple[OrderFill, ...] = ()
    account_snapshot: AccountSnapshot | None = None
    account_snapshots: tuple[tuple[AccountId | None, AccountSnapshot], ...] = ()
    reason_code: str | None = None
    order_results: tuple[RuntimeOrderResult, ...] = ()


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

    run_id: str
    operator_id: str
    reason: str
    runtime_state: str
    event_store_paths: tuple[str, ...]
    active_order_ids: tuple[str, ...]
    snapshot_refs: tuple[str, ...]
    account_snapshot: AccountSnapshot


class RuntimeSession:
    """Run paper/live market data through the shared strategy/order actor chain."""

    def __init__(self, dependencies: RuntimeSessionDependencies) -> None:
        """Create the runtime session and its actor graph."""
        self._dependencies = dependencies
        self._topology = dependencies.runtime_topology
        self._resolved_account_id = dependencies.account_id
        self._resolved_strategy_id = dependencies.strategy_id
        self._strategy_bindings: tuple[StrategyRuntimeBinding, ...] = ()
        self._strategy_subscriptions: tuple[InstrumentId, ...] = ()
        self._account_partitions: dict[AccountId | None, AccountRuntimePartition] = {}
        self._intent_processors: dict[AccountId | None, TargetIntentProcessor] = {}
        self._latest_prices: dict[InstrumentId, Decimal] = {}
        self._event_index = 0
        self._runtime_event_sequence = 0
        self._order_sequence = 0
        self._safety_state = RuntimeSafetyState()
        resolved_topology = BrokerRuntimeTopologyResolver(dependencies).build()
        self._strategy_bindings = resolved_topology.strategy_bindings
        self._strategy_subscriptions = resolved_topology.strategy_subscriptions
        self._account_partitions = resolved_topology.account_partitions
        self._resolved_account_id = resolved_topology.resolved_account_id
        self._resolved_strategy_id = resolved_topology.resolved_strategy_id
        self._machine = RuntimeStateMachine()
        self._intent_processors = {
            account_id: TargetIntentProcessor(
                risk_engine=(
                    partition.risk_engine.requiring_live_market_data()
                    if self._requires_live_market_data_risk()
                    else partition.risk_engine
                ),
                instrument_context=dependencies.instrument_context,
                multiplier_for=dependencies.multiplier_for,
                broker_id=(
                    partition.broker_route.broker_id
                    if partition.broker_route is not None
                    else BrokerId("simulated")
                ),
                order_id_prefix=dependencies.order_id_prefix,
                broker_order_id_prefix=dependencies.order_id_prefix,
                margin_calculator=dependencies.margin_calculator,
                intraday_pnl_calculator=IntradayPnlCalculator(),
            )
            for account_id, partition in self._account_partitions.items()
        }
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
            session_window_by_instrument=dependencies.session_windows,
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
        from qts.runtime.actor_supervisor import RuntimeSupervisionCoordinator
        from qts.runtime.broker_lifecycle import RuntimeBrokerLifecycleCoordinator
        from qts.runtime.market_data_context import RuntimeMarketDataSessionContext
        from qts.runtime.market_data_coordinator import RuntimeMarketDataCoordinator
        from qts.runtime.recovery import RuntimeRecoveryCoordinator
        from qts.runtime.rollback import RuntimeRollbackCoordinator
        from qts.runtime.safety_controller import RuntimeSafetyController

        self._broker_lifecycle = RuntimeBrokerLifecycleCoordinator(self)
        self._recovery_coordinator = RuntimeRecoveryCoordinator(self)
        safety_port = _RuntimeSafetySessionAdapter(self)
        self._rollback_coordinator = RuntimeRollbackCoordinator(safety_port)
        self._safety_controller = RuntimeSafetyController(safety_port)
        self._supervision_coordinator = RuntimeSupervisionCoordinator(self)
        self._market_data_coordinator = RuntimeMarketDataCoordinator(
            RuntimeMarketDataSessionContext(self)
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
    def state(self) -> RuntimeSessionState:
        """Return the current runtime lifecycle state."""
        return self._machine.state

    @property
    def account_snapshot(self) -> AccountSnapshot:
        """Return the actor-owned account snapshot."""
        return self._primary_partition.account_ref.ask(GetAccountSnapshot())

    def start(self) -> RuntimeSessionState:
        """Start the session."""
        self._machine.apply("start")
        state = self._machine.apply("started")
        startup_blocked_reason = BrokerRuntimeStartupGate(
            mode=self._dependencies.mode,
            startup_decision=self._dependencies.startup_decision,
        ).blocked_reason()
        self._write_startup_gate_event()
        if startup_blocked_reason is not None:
            self._write_event(
                "runtime.startup_blocked",
                {"reason_code": startup_blocked_reason},
            )
            state = self.degrade()
        else:
            self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def stop(self) -> RuntimeSessionState:
        """Stop the session."""
        state = self._machine.apply("stop")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def pause(self) -> RuntimeSessionState:
        """Pause new strategy intent processing."""
        state = self._machine.apply("pause")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def resume(self) -> RuntimeSessionState:
        """Resume new strategy intent processing."""
        state = self._machine.apply("resume")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def degrade(self) -> RuntimeSessionState:
        """Degrade the session while keeping observability alive."""
        state = self._machine.apply("degrade")
        self._write_event("runtime.state_transition", {"state": state.value})
        return state

    def recover(self) -> RuntimeSessionState:
        """Recover a degraded session."""
        return self._recovery_coordinator.recover()

    def on_actor_failure(self, event: ActorFailureEvent) -> SupervisorDecision:
        """Route an actor failure through the supervisor and degrade if needed.

        This is the production caller for :class:`ActorSupervisor`: the supervisor
        records the failure, applies its restart policy, and returns a decision;
        a non-restart decision degrades the running/paused session so it stops
        accepting new work while observability stays alive.
        """
        return self._supervision_coordinator.on_actor_failure(event)

    def on_broker_disconnect(self, *, reason: str) -> RuntimeSessionState:
        """Mark the session degraded after broker connectivity is lost."""
        return self._broker_lifecycle.on_broker_disconnect(reason=reason)

    def on_broker_reconnect(
        self,
        *,
        reason: str,
    ) -> RuntimeSessionState:
        """Recover from broker reconnect only after reconciliation passes."""
        return self._broker_lifecycle.on_broker_reconnect(
            reason=reason,
        )

    def on_market_data_source_event(
        self,
        event: Bar
        | StreamingMarketDataDegradation
        | StreamingMarketDataSubscriptionEvent
        | MarketDataPermissionEvent,
    ) -> RuntimeSessionResult:
        """Handle a source market-data event, including degradation and permission signals."""
        return self._market_data_coordinator.on_market_data_source_event(event)

    def on_market_data(self, source_bar: Bar) -> RuntimeSessionResult:
        """Handle one source bar through market-data, strategy, risk, and actors."""
        return self._market_data_coordinator.on_market_data(source_bar)

    def activate_kill_switch(self, command: RuntimeKillSwitchCommand) -> RuntimeKillSwitchEvidence:
        """Block new orders and optionally cancel active orders through actors."""
        return self._safety_controller.activate_kill_switch(command)

    def rollback(self, command: RuntimeRollbackCommand) -> RuntimeRollbackEvidence:
        """Stop new orders and preserve rollback evidence."""
        return self._rollback_coordinator.rollback(command)

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
        aggregation_decision_id: str | None = None,
        conflict_reason: str | None = None,
    ) -> ProcessedIntent:
        self._order_sequence += 1
        try:
            intent_processor = self._intent_processors[partition.account_id]
        except KeyError as exc:
            raise ValueError(f"missing intent processor for account: {account_id}") from exc
        return intent_processor.process_intent(
            intent,
            bar=bar,
            account_ref=partition.account_ref,
            order_manager_ref=partition.order_manager_ref,
            execution_ref=partition.execution_ref,
            account_id=account_id,
            strategy_id=strategy_id,
            correlation_id=correlation_id,
            contributing_strategy_ids=contributing_strategy_ids,
            aggregation_decision_id=aggregation_decision_id,
            conflict_reason=conflict_reason,
            market_data_context=self._market_data_flow.risk_context_for(bar.instrument_id),
            order_number=self._order_sequence,
        )

    def _aggregate_signal_batches(
        self,
        bar: Bar,
        contributions: tuple[SignalContribution, ...],
        *,
        account_id: AccountId | None = None,
        correlation_id: CorrelationId | None = None,
    ) -> tuple[AggregatedSignalBatch, ...]:
        if not contributions:
            return ()
        self._signal_aggregator_ref.tell(
            StrategySignalEvent(
                bar=bar,
                contributions=contributions,
                account_id=account_id,
                correlation_id=correlation_id,
            )
        )
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
        return self._safety_controller.blocked_reason()

    def _write_startup_gate_event(self) -> None:
        decision = self._dependencies.startup_decision
        if decision is None:
            return
        payload = decision.checklist.to_payload()
        self._write_event(
            "runtime.startup_gate",
            {
                "status": decision.status.value,
                "order_permission": decision.order_permission.value,
                "real_order_submission_enabled": decision.real_order_submission_enabled,
                "checklist_hash": payload["checklist_hash"],
                "passed": payload["passed"],
                "checks": payload["checks"],
            },
        )

    def _permission_block_result(self, reason_code: str) -> RuntimeOrderResult:
        return RuntimeOrderResult(request=None, accepted=False, reason_code=reason_code)

    def _write_order_permission_blocked(
        self,
        reason_code: str,
        order_result: RuntimeOrderResult,
        *,
        correlation_id: CorrelationId,
        instrument_id: InstrumentId,
    ) -> None:
        decision = self._dependencies.startup_decision
        payload: dict[str, object] = {
            "reason_code": reason_code,
            "client_order_id": "permission-blocked",
            "runtime_order_result": order_result.to_evidence(),
        }
        if decision is not None:
            payload["order_permission"] = decision.order_permission.value
            payload["real_order_submission_enabled"] = decision.real_order_submission_enabled
            payload["startup_checklist"] = decision.checklist.to_payload()
        self._write_event(
            "order_blocked_by_permission",
            payload,
            correlation_id=correlation_id,
            instrument_id=instrument_id,
        )

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

    def _record_account_snapshots(self) -> tuple[str, ...]:
        snapshot_refs: list[str] = []
        for account_id, partition in self._account_partitions.items():
            if partition.snapshot_store is None:
                continue
            actor_id = self._account_snapshot_actor_id(account_id)
            snapshot: AccountSnapshot = partition.account_ref.ask(GetAccountSnapshot())
            partition.snapshot_store.save(
                StateSnapshot(
                    snapshot_id=actor_id,
                    actor_id=actor_id,
                    run_id=self._dependencies.run_id,
                    state_version=1,
                    last_sequence=self._runtime_event_sequence,
                    payload={
                        "cash": {
                            currency: str(balance) for currency, balance in snapshot.cash.items()
                        },
                        "positions": {
                            instrument_id.value: str(position.quantity)
                            for instrument_id, position in snapshot.positions.items()
                        },
                    },
                )
            )
            snapshot_refs.append(actor_id)
        return tuple(snapshot_refs)

    @staticmethod
    def _account_snapshot_actor_id(account_id: AccountId | None) -> str:
        if account_id is None:
            return "account:default"
        return f"account:{account_id.value}"

    def _requires_live_market_data_risk(self) -> bool:
        return (
            self._dependencies.mode is RuntimeMode.LIVE
            and self._dependencies.execution_environment is ExecutionEnvironment.BROKER
        )

    def _active_order_ids(self) -> tuple[str, ...]:
        terminal = {OrderState.FILLED, OrderState.CANCELLED, OrderState.REJECTED}
        active_order_ids: list[str] = []
        for partition in self._account_partitions.values():
            om_snapshot: OrderStateSnapshot = partition.order_manager_ref.ask(
                GetOrderManagerSnapshot()
            )
            for order in om_snapshot.orders:
                if order.state not in terminal:
                    active_order_ids.append(order.order_id.value)
        return tuple(active_order_ids)


class _RuntimeSafetySessionAdapter:
    """Adapt a ``RuntimeSession`` to ``RuntimeSafetySessionPort``.

    Owned by ``RuntimeSession`` and defined in this module, so it is the single
    place permitted to read the session's private safety collaborators on behalf
    of the safety/rollback coordinators, which see only the narrow port.
    """

    def __init__(self, session: RuntimeSession) -> None:
        self._session = session

    @property
    def safety_state(self) -> RuntimeSafetyState:
        """Return the session's owned kill-switch state."""
        return self._session._safety_state

    @property
    def runtime_state(self) -> RuntimeSessionState:
        """Return the current runtime lifecycle state."""
        return self._session.state

    @property
    def mode(self) -> RuntimeMode:
        """Return the runtime mode."""
        return self._session._dependencies.mode

    @property
    def startup_decision(self) -> object:
        """Return the broker startup decision."""
        return self._session._dependencies.startup_decision

    @property
    def run_id(self) -> str:
        """Return the run identifier value."""
        return self._session._dependencies.run_id.value

    @property
    def primary_partition(self) -> AccountRuntimePartition:
        """Return the primary account runtime partition."""
        return self._session._primary_partition

    def account_partitions(self) -> tuple[AccountRuntimePartition, ...]:
        """Return all account runtime partitions."""
        return tuple(self._session._account_partitions.values())

    def active_order_ids(self) -> tuple[str, ...]:
        """Return the ids of currently active orders."""
        return self._session._active_order_ids()

    def record_account_snapshots(self) -> tuple[str, ...]:
        """Persist account snapshots and return their evidence refs."""
        return self._session._record_account_snapshots()

    def write_event(self, kind: str, payload: Mapping[str, object]) -> None:
        """Append a normalized runtime event to the session event stream."""
        self._session._write_event(kind, dict(payload))


__all__ = [
    "RuntimeKillSwitchEvidence",
    "RuntimeRollbackCommand",
    "RuntimeRollbackEvidence",
    "RuntimeSession",
    "RuntimeSessionResult",
]
