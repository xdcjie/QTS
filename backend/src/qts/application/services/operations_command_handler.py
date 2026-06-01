"""Operation command handling owner."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal

from qts.application.services.kill_switch_commands import KillSwitchCommandService
from qts.application.services.runtime_lifecycle import RuntimeLifecycleService
from qts.portfolio.account_snapshot import AccountSnapshot
from qts.risk.kill_switch import RuntimeKillSwitchCommand
from qts.runtime.commands import (
    RuntimeCommand,
    RuntimeCommandResult,
    RuntimeCommandResultStatus,
    RuntimeCommandType,
)
from qts.runtime.control_plane import RuntimeCommandExecutor, RuntimeSessionKey
from qts.runtime.errors import RuntimeCommandNotBound
from qts.runtime.safety import RuntimeKillSwitchDeactivateCommand
from qts.runtime.state import RuntimeSessionState

_RUNTIME_LIFECYCLE_COMMANDS = frozenset(
    {
        RuntimeCommandType.START,
        RuntimeCommandType.STOP,
        RuntimeCommandType.PAUSE,
        RuntimeCommandType.RESUME,
        RuntimeCommandType.ENTER_OBSERVATION,
        RuntimeCommandType.EXIT_OBSERVATION,
    }
)


class OperationsCommandHandler:
    """Owns operation command dispatch after idempotency and authorization.

    Every operator command is routed to a real RuntimeSession through
    ``RuntimeCommandExecutor`` so a COMPLETED result always reflects a runtime
    effect; with no runtime bound the handler raises ``RuntimeCommandNotBound``
    and ``RuntimeCommandBus`` surfaces ``RUNTIME_SESSION_NOT_BOUND`` rather than
    mutating shadow application state.
    """

    def __init__(
        self,
        *,
        lifecycle: RuntimeLifecycleService,
        kill_switch_commands: KillSwitchCommandService,
        command_executor: RuntimeCommandExecutor | None = None,
    ) -> None:
        self._lifecycle = lifecycle
        self._kill_switch_commands = kill_switch_commands
        self._command_executor = command_executor

    def handle(self, command: RuntimeCommand) -> RuntimeCommandResult:
        """Handle one authorized operation command."""
        accepted_at = datetime.now(UTC)
        if command.command_type in _RUNTIME_LIFECYCLE_COMMANDS:
            return self._execute_runtime_lifecycle(command, accepted_at=accepted_at)
        if command.command_type is RuntimeCommandType.ACTIVATE_KILL_SWITCH:
            return self._execute_kill_switch(command, accepted_at=accepted_at)
        if command.command_type is RuntimeCommandType.RECONCILE:
            return self._execute_reconcile(command, accepted_at=accepted_at)
        elif command.command_type is RuntimeCommandType.SNAPSHOT:
            return self._execute_snapshot(command, accepted_at=accepted_at)
        elif command.command_type is RuntimeCommandType.DEACTIVATE_KILL_SWITCH:
            return self._execute_kill_switch_deactivation(command, accepted_at=accepted_at)
        else:
            return self._rejected_result(
                command,
                accepted_at=accepted_at,
                failure_reason=f"unsupported runtime command: {command.command_type.value}",
            )

    def _execute_runtime_lifecycle(
        self, command: RuntimeCommand, *, accepted_at: datetime
    ) -> RuntimeCommandResult:
        """Apply a lifecycle command to the bound runtime session, or fail unbound."""
        executor, key = self._require_executor(command)
        lifecycle_methods: dict[RuntimeCommandType, Callable[[], RuntimeSessionState]] = {
            RuntimeCommandType.START: lambda: executor.start(key=key),
            RuntimeCommandType.STOP: lambda: executor.stop(key=key),
            RuntimeCommandType.PAUSE: lambda: executor.pause(key=key),
            RuntimeCommandType.RESUME: lambda: executor.resume(key=key),
            RuntimeCommandType.ENTER_OBSERVATION: lambda: executor.enter_observation(key=key),
            RuntimeCommandType.EXIT_OBSERVATION: lambda: executor.exit_observation(key=key),
        }
        state = lifecycle_methods[command.command_type]()
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            completed_at=datetime.now(UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence=self._command_evidence(command, {"state": state.value}),
        )

    def _execute_kill_switch(
        self, command: RuntimeCommand, *, accepted_at: datetime
    ) -> RuntimeCommandResult:
        """Activate the kill switch on the bound runtime session, or fail unbound."""
        executor, key = self._require_executor(command)
        reason = command.reason or str(command.payload.get("reason") or "operator kill switch")
        evidence = executor.activate_kill_switch(
            RuntimeKillSwitchCommand(operator_id=command.operator_id, reason=reason),
            key=key,
        )
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            completed_at=datetime.now(UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence=self._command_evidence(
                command,
                {
                    "scope": command.payload.get("scope"),
                    "scope_id": command.payload.get("scope_id"),
                    "active": True,
                    "reason": reason,
                    "runtime_state": evidence.runtime_state,
                    "cancelled_order_ids": list(evidence.cancelled_order_ids),
                },
            ),
        )

    def _execute_kill_switch_deactivation(
        self,
        command: RuntimeCommand,
        *,
        accepted_at: datetime,
    ) -> RuntimeCommandResult:
        """Deactivate the kill switch on the bound runtime session, or fail unbound."""
        executor, key = self._require_executor(command)
        reason = command.reason or str(command.payload.get("reason") or "operator resume")
        state = executor.deactivate_kill_switch(
            RuntimeKillSwitchDeactivateCommand(
                operator_id=command.operator_id,
                reason=reason,
                authorized=True,
            ),
            key=key,
        )
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            completed_at=datetime.now(UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence=self._command_evidence(
                command,
                {
                    "scope": command.payload.get("scope"),
                    "scope_id": command.payload.get("scope_id"),
                    "active": False,
                    "reason": reason,
                    "runtime_state": state.value,
                },
            ),
        )

    def _execute_reconcile(
        self,
        command: RuntimeCommand,
        *,
        accepted_at: datetime,
    ) -> RuntimeCommandResult:
        """Reconcile the bound runtime session, or fail unbound."""
        executor, key = self._require_executor(command)
        state = executor.reconcile(key=key)
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            completed_at=datetime.now(UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence=self._command_evidence(
                command,
                {"state": state.value, "reconciliation": "completed"},
            ),
        )

    def _execute_snapshot(
        self,
        command: RuntimeCommand,
        *,
        accepted_at: datetime,
    ) -> RuntimeCommandResult:
        """Snapshot the bound runtime session, or fail unbound."""
        executor, key = self._require_executor(command)
        snapshot = executor.snapshot(key=key)
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            completed_at=datetime.now(UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence=self._command_evidence(command, self._snapshot_evidence(snapshot)),
        )

    def _require_executor(
        self, command: RuntimeCommand
    ) -> tuple[RuntimeCommandExecutor, RuntimeSessionKey]:
        if self._command_executor is None:
            raise RuntimeCommandNotBound(
                "RUNTIME_SESSION_NOT_BOUND: no runtime session is bound to apply "
                f"{command.command_type.value}"
            )
        return self._command_executor, RuntimeSessionKey(
            runtime_instance_id=command.runtime_instance_id
        )

    @staticmethod
    def _command_evidence(
        command: RuntimeCommand,
        evidence: Mapping[str, object],
    ) -> dict[str, object]:
        return {
            "runtime_instance_id": command.runtime_instance_id,
            "operator_id": command.operator_id,
            "operator_role": command.operator_role,
            "authorization_scope": command.authorization_scope,
            **dict(evidence),
        }

    @staticmethod
    def _snapshot_evidence(snapshot: object) -> dict[str, object]:
        if isinstance(snapshot, AccountSnapshot):
            payload: dict[str, object] = {
                "snapshot": "captured",
                "cash": {
                    currency: OperationsCommandHandler._evidence_scalar(balance)
                    for currency, balance in snapshot.cash.items()
                },
                "positions": {
                    instrument_id.value: OperationsCommandHandler._evidence_scalar(holding.quantity)
                    for instrument_id, holding in snapshot.positions.items()
                },
            }
            if snapshot.account_id is not None:
                payload["account_id"] = snapshot.account_id.value
            return payload
        if isinstance(snapshot, Mapping):
            return {"snapshot": "captured", "account_snapshot": dict(snapshot)}
        return {"snapshot": "captured", "account_snapshot": repr(snapshot)}

    @staticmethod
    def _evidence_scalar(value: object) -> object:
        if isinstance(value, Decimal):
            return str(value)
        return value

    @staticmethod
    def _rejected_result(
        command: RuntimeCommand,
        *,
        accepted_at: datetime,
        failure_reason: str,
    ) -> RuntimeCommandResult:
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            result_status=RuntimeCommandResultStatus.REJECTED,
            failure_reason=failure_reason,
        )


__all__ = ["OperationsCommandHandler"]
