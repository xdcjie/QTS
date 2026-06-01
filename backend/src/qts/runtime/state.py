"""Mode-neutral runtime session lifecycle state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuntimeSessionState(StrEnum):
    """Runtime session lifecycle states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    OBSERVATION = "observation"
    DEGRADED = "degraded"


_TRANSITIONS: dict[RuntimeSessionState, dict[str, RuntimeSessionState]] = {
    RuntimeSessionState.STOPPED: {"start": RuntimeSessionState.STARTING},
    RuntimeSessionState.STARTING: {
        "started": RuntimeSessionState.RUNNING,
        "stop": RuntimeSessionState.STOPPED,
    },
    RuntimeSessionState.RUNNING: {
        "pause": RuntimeSessionState.PAUSED,
        "enter_observation": RuntimeSessionState.OBSERVATION,
        "degrade": RuntimeSessionState.DEGRADED,
        "stop": RuntimeSessionState.STOPPED,
    },
    RuntimeSessionState.PAUSED: {
        "resume": RuntimeSessionState.RUNNING,
        "enter_observation": RuntimeSessionState.OBSERVATION,
        "degrade": RuntimeSessionState.DEGRADED,
        "stop": RuntimeSessionState.STOPPED,
    },
    RuntimeSessionState.OBSERVATION: {
        "exit_observation": RuntimeSessionState.RUNNING,
        "degrade": RuntimeSessionState.DEGRADED,
        "stop": RuntimeSessionState.STOPPED,
    },
    RuntimeSessionState.DEGRADED: {
        "recover": RuntimeSessionState.RUNNING,
        "pause": RuntimeSessionState.PAUSED,
        "enter_observation": RuntimeSessionState.OBSERVATION,
        "stop": RuntimeSessionState.STOPPED,
    },
}


@dataclass(slots=True)
class RuntimeStateMachine:
    """Mutable runtime session state machine."""

    state: RuntimeSessionState = RuntimeSessionState.STOPPED

    def apply(self, command: str) -> RuntimeSessionState:
        """Apply one lifecycle command and return the new state."""
        next_state = _TRANSITIONS.get(self.state, {}).get(command)
        if next_state is None:
            raise ValueError(f"invalid runtime transition: {self.state} -> {command}")
        self.state = next_state
        return self.state


__all__ = [
    "RuntimeSessionState",
    "RuntimeStateMachine",
]
