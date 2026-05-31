"""Operation command handling owner."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from qts.application.services.kill_switch_commands import KillSwitchCommandService
from qts.application.services.runtime_lifecycle import RuntimeLifecycleService
from qts.risk.kill_switch import RuntimeKillSwitchCommand
from qts.runtime.commands import (
    RuntimeCommand,
    RuntimeCommandResult,
    RuntimeCommandResultStatus,
    RuntimeCommandType,
)
from qts.runtime.control_plane import RuntimeCommandExecutor
from qts.runtime.errors import RuntimeCommandNotBound
from qts.runtime.state import RuntimeSessionState

_RUNTIME_LIFECYCLE_COMMANDS = frozenset(
    {
        RuntimeCommandType.START,
        RuntimeCommandType.STOP,
        RuntimeCommandType.PAUSE,
        RuntimeCommandType.RESUME,
    }
)


class OperationsCommandHandler:
    """Owns operation command dispatch after idempotency and authorization.

    Lifecycle (start/stop/pause/resume) and kill-switch *activation* are routed to
    a real RuntimeSession through ``RuntimeCommandExecutor`` so a COMPLETED result
    always reflects a runtime effect; with no runtime bound they raise
    ``RuntimeCommandNotBound`` (surfaced as ``RUNTIME_SESSION_NOT_BOUND``) rather
    than mutating shadow state. Observation, kill-switch deactivation, reconcile,
    and snapshot keep their application-owned command handling.
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
        lifecycle_result = self._lifecycle.handle(command, accepted_at=accepted_at)
        if lifecycle_result is not None:
            return lifecycle_result
        kill_switch_result = self._kill_switch_commands.handle(command, accepted_at=accepted_at)
        if kill_switch_result is not None:
            return kill_switch_result
        if command.command_type is RuntimeCommandType.RECONCILE:
            evidence = self._command_evidence(
                command,
                {"state": self._lifecycle.state, "reconciliation": "requested"},
            )
        elif command.command_type is RuntimeCommandType.SNAPSHOT:
            evidence = self._command_evidence(
                command,
                {"state": self._lifecycle.state, "snapshot": "requested"},
            )
        else:
            return self._rejected_result(
                command,
                accepted_at=accepted_at,
                failure_reason=f"unsupported runtime command: {command.command_type.value}",
            )
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            completed_at=datetime.now(UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence=evidence,
        )

    def _execute_runtime_lifecycle(
        self, command: RuntimeCommand, *, accepted_at: datetime
    ) -> RuntimeCommandResult:
        """Apply a lifecycle command to the bound runtime session, or fail unbound."""
        executor = self._require_executor(command)
        lifecycle_methods: dict[RuntimeCommandType, Callable[[], RuntimeSessionState]] = {
            RuntimeCommandType.START: executor.start,
            RuntimeCommandType.STOP: executor.stop,
            RuntimeCommandType.PAUSE: executor.pause,
            RuntimeCommandType.RESUME: executor.resume,
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
        executor = self._require_executor(command)
        reason = command.reason or str(command.payload.get("reason") or "operator kill switch")
        evidence = executor.activate_kill_switch(
            RuntimeKillSwitchCommand(operator_id=command.operator_id, reason=reason)
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

    def _require_executor(self, command: RuntimeCommand) -> RuntimeCommandExecutor:
        if self._command_executor is None:
            raise RuntimeCommandNotBound(
                "RUNTIME_SESSION_NOT_BOUND: no runtime session is bound to apply "
                f"{command.command_type.value}"
            )
        return self._command_executor

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
