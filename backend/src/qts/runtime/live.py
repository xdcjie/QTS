"""Paper/live runtime lifecycle and startup safety orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.data.interfaces import StreamingFeedAdapter
from qts.execution.broker import BrokerAdapter, BrokerExecutionReport, BrokerOrderRequest
from qts.runtime.config import LiveRuntimeConfig
from qts.runtime.mode import AccountEnvironment, RuntimeMode
from qts.runtime.permissions import LiveOrderPermission
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.state import RuntimeSessionState, RuntimeStateMachine

LiveRuntimeState = RuntimeSessionState
LiveRuntimeStateMachine = RuntimeStateMachine
LivePermissionMode = LiveOrderPermission


class BrokerRuntimeStartupDecisionStatus(StrEnum):
    """Explicit startup decision for paper/live capable runtimes."""

    ALLOW_OBSERVATION = "allow_observation"
    ALLOW_PAPER = "allow_paper"
    ALLOW_LIVE = "allow_live"
    BLOCK = "block"


@dataclass(frozen=True, slots=True)
class BrokerRuntimeStartupCheck:
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
class BrokerRuntimeStartupChecklist:
    """Structured startup checklist evidence for paper/live modes."""

    checks: tuple[BrokerRuntimeStartupCheck, ...]

    @classmethod
    def from_config(cls, config: LiveRuntimeConfig) -> BrokerRuntimeStartupChecklist:
        """Build structured startup evidence without changing startup state."""

        checks: list[BrokerRuntimeStartupCheck] = []
        mode = RuntimeMode.from_value(config.mode)
        account_environment = AccountEnvironment.from_value(config.account_environment, mode=mode)
        for check_name, configured, evidence, remediation in (
            (
                "broker_configured",
                config.broker_configured,
                f"broker_configured={config.broker_configured}",
                "configure broker connection",
            ),
            (
                "account_configured",
                config.account_configured,
                f"account_configured={config.account_configured}",
                "configure account mapping",
            ),
            (
                "account_mode_check",
                config.account_configured,
                (
                    f"account_environment={account_environment.value};"
                    f"broker_account_kind={config.broker_account_kind};"
                    f"broker_account_code={config.broker_account_code}"
                ),
                "configure account environment and broker account kind for the runtime mode",
            ),
            (
                "port_check",
                mode
                not in {
                    RuntimeMode.LIVE,
                    RuntimeMode.PAPER_BROKER,
                }
                or config.broker_port is not None,
                (
                    f"broker_port={config.broker_port}"
                    if mode in {RuntimeMode.LIVE, RuntimeMode.PAPER_BROKER}
                    else "broker_port=not_required"
                ),
                "configure the broker port for the runtime mode",
            ),
            (
                "api_read_only_check",
                mode is not RuntimeMode.LIVE or not config.api_read_only,
                f"api_read_only={config.api_read_only}",
                "disable broker API read-only mode before enabling live orders",
            ),
            (
                "broker_time_check",
                config.broker_time_synced,
                f"broker_time_synced={config.broker_time_synced}",
                "synchronize broker/runtime clocks before startup",
            ),
            (
                "risk_config_check",
                config.risk_configured,
                f"risk_configured={config.risk_configured}",
                "configure risk limits",
            ),
            (
                "calendar_configured",
                config.calendar_configured,
                f"calendar_configured={config.calendar_configured}",
                "configure trading calendar",
            ),
            (
                "kill_switch_check",
                config.kill_switch_configured,
                f"kill_switch_configured={config.kill_switch_configured}",
                "configure kill switch",
            ),
        ):
            checks.append(
                BrokerRuntimeStartupCheck(
                    check_name=check_name,
                    status="PASS" if configured else "FAIL",
                    severity="INFO" if configured else "BLOCKER",
                    evidence=evidence,
                    remediation="none" if configured else remediation,
                )
            )
        for check_name, passed, evidence, remediation in (
            (
                "market_data_permission_check",
                config.market_data_permission_live,
                f"market_data_permission_live={config.market_data_permission_live}",
                "obtain live market-data permission or switch to observation-only",
            ),
            (
                "open_order_reconciliation_check",
                bool(config.open_order_reconciliation_passed),
                f"open_order_reconciliation_passed={config.open_order_reconciliation_passed}",
                "run open-order reconciliation and resolve drift",
            ),
            (
                "position_reconciliation_check",
                bool(config.position_reconciliation_passed),
                f"position_reconciliation_passed={config.position_reconciliation_passed}",
                "run position reconciliation and resolve drift",
            ),
            (
                "cash_reconciliation_check",
                bool(config.cash_reconciliation_passed),
                f"cash_reconciliation_passed={config.cash_reconciliation_passed}",
                "run cash reconciliation and resolve drift",
            ),
            (
                "event_sink_check",
                config.event_sink_writable,
                f"event_sink_writable={config.event_sink_writable}",
                "configure a writable runtime event sink",
            ),
            (
                "snapshot_store_check",
                config.snapshot_store_configured,
                f"snapshot_store_configured={config.snapshot_store_configured}",
                "configure a runtime snapshot store",
            ),
            (
                "operator_signoff_check",
                mode is not RuntimeMode.LIVE or bool(config.operator_signoff_id),
                (
                    f"operator_signoff_id={config.operator_signoff_id}"
                    if mode is RuntimeMode.LIVE
                    else "operator_signoff_id=not_required"
                ),
                "record operator signoff before enabling live orders",
            ),
        ):
            checks.append(
                BrokerRuntimeStartupCheck(
                    check_name=check_name,
                    status="PASS" if passed else "FAIL",
                    severity="INFO" if passed else "BLOCKER",
                    evidence=evidence,
                    remediation="none" if passed else remediation,
                )
            )
        return cls(checks=tuple(checks))

    @property
    def passed(self) -> bool:
        """Return whether all blocking checks passed."""

        return all(check.status != "FAIL" for check in self.checks)

    def by_name(self, check_name: str) -> BrokerRuntimeStartupCheck:
        """Return one checklist item by name."""

        for check in self.checks:
            if check.check_name == check_name:
                return check
        raise KeyError(check_name)

    @property
    def checklist_hash(self) -> str:
        """Return a stable hash of startup checklist evidence."""

        return stable_json_hash(self.to_payload(include_hash=False))

    def to_payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        """Serialize checklist evidence for manifests and startup artifacts."""

        payload: dict[str, Any] = {
            "passed": self.passed,
            "checks": [
                {
                    "check_name": check.check_name,
                    "status": check.status,
                    "severity": check.severity,
                    "evidence": check.evidence,
                    "remediation": check.remediation,
                }
                for check in self.checks
            ],
        }
        if include_hash:
            payload["checklist_hash"] = self.checklist_hash
        return payload


@dataclass(frozen=True, slots=True)
class BrokerRuntimeStartupDecision:
    """Result of startup guard validation."""

    status: BrokerRuntimeStartupDecisionStatus
    mode: RuntimeMode
    order_permission: LiveOrderPermission
    real_order_submission_enabled: bool
    checklist: BrokerRuntimeStartupChecklist


def validate_live_startup(config: LiveRuntimeConfig) -> BrokerRuntimeStartupDecision:
    """Fail closed unless all live safety prerequisites are explicit."""

    checklist = BrokerRuntimeStartupChecklist.from_config(config)
    missing = [
        f"{check.check_name} ({check.evidence})"
        for check in checklist.checks
        if check.status == "FAIL"
    ]
    if missing:
        raise ValueError("live startup missing required config: " + ", ".join(missing))
    mode = RuntimeMode.from_value(config.mode)
    status = _startup_decision_status(mode)
    return BrokerRuntimeStartupDecision(
        status=status,
        mode=mode,
        order_permission=_order_permission_for_status(status),
        real_order_submission_enabled=(
            _order_permission_for_status(status).allows_live_orders
            and config.allow_live_orders
            and not config.observation_only
        ),
        checklist=checklist,
    )


def _startup_decision_status(mode: RuntimeMode) -> BrokerRuntimeStartupDecisionStatus:
    if mode is RuntimeMode.LIVE:
        return BrokerRuntimeStartupDecisionStatus.ALLOW_LIVE
    if mode in {RuntimeMode.PAPER_BROKER, RuntimeMode.PAPER_SIMULATED}:
        return BrokerRuntimeStartupDecisionStatus.ALLOW_PAPER
    if mode in {RuntimeMode.OBSERVATION, RuntimeMode.LIVE_OBSERVATION}:
        return BrokerRuntimeStartupDecisionStatus.ALLOW_OBSERVATION
    return BrokerRuntimeStartupDecisionStatus.BLOCK


def _order_permission_for_status(
    status: BrokerRuntimeStartupDecisionStatus,
) -> LiveOrderPermission:
    if status is BrokerRuntimeStartupDecisionStatus.ALLOW_LIVE:
        return LiveOrderPermission.LIVE_ORDERS_ALLOWED
    if status is BrokerRuntimeStartupDecisionStatus.ALLOW_PAPER:
        return LiveOrderPermission.PAPER_ORDERS_ALLOWED
    return LiveOrderPermission.OBSERVATION_ONLY


LiveStartupDecisionStatus = BrokerRuntimeStartupDecisionStatus
LiveStartupCheck = BrokerRuntimeStartupCheck
LiveStartupChecklist = BrokerRuntimeStartupChecklist
LiveStartupDecision = BrokerRuntimeStartupDecision


@dataclass(frozen=True, slots=True)
class RuntimeOrderResult:
    """Result of live runtime order submission."""

    request: BrokerOrderRequest
    accepted: bool
    report: BrokerExecutionReport | None = None
    reason_code: str | None = None


class LiveRuntime:
    """Runtime facade over broker and market-data boundary adapters."""

    def __init__(self, *, broker: BrokerAdapter, feed: StreamingFeedAdapter) -> None:
        self._broker = broker
        self._feed = feed
        self._machine = LiveRuntimeStateMachine()

    @property
    def state(self) -> LiveRuntimeState:
        """Perform state."""
        return self._machine.state

    @property
    def feed(self) -> StreamingFeedAdapter:
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
    "BrokerRuntimeStartupCheck",
    "BrokerRuntimeStartupChecklist",
    "BrokerRuntimeStartupDecision",
    "BrokerRuntimeStartupDecisionStatus",
    "LivePermissionMode",
    "LiveStartupCheck",
    "LiveStartupChecklist",
    "LiveStartupDecisionStatus",
    "LiveRuntime",
    "LiveRuntimeState",
    "LiveRuntimeStateMachine",
    "LiveStartupDecision",
    "RuntimeOrderResult",
    "validate_live_startup",
]
