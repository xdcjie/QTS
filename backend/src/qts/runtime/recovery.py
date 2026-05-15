"""Runtime recovery state coordination."""

from __future__ import annotations

from typing import Any, cast

from qts.runtime.state import RuntimeSessionState


class RuntimeRecoveryCoordinator:
    """Own recovery transitions while RuntimeSession remains the public facade."""

    def __init__(self, session: Any) -> None:
        self._session = session

    def recover(self) -> RuntimeSessionState:
        """Recover a degraded session."""
        session = self._session
        state = cast(RuntimeSessionState, session._machine.apply("recover"))
        session._write_event("runtime.state_transition", {"state": state.value})
        return state


__all__ = ["RuntimeRecoveryCoordinator"]
