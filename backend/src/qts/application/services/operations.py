"""Operational application service."""

from __future__ import annotations

from qts.application.dto import KillSwitchCommandDTO, KillSwitchStateDTO, RuntimeStateDTO
from qts.risk.kill_switch import KillSwitchRegistry, KillSwitchScope, KillSwitchScopeType


class OperationsService:
    """Owns operational state without leaking runtime internals into API routes."""

    def __init__(self, *, kill_switches: KillSwitchRegistry | None = None) -> None:
        """Perform __init__."""
        self._runtime_state = "running"
        self._kill_switches = kill_switches or KillSwitchRegistry()

    def pause_runtime(self) -> RuntimeStateDTO:
        """Perform pause_runtime."""
        self._runtime_state = "paused"
        return RuntimeStateDTO(state=self._runtime_state)

    def resume_runtime(self) -> RuntimeStateDTO:
        """Perform resume_runtime."""
        self._runtime_state = "running"
        return RuntimeStateDTO(state=self._runtime_state)

    def activate_kill_switch(self, command: KillSwitchCommandDTO) -> KillSwitchStateDTO:
        """Perform activate_kill_switch."""
        scope = self._scope_from_command(command)
        state = self._kill_switches.activate(scope, reason=command.reason)
        return KillSwitchStateDTO(
            scope=state.scope.scope_type.value,
            scope_id=state.scope.scope_id,
            active=state.active,
            reason=state.reason,
        )

    @staticmethod
    def _scope_from_command(command: KillSwitchCommandDTO) -> KillSwitchScope:
        """Perform _scope_from_command."""
        scope_type = KillSwitchScopeType(command.scope)
        if scope_type is KillSwitchScopeType.GLOBAL:
            return KillSwitchScope.global_scope()
        return KillSwitchScope(scope_type, command.scope_id)


__all__ = ["OperationsService"]
