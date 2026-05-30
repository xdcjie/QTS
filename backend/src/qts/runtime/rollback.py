"""Runtime rollback coordination and evidence capture."""

from __future__ import annotations

from qts.runtime.actors.account_actor import GetAccountSnapshot
from qts.runtime.safety_port import RuntimeSafetySessionPort
from qts.runtime.session import RuntimeRollbackCommand, RuntimeRollbackEvidence


class RuntimeRollbackCoordinator:
    """Own rollback fail-closed state and audit evidence.

    Depends on the narrow :class:`RuntimeSafetySessionPort`; it never touches
    ``RuntimeSession`` private attributes.
    """

    def __init__(self, port: RuntimeSafetySessionPort) -> None:
        self._port = port

    def rollback(self, command: RuntimeRollbackCommand) -> RuntimeRollbackEvidence:
        """Stop new orders and preserve rollback evidence."""
        port = self._port
        active_order_ids = port.active_order_ids()
        port.safety_state.activate_kill_switch()
        snapshot = port.primary_partition.account_ref.ask(GetAccountSnapshot())
        snapshot_refs = port.record_account_snapshots()
        evidence = RuntimeRollbackEvidence(
            run_id=port.run_id,
            operator_id=command.operator_id,
            reason=command.reason,
            runtime_state=port.runtime_state.value,
            event_store_paths=tuple(str(path) for path in command.event_store_paths),
            active_order_ids=active_order_ids,
            snapshot_refs=snapshot_refs,
            account_snapshot=snapshot,
        )
        port.write_event(
            "runtime.rollback",
            {
                "run_id": evidence.run_id,
                "operator_id": evidence.operator_id,
                "reason": evidence.reason,
                "runtime_state": evidence.runtime_state,
                "event_store_paths": list(evidence.event_store_paths),
                "active_order_ids": list(evidence.active_order_ids),
                "snapshot_refs": list(evidence.snapshot_refs),
                "cash": {
                    currency: str(balance)
                    for currency, balance in evidence.account_snapshot.cash.items()
                },
            },
        )
        return evidence


__all__ = ["RuntimeRollbackCoordinator"]
