"""Operation command handling owner."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from qts.application.services.kill_switch_commands import KillSwitchCommandService
from qts.application.services.runtime_lifecycle import RuntimeLifecycleService
from qts.runtime.commands import (
    RuntimeCommand,
    RuntimeCommandResult,
    RuntimeCommandResultStatus,
    RuntimeCommandType,
)


class OperationsCommandHandler:
    """Owns operation command dispatch after idempotency and authorization."""

    def __init__(
        self,
        *,
        lifecycle: RuntimeLifecycleService,
        kill_switch_commands: KillSwitchCommandService,
    ) -> None:
        self._lifecycle = lifecycle
        self._kill_switch_commands = kill_switch_commands

    def handle(self, command: RuntimeCommand) -> RuntimeCommandResult:
        """Handle one authorized operation command."""
        accepted_at = datetime.now(UTC)
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
