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


class LiveMode(StrEnum):
    """Runtime mode with explicit live-trading permissions."""

    PAPER = "paper"
    OBSERVATION = "observation"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class LiveStartupConfig:
    """Startup guard inputs for live-capable runtime."""

    mode: LiveMode
    broker_configured: bool
    account_configured: bool
    risk_configured: bool
    calendar_configured: bool
    kill_switch_configured: bool


@dataclass(frozen=True, slots=True)
class LiveStartupDecision:
    """Result of startup guard validation."""

    mode: LiveMode
    real_order_submission_enabled: bool


def validate_live_startup(config: LiveStartupConfig) -> LiveStartupDecision:
    """Fail closed unless all live safety prerequisites are explicit."""

    missing = [
        field_name
        for field_name, configured in (
            ("broker_configured", config.broker_configured),
            ("account_configured", config.account_configured),
            ("risk_configured", config.risk_configured),
            ("calendar_configured", config.calendar_configured),
            ("kill_switch_configured", config.kill_switch_configured),
        )
        if not configured
    ]
    if missing:
        raise ValueError("live startup missing required config: " + ", ".join(missing))
    return LiveStartupDecision(
        mode=config.mode,
        real_order_submission_enabled=config.mode is LiveMode.LIVE,
    )


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


__all__ = [
    "LiveMode",
    "LiveRuntime",
    "LiveRuntimeState",
    "LiveRuntimeStateMachine",
    "LiveStartupConfig",
    "LiveStartupDecision",
    "RuntimeOrderResult",
    "validate_live_startup",
]
