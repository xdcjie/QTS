"""Runtime lifecycle application command owner."""

from __future__ import annotations

from datetime import datetime
from types import MappingProxyType

from qts.runtime.commands import (
    RuntimeCommand,
    RuntimeCommandResult,
    RuntimeCommandResultStatus,
    RuntimeCommandType,
)


class RuntimeLifecycleService:
    """Owns runtime lifecycle state transitions for operator commands."""

    _STATE_BY_COMMAND = MappingProxyType(
        {
            RuntimeCommandType.START: "running",
            RuntimeCommandType.STOP: "stopped",
            RuntimeCommandType.PAUSE: "paused",
            RuntimeCommandType.RESUME: "running",
            RuntimeCommandType.ENTER_OBSERVATION: "observation",
            RuntimeCommandType.EXIT_OBSERVATION: "running",
        }
    )

    def __init__(self, *, initial_state: str = "running") -> None:
        if not initial_state.strip():
            raise ValueError("initial_state must not be empty")
        self._state = initial_state

    @property
    def state(self) -> str:
        """Return the current runtime lifecycle state."""
        return self._state

    def handle(
        self,
        command: RuntimeCommand,
        *,
        accepted_at: datetime,
    ) -> RuntimeCommandResult | None:
        """Apply a lifecycle command or return None for commands owned elsewhere."""
        state = self._STATE_BY_COMMAND.get(command.command_type)
        if state is None:
            return None
        self._state = state
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            completed_at=accepted_at,
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence=self._command_evidence(command, {"state": self._state}),
        )

    @staticmethod
    def _command_evidence(
        command: RuntimeCommand,
        evidence: dict[str, object],
    ) -> dict[str, object]:
        return {
            "runtime_instance_id": command.runtime_instance_id,
            "operator_id": command.operator_id,
            "operator_role": command.operator_role,
            "authorization_scope": command.authorization_scope,
            **evidence,
        }


__all__ = ["RuntimeLifecycleService"]
