"""Operational application service."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from qts.application.dto import (
    KillSwitchCommandDTO,
    KillSwitchStateDTO,
    OperatorDashboardStatusDTO,
    OperatorStatusFieldDTO,
    RuntimeCommandResultDTO,
    RuntimeStateDTO,
)
from qts.risk.kill_switch import KillSwitchRegistry, KillSwitchScope, KillSwitchScopeType
from qts.runtime.commands import (
    RuntimeCommand,
    RuntimeCommandBus,
    RuntimeCommandResult,
    RuntimeCommandResultStatus,
    RuntimeCommandType,
)


class OperationsService:
    """Owns operational state without leaking runtime internals into API routes."""

    def __init__(
        self,
        *,
        kill_switches: KillSwitchRegistry | None = None,
        operator_status: OperatorDashboardStatusDTO | None = None,
    ) -> None:
        """Create operational command state and idempotent command routing."""
        self._runtime_state = "running"
        self._runtime_mode = "paper"
        self._kill_switches = kill_switches or KillSwitchRegistry()
        self._kill_switch_state = {
            "scope": "global",
            "scope_id": None,
            "active": False,
            "reason": "",
        }
        self._operator_status = operator_status
        self._command_sequence = 0
        self._command_bus = RuntimeCommandBus(handler=self._handle_runtime_command)

    def start_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Start runtime processing through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.START,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def stop_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Stop runtime processing through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.STOP,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def pause_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Pause runtime processing through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.PAUSE,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def resume_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Resume runtime processing through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.RESUME,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def enter_observation(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Enter observation mode through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.ENTER_OBSERVATION,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def exit_observation(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Exit observation mode through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.EXIT_OBSERVATION,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def activate_kill_switch(
        self,
        command: KillSwitchCommandDTO,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> KillSwitchStateDTO:
        """Activate a kill switch through the command bus."""
        result = self._submit_runtime_command(
            RuntimeCommandType.ACTIVATE_KILL_SWITCH,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
            reason=command.reason,
            payload={
                "scope": command.scope,
                "scope_id": command.scope_id,
                "reason": command.reason,
            },
        )
        return self._kill_switch_state_from_result(result)

    def deactivate_kill_switch(
        self,
        command: KillSwitchCommandDTO,
        *,
        operator_id: str = "system",
        operator_role: str = "operator",
        authorization_scope: str = "runtime:operator",
        idempotency_key: str | None = None,
    ) -> KillSwitchStateDTO:
        """Deactivate a kill switch through the command bus."""
        result = self._submit_deactivate_kill_switch_command(
            command,
            operator_id=operator_id,
            operator_role=operator_role,
            authorization_scope=authorization_scope,
            idempotency_key=idempotency_key,
        )
        return self._kill_switch_state_from_result(result)

    def deactivate_kill_switch_result(
        self,
        command: KillSwitchCommandDTO,
        *,
        operator_id: str = "system",
        operator_role: str = "operator",
        authorization_scope: str = "runtime:operator",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Deactivate a kill switch and return the auditable command result."""
        result = self._submit_deactivate_kill_switch_command(
            command,
            operator_id=operator_id,
            operator_role=operator_role,
            authorization_scope=authorization_scope,
            idempotency_key=idempotency_key,
        )
        return self._command_result_dto(result)

    def _submit_deactivate_kill_switch_command(
        self,
        command: KillSwitchCommandDTO,
        *,
        operator_id: str,
        operator_role: str,
        authorization_scope: str,
        idempotency_key: str | None,
    ) -> RuntimeCommandResult:
        return self._submit_runtime_command(
            RuntimeCommandType.DEACTIVATE_KILL_SWITCH,
            operator_id=operator_id,
            operator_role=operator_role,
            authorization_scope=authorization_scope,
            idempotency_key=idempotency_key,
            reason=command.reason,
            payload={
                "scope": command.scope,
                "scope_id": command.scope_id,
                "reason": command.reason,
            },
        )

    def reconcile_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Request a runtime reconciliation through the command bus."""
        result = self._submit_runtime_command(
            RuntimeCommandType.RECONCILE,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )
        return self._command_result_dto(result)

    def snapshot_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Request a runtime snapshot through the command bus."""
        result = self._submit_runtime_command(
            RuntimeCommandType.SNAPSHOT,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )
        return self._command_result_dto(result)

    def operator_status(self) -> OperatorDashboardStatusDTO:
        """Return the application-owned operator dashboard state."""
        if self._operator_status is not None:
            return self._operator_status
        observed_at = datetime.now(UTC)
        return OperatorDashboardStatusDTO(
            runtime_state=OperatorStatusFieldDTO(
                value=self._runtime_state,
                timestamp=observed_at,
            ),
            runtime_mode=OperatorStatusFieldDTO(value=self._runtime_mode, timestamp=observed_at),
            order_permission_state=OperatorStatusFieldDTO(value="enabled", timestamp=observed_at),
            broker_connection_state=OperatorStatusFieldDTO(
                value="disconnected",
                timestamp=observed_at,
            ),
            market_data_permission_state=OperatorStatusFieldDTO(
                value="enabled",
                timestamp=observed_at,
            ),
            stale_subscriptions=OperatorStatusFieldDTO(value=(), timestamp=observed_at),
            open_orders=OperatorStatusFieldDTO(value=(), timestamp=observed_at),
            positions=OperatorStatusFieldDTO(value=(), timestamp=observed_at),
            cash_snapshot=OperatorStatusFieldDTO(value=(), timestamp=observed_at),
            kill_switch_state=OperatorStatusFieldDTO(
                value=self._kill_switch_state,
                timestamp=observed_at,
            ),
            last_reconciliation_result=OperatorStatusFieldDTO(
                value={"status": "not_requested", "drift_count": 0},
                timestamp=observed_at,
            ),
            unresolved_broker_callbacks=OperatorStatusFieldDTO(value=(), timestamp=observed_at),
            event_sink=OperatorStatusFieldDTO(
                value={"path": None, "hash": None, "row_count": 0},
                timestamp=observed_at,
            ),
            latest_manifest=OperatorStatusFieldDTO(
                value={"path": None, "hash": None},
                timestamp=observed_at,
            ),
        )

    def _submit_runtime_state_command(
        self,
        command_type: RuntimeCommandType,
        *,
        operator_id: str,
        idempotency_key: str | None,
    ) -> RuntimeStateDTO:
        result = self._submit_runtime_command(
            command_type,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )
        state = result.evidence.get("state")
        if not isinstance(state, str):
            raise RuntimeError("runtime command result did not include state evidence")
        return RuntimeStateDTO(state=state)

    def _submit_runtime_command(
        self,
        command_type: RuntimeCommandType,
        *,
        operator_id: str,
        operator_role: str = "operator",
        authorization_scope: str = "runtime:operator",
        approved_by: str | None = None,
        approval_required: bool = False,
        idempotency_key: str | None,
        reason: str | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> RuntimeCommandResult:
        command_id = self._next_command_id(command_type)
        return self._command_bus.submit(
            RuntimeCommand(
                command_id=command_id,
                command_type=command_type,
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

    def _handle_runtime_command(self, command: RuntimeCommand) -> RuntimeCommandResult:
        accepted_at = datetime.now(UTC)
        evidence: dict[str, object]
        if command.command_type is RuntimeCommandType.START:
            self._runtime_state = "running"
            evidence = self._command_evidence(command, {"state": self._runtime_state})
        elif command.command_type is RuntimeCommandType.STOP:
            self._runtime_state = "stopped"
            evidence = self._command_evidence(command, {"state": self._runtime_state})
        elif command.command_type is RuntimeCommandType.PAUSE:
            self._runtime_state = "paused"
            evidence = self._command_evidence(command, {"state": self._runtime_state})
        elif command.command_type is RuntimeCommandType.RESUME:
            self._runtime_state = "running"
            evidence = self._command_evidence(command, {"state": self._runtime_state})
        elif command.command_type is RuntimeCommandType.ENTER_OBSERVATION:
            self._runtime_state = "observation"
            evidence = self._command_evidence(command, {"state": self._runtime_state})
        elif command.command_type is RuntimeCommandType.EXIT_OBSERVATION:
            self._runtime_state = "running"
            evidence = self._command_evidence(command, {"state": self._runtime_state})
        elif command.command_type is RuntimeCommandType.ACTIVATE_KILL_SWITCH:
            try:
                scope = self._scope_from_payload(command.payload)
                reason = self._require_payload_text(command.payload, "reason")
            except ValueError as exc:
                return self._rejected_result(
                    command,
                    accepted_at=accepted_at,
                    reason=str(exc),
                )
            state = self._kill_switches.activate(scope, reason=reason)
            self._kill_switch_state = {
                "scope": state.scope.scope_type.value,
                "scope_id": state.scope.scope_id,
                "active": state.active,
                "reason": state.reason,
            }
            evidence = self._command_evidence(
                command,
                {
                    "scope": state.scope.scope_type.value,
                    "scope_id": state.scope.scope_id,
                    "active": state.active,
                    "reason": state.reason,
                },
            )
        elif command.command_type is RuntimeCommandType.DEACTIVATE_KILL_SWITCH:
            try:
                scope = self._scope_from_payload(command.payload)
                reason = self._require_payload_text(command.payload, "reason")
            except ValueError as exc:
                return self._rejected_result(
                    command,
                    accepted_at=accepted_at,
                    reason=str(exc),
                )
            state = self._kill_switches.deactivate(scope, reason=reason)
            self._kill_switch_state = {
                "scope": state.scope.scope_type.value,
                "scope_id": state.scope.scope_id,
                "active": state.active,
                "reason": state.reason,
            }
            evidence = self._command_evidence(
                command,
                {
                    "scope": state.scope.scope_type.value,
                    "scope_id": state.scope.scope_id,
                    "active": state.active,
                    "reason": state.reason,
                },
            )
        elif command.command_type is RuntimeCommandType.RECONCILE:
            evidence = self._command_evidence(
                command,
                {"state": self._runtime_state, "reconciliation": "requested"},
            )
        elif command.command_type is RuntimeCommandType.SNAPSHOT:
            evidence = self._command_evidence(
                command,
                {"state": self._runtime_state, "snapshot": "requested"},
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

    def _next_command_id(self, command_type: RuntimeCommandType) -> str:
        self._command_sequence += 1
        return f"{command_type.value}-{self._command_sequence}"

    @staticmethod
    def _scope_from_payload(payload: Mapping[str, object]) -> KillSwitchScope:
        """Build kill-switch scope from command payload evidence."""
        scope = OperationsService._require_payload_text(payload, "scope")
        scope_type = KillSwitchScopeType(scope)
        if scope_type is KillSwitchScopeType.GLOBAL:
            return KillSwitchScope.global_scope()
        scope_id = OperationsService._require_payload_text(payload, "scope_id")
        return KillSwitchScope(scope_type, scope_id)

    @staticmethod
    def _require_payload_text(payload: Mapping[str, object], name: str) -> str:
        """Read a non-empty text value from command payload."""
        value = payload.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")
        return value.strip()

    @staticmethod
    def _rejected_result(
        command: RuntimeCommand,
        *,
        accepted_at: datetime,
        failure_reason: str | None = None,
        reason: str | None = None,
    ) -> RuntimeCommandResult:
        """Create a rejected command result with required failure evidence."""
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            result_status=RuntimeCommandResultStatus.REJECTED,
            failure_reason=failure_reason or reason,
        )

    @staticmethod
    def _kill_switch_state_from_result(result: RuntimeCommandResult) -> KillSwitchStateDTO:
        """Map command result evidence into the stable kill-switch DTO."""
        scope = result.evidence.get("scope")
        scope_id = result.evidence.get("scope_id")
        active = result.evidence.get("active")
        reason = result.evidence.get("reason")
        if not isinstance(scope, str):
            raise RuntimeError("kill-switch command result did not include scope evidence")
        if scope_id is not None and not isinstance(scope_id, str):
            raise RuntimeError("kill-switch command result included invalid scope_id evidence")
        if not isinstance(active, bool):
            raise RuntimeError("kill-switch command result did not include active evidence")
        if not isinstance(reason, str):
            raise RuntimeError("kill-switch command result did not include reason evidence")
        return KillSwitchStateDTO(scope=scope, scope_id=scope_id, active=active, reason=reason)

    @staticmethod
    def _command_result_dto(result: RuntimeCommandResult) -> RuntimeCommandResultDTO:
        """Map runtime command results to application DTOs."""
        return RuntimeCommandResultDTO(
            command_id=result.command_id,
            idempotency_key=result.idempotency_key,
            status=result.result_status.value,
            evidence=result.evidence,
            failure_reason=result.failure_reason,
            reason_code=result.reason_code,
        )


__all__ = ["OperationsService"]
