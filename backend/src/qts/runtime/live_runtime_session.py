"""Shared paper/live runtime session orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from qts.core.ids import InstrumentId, OrderId
from qts.domain.market_data import Bar
from qts.domain.orders import CancelIntent
from qts.execution.order_manager import Order, OrderFill
from qts.execution.order_state_machine import OrderState
from qts.risk.kill_switch import RuntimeKillSwitchCommand
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import CancelOrder, OrderManagerActor
from qts.runtime.intent_processing import ProcessedIntent, TargetIntentProcessor
from qts.runtime.live import LiveRuntimeState, LiveRuntimeStateMachine
from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
from qts.runtime.mailbox import Mailbox
from qts.runtime.market_data_flow import MarketDataFlow
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline
from qts.strategy_sdk import TargetIntent


@dataclass(frozen=True, slots=True)
class LiveRuntimeSessionResult:
    """Observable result from one paper/live market-data event."""

    market_data: tuple[Bar, ...] = ()
    orders: tuple[Order, ...] = ()
    fills: tuple[OrderFill, ...] = ()
    account_snapshot: AccountSnapshot | None = None
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
        self._machine = LiveRuntimeStateMachine()
        self._latest_prices: dict[InstrumentId, Decimal] = {}
        self._event_index = 0
        self._order_sequence = 0
        self._kill_switch_active = False
        self._account_actor = dependencies.account_actor
        self._account_ref = ActorRef(actor=self._account_actor, mailbox=Mailbox())
        self._execution_mailbox = Mailbox()
        self._order_manager_mailbox = Mailbox()
        self._order_manager_actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=self._execution_mailbox),
            account_ref=self._account_ref,
            multiplier_by_instrument=dependencies.multipliers,
        )
        self._order_manager_ref = ActorRef(
            actor=self._order_manager_actor,
            mailbox=self._order_manager_mailbox,
        )
        self._execution_ref = ActorRef(
            actor=ExecutionActor(
                order_manager_ref=self._order_manager_ref,
                execution_adapter=dependencies.execution_adapter,
            ),
            mailbox=self._execution_mailbox,
        )
        self._strategy_pipeline = StrategyExecutionPipeline(
            strategy=dependencies.strategy,
            instrument_registry=dependencies.instrument_registry,
            future_chain_registry=dependencies.future_roll_registry,
            portfolio_view=dependencies.portfolio_view,
            prune_history=True,
        )
        self._intent_processor = TargetIntentProcessor(
            risk_engine=dependencies.risk_engine,
            instrument_context=dependencies.instrument_context,
            multiplier_for=dependencies.multiplier_for,
            order_id_prefix=dependencies.order_id_prefix,
            broker_order_id_prefix=dependencies.order_id_prefix,
        )
        self._market_data_flow = MarketDataFlow(
            target_timeframe=dependencies.target_timeframe,
            exchange_timezone_by_instrument=dependencies.exchange_timezones,
        )

    @property
    def state(self) -> LiveRuntimeState:
        """Return the current runtime lifecycle state."""
        return self._machine.state

    @property
    def account_snapshot(self) -> AccountSnapshot:
        """Return the actor-owned account snapshot."""
        return self._account_actor.snapshot()

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

    def on_market_data(self, source_bar: Bar) -> LiveRuntimeSessionResult:
        """Handle one source bar through market-data, strategy, risk, and actors."""
        flow_result = self._market_data_flow.publish_source_event(source_bar)
        for event in flow_result.runtime_events:
            self._write(event)
            if event.kind == "runtime.degraded" and self.state is not LiveRuntimeState.DEGRADED:
                self.degrade()

        bars = flow_result.market_data
        all_orders: list[Order] = []
        all_fills: list[OrderFill] = []
        reason_code: str | None = None
        for bar in bars:
            self._latest_prices[bar.instrument_id] = bar.close
            self._write_event(
                "runtime.market_data",
                {
                    "instrument_id": bar.instrument_id.value,
                    "timeframe": bar.timeframe,
                    "end_time": bar.end_time.isoformat(),
                },
            )
            blocked_reason = self._blocked_reason()
            if blocked_reason is not None:
                reason_code = blocked_reason
                continue
            strategy_result = self._strategy_pipeline.execute_bar(
                bar,
                account_snapshot=self._account_actor.snapshot(),
                latest_prices=self._latest_prices,
                aggregate_signals=self._event_index >= self._dependencies.warmup_bars,
            )
            for intent in strategy_result.intents:
                self._write_event(
                    "runtime.strategy_intent",
                    {
                        "instrument_id": intent.asset.instrument_id.value,
                        "intent_type": intent.intent_type.value,
                        "value": str(intent.value) if intent.value is not None else None,
                    },
                )
                if not self._dependencies.order_submission_enabled:
                    reason_code = "ORDER_SUBMISSION_DISABLED"
                    continue
                processed = self._process_intent(intent, bar)
                all_orders.extend(processed.orders)
                all_fills.extend(processed.fills)
                for order in processed.orders:
                    self._write_event(
                        "runtime.order_submitted",
                        {
                            "order_id": order.order_id.value,
                            "broker_order_id": order.broker_order_id,
                            "instrument_id": order.intent.instrument_id.value,
                        },
                    )
                    self._write_event(
                        "runtime.broker_report",
                        {
                            "order_id": order.order_id.value,
                            "state": order.state.value,
                            "broker_order_id": order.broker_order_id,
                        },
                    )
            self._event_index += 1

        snapshot = self._account_actor.snapshot()
        if bars:
            self._write_event(
                "runtime.account_snapshot",
                {
                    "cash": {currency: str(balance) for currency, balance in snapshot.cash.items()},
                    "positions": {
                        instrument_id.value: str(position.quantity)
                        for instrument_id, position in snapshot.positions.items()
                    },
                },
            )
        return LiveRuntimeSessionResult(
            market_data=bars,
            orders=tuple(all_orders),
            fills=tuple(all_fills),
            account_snapshot=snapshot,
            reason_code=reason_code,
        )

    def activate_kill_switch(self, command: RuntimeKillSwitchCommand) -> LiveKillSwitchEvidence:
        """Block new orders and optionally cancel active orders through actors."""
        self._kill_switch_active = True
        active_order_ids = self._active_order_ids()
        cancelled_order_ids: list[str] = []
        if command.cancel_active_orders:
            for order_id in active_order_ids:
                self._order_manager_ref.tell(CancelOrder(CancelIntent(order_id=OrderId(order_id))))
            self._order_manager_ref.process_all()
            self._execution_ref.process_all()
            self._order_manager_ref.process_all()
            self._account_ref.process_all()
            cancelled_order_ids = [
                order_id
                for order_id in active_order_ids
                if self._order_manager_actor.get_order(OrderId(order_id)).state
                is OrderState.CANCELLED
            ]
        snapshot = self._account_actor.snapshot()
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
        snapshot = self._account_actor.snapshot()
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

    def _process_intent(self, intent: TargetIntent, bar: Bar) -> ProcessedIntent:
        self._order_sequence += 1
        return self._intent_processor.process_intent(
            intent,
            bar=bar,
            account_actor=self._account_actor,
            order_manager_actor=self._order_manager_actor,
            order_manager_ref=self._order_manager_ref,
            execution_ref=self._execution_ref,
            account_ref=self._account_ref,
            order_number=self._order_sequence,
        )

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

    def _write_event(self, kind: str, payload: dict[str, object]) -> None:
        self._write(RuntimeEvent(kind=kind, payload=payload))

    def _write(self, event: RuntimeEvent) -> None:
        sink = self._dependencies.sink
        if sink is not None:
            sink.write(event)

    def _active_order_ids(self) -> tuple[str, ...]:
        terminal = {OrderState.FILLED, OrderState.CANCELLED, OrderState.REJECTED}
        return tuple(
            order.order_id.value
            for order in self._order_manager_actor.snapshot().orders
            if order.state not in terminal
        )


__all__ = [
    "LiveKillSwitchEvidence",
    "LiveRuntimeSession",
    "LiveRuntimeSessionResult",
    "RuntimeRollbackCommand",
    "RuntimeRollbackEvidence",
]
