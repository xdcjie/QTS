"""Runtime rollback coordination and evidence capture."""

from __future__ import annotations

from typing import Any

from qts.runtime.session import RuntimeRollbackCommand, RuntimeRollbackEvidence


class RuntimeRollbackCoordinator:
    """Own rollback fail-closed state and audit evidence."""

    def __init__(self, session: Any) -> None:
        self._session = session

    def rollback(self, command: RuntimeRollbackCommand) -> RuntimeRollbackEvidence:
        """Stop new orders and preserve rollback evidence."""
        session = self._session
        active_order_ids = session._active_order_ids()
        session._kill_switch_active = True
        snapshot = session._primary_partition.account_actor.snapshot()
        snapshot_refs = session._record_account_snapshots()
        evidence = RuntimeRollbackEvidence(
            run_id=session._dependencies.run_id.value,
            operator_id=command.operator_id,
            reason=command.reason,
            runtime_state=session.state.value,
            event_store_paths=tuple(str(path) for path in command.event_store_paths),
            active_order_ids=active_order_ids,
            snapshot_refs=snapshot_refs,
            account_snapshot=snapshot,
        )
        session._write_event(
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
