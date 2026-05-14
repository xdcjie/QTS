"""Live runtime lifecycle and fake-adapter orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from qts.data.live_feed import LiveFeedAdapter
from qts.execution.broker import BrokerAdapter, BrokerExecutionReport, BrokerOrderRequest
from qts.runtime.config import LiveRuntimeConfig
from qts.runtime.mode import RuntimeMode
from qts.runtime.sinks.base import RuntimeEvent


class LiveRuntimeState(StrEnum):
    """Live runtime lifecycle states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    DEGRADED = "degraded"


class LivePermissionMode(StrEnum):
    """Runtime mode with explicit live-trading permissions."""

    PAPER = "paper"
    OBSERVATION = "observation"
    LIVE = "live"


LiveMode = LivePermissionMode


@dataclass(frozen=True, slots=True)
class LiveStartupCheck:
    """One structured live startup checklist item."""

    check_name: str
    status: str
    severity: str
    evidence: str
    remediation: str

    def __post_init__(self) -> None:
        if not self.check_name.strip():
            raise ValueError("check_name must not be empty")
        if self.status not in {"PASS", "WARN", "FAIL"}:
            raise ValueError("status must be PASS, WARN, or FAIL")
        if self.severity not in {"INFO", "WARN", "BLOCKER"}:
            raise ValueError("severity must be INFO, WARN, or BLOCKER")
        if not self.evidence.strip():
            raise ValueError("evidence must not be empty")
        if not self.remediation.strip():
            raise ValueError("remediation must not be empty")


@dataclass(frozen=True, slots=True)
class LiveStartupChecklist:
    """Structured startup checklist evidence for paper/live modes."""

    checks: tuple[LiveStartupCheck, ...]

    @classmethod
    def from_config(cls, config: LiveRuntimeConfig) -> LiveStartupChecklist:
        """Build structured startup evidence without changing startup state."""

        checks: list[LiveStartupCheck] = []
        for field_name, configured, remediation in (
            ("broker_configured", config.broker_configured, "configure broker connection"),
            ("account_configured", config.account_configured, "configure account mapping"),
            ("risk_configured", config.risk_configured, "configure risk limits"),
            ("calendar_configured", config.calendar_configured, "configure trading calendar"),
            ("kill_switch_configured", config.kill_switch_configured, "configure kill switch"),
        ):
            checks.append(
                LiveStartupCheck(
                    check_name=field_name,
                    status="PASS" if configured else "FAIL",
                    severity="INFO" if configured else "BLOCKER",
                    evidence=f"{field_name}={configured}",
                    remediation="none" if configured else remediation,
                )
            )
        return cls(checks=tuple(checks))

    @property
    def passed(self) -> bool:
        """Return whether all blocking checks passed."""

        return all(check.status != "FAIL" for check in self.checks)

    def by_name(self, check_name: str) -> LiveStartupCheck:
        """Return one checklist item by name."""

        for check in self.checks:
            if check.check_name == check_name:
                return check
        raise KeyError(check_name)


@dataclass(frozen=True, slots=True)
class LiveStartupDecision:
    """Result of startup guard validation."""

    mode: RuntimeMode
    real_order_submission_enabled: bool


def validate_live_startup(config: LiveRuntimeConfig) -> LiveStartupDecision:
    """Fail closed unless all live safety prerequisites are explicit."""

    checklist = LiveStartupChecklist.from_config(config)
    missing = [check.check_name for check in checklist.checks if check.status == "FAIL"]
    if missing:
        raise ValueError("live startup missing required config: " + ", ".join(missing))
    mode = RuntimeMode.from_value(config.mode)
    return LiveStartupDecision(
        mode=mode,
        real_order_submission_enabled=(
            mode is RuntimeMode.LIVE and config.allow_live_orders and not config.observation_only
        ),
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
    """Mutable live runtime state machine."""

    state: LiveRuntimeState = LiveRuntimeState.STOPPED

    def apply(self, command: str) -> LiveRuntimeState:
        """Perform apply."""
        next_state = _TRANSITIONS.get(self.state, {}).get(command)
        if next_state is None:
            raise ValueError(f"invalid live runtime transition: {self.state} -> {command}")
        self.state = next_state
        return self.state


@dataclass(frozen=True, slots=True)
class RuntimeOrderResult:
    """Result of live runtime order submission."""

    request: BrokerOrderRequest
    accepted: bool
    report: BrokerExecutionReport | None = None
    reason_code: str | None = None


class LiveRuntime:
    """Runtime facade over broker and market-data boundary adapters."""

    def __init__(self, *, broker: BrokerAdapter, feed: LiveFeedAdapter) -> None:
        self._broker = broker
        self._feed = feed
        self._machine = LiveRuntimeStateMachine()

    @property
    def state(self) -> LiveRuntimeState:
        """Perform state."""
        return self._machine.state

    @property
    def feed(self) -> LiveFeedAdapter:
        """Perform feed."""
        return self._feed

    def start(self) -> LiveRuntimeState:
        """Perform start."""
        self._machine.apply("start")
        return self._machine.apply("started")

    def stop(self) -> LiveRuntimeState:
        """Perform stop."""
        return self._machine.apply("stop")

    def pause(self) -> LiveRuntimeState:
        """Perform pause."""
        return self._machine.apply("pause")

    def resume(self) -> LiveRuntimeState:
        """Perform resume."""
        return self._machine.apply("resume")

    def degrade(self) -> LiveRuntimeState:
        """Perform degrade."""
        return self._machine.apply("degrade")

    def recover(self) -> LiveRuntimeState:
        """Perform recover."""
        return self._machine.apply("recover")

    def apply_runtime_event(self, event: RuntimeEvent) -> LiveRuntimeState:
        """Apply runtime control events such as market-data degradation."""

        if event.kind == "runtime.degraded":
            if self.state is LiveRuntimeState.DEGRADED:
                return self.state
            return self.degrade()
        return self.state

    def submit_order(self, request: BrokerOrderRequest) -> RuntimeOrderResult:
        """Perform submit_order."""
        if self.state is LiveRuntimeState.PAUSED:
            return RuntimeOrderResult(request=request, accepted=False, reason_code="RUNTIME_PAUSED")
        if self.state is LiveRuntimeState.DEGRADED:
            return RuntimeOrderResult(
                request=request, accepted=False, reason_code="RUNTIME_DEGRADED"
            )
        if self.state is not LiveRuntimeState.RUNNING:
            return RuntimeOrderResult(
                request=request, accepted=False, reason_code="RUNTIME_NOT_RUNNING"
            )
        return RuntimeOrderResult(
            request=request, accepted=True, report=self._broker.submit_order(request)
        )


__all__ = [
    "LivePermissionMode",
    "LiveStartupCheck",
    "LiveStartupChecklist",
    "LiveMode",
    "LiveRuntime",
    "LiveRuntimeState",
    "LiveRuntimeStateMachine",
    "LiveStartupDecision",
    "RuntimeOrderResult",
    "validate_live_startup",
]
