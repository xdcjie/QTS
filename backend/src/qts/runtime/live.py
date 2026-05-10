"""Live runtime lifecycle and fake-adapter orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from qts.data.live_feed import LiveFeedAdapter
from qts.execution.broker import BrokerAdapter, BrokerExecutionReport, BrokerOrderRequest


class LiveRuntimeState(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    DEGRADED = "degraded"


_TRANSITIONS: dict[LiveRuntimeState, dict[str, LiveRuntimeState]] = {
    LiveRuntimeState.STOPPED: {"start": LiveRuntimeState.STARTING},
    LiveRuntimeState.STARTING: {
        "started": LiveRuntimeState.RUNNING,
        "stop": LiveRuntimeState.STOPPED,
    },
    LiveRuntimeState.RUNNING: {
        "pause": LiveRuntimeState.PAUSED,
        "degrade": LiveRuntimeState.DEGRADED,
        "stop": LiveRuntimeState.STOPPED,
    },
    LiveRuntimeState.PAUSED: {
        "resume": LiveRuntimeState.RUNNING,
        "degrade": LiveRuntimeState.DEGRADED,
        "stop": LiveRuntimeState.STOPPED,
    },
    LiveRuntimeState.DEGRADED: {
        "recover": LiveRuntimeState.RUNNING,
        "pause": LiveRuntimeState.PAUSED,
        "stop": LiveRuntimeState.STOPPED,
    },
}


@dataclass(slots=True)
class LiveRuntimeStateMachine:
    state: LiveRuntimeState = LiveRuntimeState.STOPPED

    def apply(self, command: str) -> LiveRuntimeState:
        next_state = _TRANSITIONS.get(self.state, {}).get(command)
        if next_state is None:
            raise ValueError(f"invalid live runtime transition: {self.state} -> {command}")
        self.state = next_state
        return self.state


@dataclass(frozen=True, slots=True)
class RuntimeOrderResult:
    request: BrokerOrderRequest
    accepted: bool
    report: BrokerExecutionReport | None = None
    reason_code: str | None = None


class LiveRuntime:
    """Small live-beta runtime wrapper over fake or real boundary adapters."""

    def __init__(self, *, broker: BrokerAdapter, feed: LiveFeedAdapter) -> None:
        self._broker = broker
        self._feed = feed
        self._machine = LiveRuntimeStateMachine()

    @property
    def state(self) -> LiveRuntimeState:
        return self._machine.state

    @property
    def feed(self) -> LiveFeedAdapter:
        return self._feed

    def start(self) -> LiveRuntimeState:
        self._machine.apply("start")
        return self._machine.apply("started")

    def stop(self) -> LiveRuntimeState:
        return self._machine.apply("stop")

    def pause(self) -> LiveRuntimeState:
        return self._machine.apply("pause")

    def resume(self) -> LiveRuntimeState:
        return self._machine.apply("resume")

    def degrade(self) -> LiveRuntimeState:
        return self._machine.apply("degrade")

    def recover(self) -> LiveRuntimeState:
        return self._machine.apply("recover")

    def submit_order(self, request: BrokerOrderRequest) -> RuntimeOrderResult:
        if self.state is LiveRuntimeState.PAUSED:
            return RuntimeOrderResult(request=request, accepted=False, reason_code="RUNTIME_PAUSED")
        if self.state is not LiveRuntimeState.RUNNING:
            return RuntimeOrderResult(
                request=request, accepted=False, reason_code="RUNTIME_NOT_RUNNING"
            )
        return RuntimeOrderResult(
            request=request, accepted=True, report=self._broker.submit_order(request)
        )


__all__ = ["LiveRuntime", "LiveRuntimeState", "LiveRuntimeStateMachine", "RuntimeOrderResult"]
