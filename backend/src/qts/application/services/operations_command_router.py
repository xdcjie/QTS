"""Idempotent operation command submission owner."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from qts.application.dto import RuntimeCommandResultDTO, RuntimeStateDTO
from qts.runtime.commands import (
    RuntimeCommand,
    RuntimeCommandBus,
    RuntimeCommandResult,
    RuntimeCommandType,
)


class OperationsCommandRouter:
    """Owns idempotent runtime command submission for application services."""

    def __init__(self, *, handler: Callable[[RuntimeCommand], RuntimeCommandResult]) -> None:
        self._command_sequence = 0
        self._command_bus = RuntimeCommandBus(handler=handler)

    def submit_state(
        self,
        command_type: RuntimeCommandType,
        *,
        runtime_instance_id: str,
        operator_id: str,
        idempotency_key: str | None,
    ) -> RuntimeStateDTO:
        """Submit a lifecycle command and return the stable state DTO."""
        result = self.submit(
            command_type,
            runtime_instance_id=runtime_instance_id,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )
        state = result.evidence.get("state")
        if not isinstance(state, str):
            return RuntimeStateDTO(state=result.result_status.value)
        return RuntimeStateDTO(state=state)

    def submit(
        self,
        command_type: RuntimeCommandType,
        *,
        runtime_instance_id: str,
        operator_id: str,
        operator_role: str = "operator",
        authorization_scope: str = "runtime:operator",
        approved_by: str | None = None,
        approval_required: bool = False,
        idempotency_key: str | None,
        reason: str | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> RuntimeCommandResult:
        """Submit a command through the idempotent command bus."""
        command_id = self._next_command_id(command_type)
        return self._command_bus.submit(
            RuntimeCommand(
                command_id=command_id,
                command_type=command_type,
                runtime_instance_id=runtime_instance_id,
                idempotency_key=idempotency_key or command_id,
                operator_id=operator_id,
                operator_role=operator_role,
                authorization_scope=authorization_scope,
                approved_by=approved_by,
                approval_required=approval_required,
                reason=reason,
                payload=payload or {},
            )
        )

    @staticmethod
    def result_dto(result: RuntimeCommandResult) -> RuntimeCommandResultDTO:
        """Map runtime command results to application DTOs."""
        return RuntimeCommandResultDTO(
            command_id=result.command_id,
            idempotency_key=result.idempotency_key,
            status=result.result_status.value,
            evidence=result.evidence,
            failure_reason=result.failure_reason,
            reason_code=result.reason_code,
        )

    def _next_command_id(self, command_type: RuntimeCommandType) -> str:
        self._command_sequence += 1
        return f"{command_type.value}-{self._command_sequence}"


__all__ = ["OperationsCommandRouter"]
