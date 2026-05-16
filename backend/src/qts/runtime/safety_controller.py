"""Runtime order-safety gates and operator safety actions."""

from __future__ import annotations

from typing import Any

from qts.core.ids import OrderId
from qts.domain.orders import CancelIntent
from qts.execution.order_state_machine import OrderState
from qts.risk.kill_switch import RuntimeKillSwitchCommand
from qts.runtime.actors.order_manager_actor import CancelOrder
from qts.runtime.broker_runtime_topology import AccountRuntimePartition
from qts.runtime.safety import RuntimeKillSwitchEvidence
from qts.runtime.startup_gate import BrokerRuntimeStartupGate
from qts.runtime.state import RuntimeSessionState


class RuntimeSafetyController:
    """Own runtime safety gates that block or cancel order submission."""

    def __init__(self, session: Any) -> None:
        self._session = session

    def blocked_reason(self) -> str | None:
        """Return the current order-blocking reason code, if any."""
        session = self._session
        if session._kill_switch_active:
            return "KILL_SWITCH_ACTIVE"
        if session.state is RuntimeSessionState.PAUSED:
            return "RUNTIME_PAUSED"
        if session.state is RuntimeSessionState.DEGRADED:
            return "RUNTIME_DEGRADED"
        if session.state is not RuntimeSessionState.RUNNING:
            return "RUNTIME_NOT_RUNNING"
        return BrokerRuntimeStartupGate(
            mode=session._dependencies.mode,
            startup_decision=session._dependencies.startup_decision,
        ).blocked_reason()

    def activate_kill_switch(
        self,
        command: RuntimeKillSwitchCommand,
    ) -> RuntimeKillSwitchEvidence:
        """Block new orders and optionally cancel active orders through actors."""
        session = self._session
        session._kill_switch_active = True
        active_order_ids = session._active_order_ids()
        cancelled_order_ids: list[str] = []
        if command.cancel_active_orders:
            active_orders_by_partition: list[tuple[str, AccountRuntimePartition]] = []
            for partition in session._account_partitions.values():
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
            for partition in session._account_partitions.values():
                partition.order_manager_ref.process_all()
                partition.execution_ref.process_all()
                partition.order_manager_ref.process_all()
                partition.account_ref.process_all()
            for order_id, partition in active_orders_by_partition:
                order = partition.order_manager_actor.get_order(OrderId(order_id))
                if order.state is OrderState.CANCELLED:
                    cancelled_order_ids.append(order_id)
            active_order_ids = tuple(order_id for order_id, _ in active_orders_by_partition)
        snapshot = session._primary_partition.account_actor.snapshot()
        evidence = RuntimeKillSwitchEvidence(
            operator_id=command.operator_id,
            reason=command.reason,
            runtime_state=session.state.value,
            active_order_ids=tuple(active_order_ids),
            cancelled_order_ids=tuple(cancelled_order_ids),
            account_snapshot=snapshot,
        )
        session._write_event(
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


__all__ = ["RuntimeSafetyController"]
