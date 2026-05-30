"""Runtime order-safety gates and operator safety actions."""

from __future__ import annotations

from typing import cast

from qts.core.ids import OrderId
from qts.domain.orders import CancelIntent, OrderState
from qts.risk.kill_switch import RuntimeKillSwitchCommand
from qts.runtime.actors.account_actor import GetAccountSnapshot
from qts.runtime.actors.order_manager_actor import (
    CancelOrder,
    GetOrder,
    GetOrderManagerSnapshot,
    GetRouteMetadata,
)
from qts.runtime.broker_runtime_topology import AccountRuntimePartition
from qts.runtime.broker_startup import BrokerRuntimeStartupDecision
from qts.runtime.order_route_metadata import OrderRouteMetadata
from qts.runtime.safety import RuntimeKillSwitchDeactivateCommand, RuntimeKillSwitchEvidence
from qts.runtime.safety_port import RuntimeSafetySessionPort
from qts.runtime.startup_gate import BrokerRuntimeStartupGate
from qts.runtime.state import RuntimeSessionState


class RuntimeSafetyController:
    """Own runtime safety gates that block or cancel order submission.

    Depends on the narrow :class:`RuntimeSafetySessionPort`; it never touches
    ``RuntimeSession`` private attributes.
    """

    def __init__(self, port: RuntimeSafetySessionPort) -> None:
        self._port = port

    def blocked_reason(self) -> str | None:
        """Return the current order-blocking reason code, if any."""
        port = self._port
        if port.safety_state.kill_switch_active:
            return "KILL_SWITCH_ACTIVE"
        if port.runtime_state is RuntimeSessionState.PAUSED:
            return "RUNTIME_PAUSED"
        if port.runtime_state not in {RuntimeSessionState.RUNNING, RuntimeSessionState.DEGRADED}:
            return "RUNTIME_NOT_RUNNING"
        startup_reason = BrokerRuntimeStartupGate(
            mode=port.mode,
            startup_decision=cast(BrokerRuntimeStartupDecision | None, port.startup_decision),
        ).blocked_reason()
        if startup_reason is not None:
            return startup_reason
        if port.runtime_state is RuntimeSessionState.DEGRADED:
            return "RUNTIME_DEGRADED"
        return None

    def activate_kill_switch(
        self,
        command: RuntimeKillSwitchCommand,
    ) -> RuntimeKillSwitchEvidence:
        """Block new orders and optionally cancel active orders through actors."""
        port = self._port
        port.safety_state.activate_kill_switch()
        active_order_ids = port.active_order_ids()
        cancelled_order_ids: list[str] = []
        if command.cancel_active_orders:
            active_orders_by_partition: list[tuple[str, AccountRuntimePartition]] = []
            for partition in port.account_partitions():
                om_snapshot = partition.order_manager_ref.ask(GetOrderManagerSnapshot())
                for order in om_snapshot.orders:
                    if order.state in {
                        OrderState.FILLED,
                        OrderState.CANCELLED,
                        OrderState.REJECTED,
                    }:
                        continue
                    active_orders_by_partition.append((order.order_id.value, partition))
            for order_id, partition in active_orders_by_partition:
                metadata: OrderRouteMetadata = partition.order_manager_ref.ask(
                    GetRouteMetadata(order_id=OrderId(order_id))
                )
                partition.order_manager_ref.tell(
                    CancelOrder(
                        CancelIntent(order_id=OrderId(order_id)),
                        account_id=metadata.account_id,
                        strategy_id=metadata.strategy_id,
                        route_metadata=metadata,
                    )
                )
            for partition in port.account_partitions():
                partition.order_manager_ref.process_all()
                partition.execution_ref.process_all()
                partition.order_manager_ref.process_all()
                partition.account_ref.process_all()
            for order_id, partition in active_orders_by_partition:
                order = partition.order_manager_ref.ask(GetOrder(order_id=OrderId(order_id)))
                if order.state is OrderState.CANCELLED:
                    cancelled_order_ids.append(order_id)
            active_order_ids = tuple(order_id for order_id, _ in active_orders_by_partition)
        snapshot = port.primary_partition.account_ref.ask(GetAccountSnapshot())
        snapshot_refs = port.record_account_snapshots()
        evidence = RuntimeKillSwitchEvidence(
            run_id=port.run_id,
            operator_id=command.operator_id,
            reason=command.reason,
            runtime_state=port.runtime_state.value,
            active_order_ids=tuple(active_order_ids),
            cancelled_order_ids=tuple(cancelled_order_ids),
            account_snapshot=snapshot,
            snapshot_refs=snapshot_refs,
        )
        port.write_event(
            "runtime.kill_switch",
            {
                "run_id": evidence.run_id,
                "operator_id": evidence.operator_id,
                "reason": evidence.reason,
                "runtime_state": evidence.runtime_state,
                "active_order_ids": list(evidence.active_order_ids),
                "cancelled_order_ids": list(evidence.cancelled_order_ids),
                "snapshot_refs": list(evidence.snapshot_refs),
                "cash": {
                    currency: str(balance)
                    for currency, balance in evidence.account_snapshot.cash.items()
                },
            },
        )
        return evidence

    def activate_kill_switch_via_persistent_drift(self, *, key: str, reason: str) -> None:
        """Activate the kill switch from a persistent reconciliation-drift event.

        This is the production-side adapter consumed by
        :class:`qts.reconciliation.persistent_drift_coordinator.PersistentDriftCoordinator`.
        It wraps :meth:`activate_kill_switch` with a system-identity command so
        the existing audit trail (``runtime.kill_switch`` event + snapshot
        refs) records the trigger as drift-driven rather than operator-driven.
        """
        self.activate_kill_switch(
            RuntimeKillSwitchCommand(
                operator_id="system:persistent_drift",
                reason=f"persistent drift key={key}: {reason}",
                cancel_active_orders=True,
            )
        )

    def deactivate_kill_switch(self, command: RuntimeKillSwitchDeactivateCommand) -> None:
        """Resume order submission only after explicit safety authorization."""
        if not command.authorized:
            raise PermissionError("kill switch deactivate requires safety authorization")
        port = self._port
        port.safety_state.deactivate_kill_switch()
        port.write_event(
            "runtime.kill_switch_deactivated",
            {
                "run_id": port.run_id,
                "operator_id": command.operator_id,
                "reason": command.reason,
            },
        )


__all__ = ["RuntimeSafetyController"]
