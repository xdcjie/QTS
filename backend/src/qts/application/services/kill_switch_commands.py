"""Kill-switch application command owner."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from qts.risk.kill_switch import KillSwitchRegistry, KillSwitchScope, KillSwitchScopeType
from qts.runtime.commands import (
    RuntimeCommand,
    RuntimeCommandResult,
    RuntimeCommandResultStatus,
    RuntimeCommandType,
)


class KillSwitchCommandService:
    """Owns kill-switch command state, scope parsing, and evidence."""

    def __init__(self, *, kill_switches: KillSwitchRegistry | None = None) -> None:
        self._kill_switches = kill_switches or KillSwitchRegistry()
        self._state: dict[str, object] = {
            "scope": "global",
            "scope_id": None,
            "active": False,
            "reason": "",
        }

    @property
    def state(self) -> dict[str, object]:
        """Return the current kill-switch state evidence."""
        return dict(self._state)

    def handle(
        self,
        command: RuntimeCommand,
        *,
        accepted_at: datetime,
    ) -> RuntimeCommandResult | None:
        """Apply a kill-switch command or return None for commands owned elsewhere."""
        if command.command_type not in {
            RuntimeCommandType.ACTIVATE_KILL_SWITCH,
            RuntimeCommandType.DEACTIVATE_KILL_SWITCH,
        }:
            return None
        try:
            scope = self._scope_from_payload(command.payload)
            reason = self._require_payload_text(command.payload, "reason")
        except ValueError as exc:
            return self._rejected_result(command, accepted_at=accepted_at, reason=str(exc))

        if command.command_type is RuntimeCommandType.ACTIVATE_KILL_SWITCH:
            state = self._kill_switches.activate(scope, reason=reason)
        else:
            state = self._kill_switches.deactivate(scope, reason=reason)
        self._state = {
            "scope": state.scope.scope_type.value,
            "scope_id": state.scope.scope_id,
            "active": state.active,
            "reason": state.reason,
        }
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            completed_at=accepted_at,
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence=self._command_evidence(command, self._state),
        )

    @staticmethod
    def _scope_from_payload(payload: Mapping[str, object]) -> KillSwitchScope:
        scope = KillSwitchCommandService._require_payload_text(payload, "scope")
        scope_type = KillSwitchScopeType(scope)
        if scope_type is KillSwitchScopeType.GLOBAL:
            return KillSwitchScope.global_scope()
        scope_id = KillSwitchCommandService._require_payload_text(payload, "scope_id")
        return KillSwitchScope(scope_type, scope_id)

    @staticmethod
    def _require_payload_text(payload: Mapping[str, object], name: str) -> str:
        value = payload.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")
        return value.strip()

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
        reason: str,
    ) -> RuntimeCommandResult:
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=accepted_at,
            result_status=RuntimeCommandResultStatus.REJECTED,
            failure_reason=reason,
        )


__all__ = ["KillSwitchCommandService"]
