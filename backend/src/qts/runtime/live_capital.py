"""Runtime-owned live-capital signoff and enablement decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.runtime.mode import RuntimeMode
from qts.runtime.permissions import OrderSubmissionPermission
from qts.runtime.sinks.base import RuntimeEvent


@dataclass(frozen=True, slots=True)
class OperatorSignoff:
    """Dual-control operator signoff scoped to live-capital exposure."""

    operator_id: str
    reason: str
    risk_approver_id: str
    engineering_approver_id: str
    expires_at: datetime
    strategy_ids: tuple[str, ...]
    account_ids: tuple[str, ...]
    max_notional_limit: Decimal
    allowed_instruments: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "operator_id", self.operator_id.strip())
        object.__setattr__(self, "reason", self.reason.strip())
        object.__setattr__(self, "risk_approver_id", self.risk_approver_id.strip())
        object.__setattr__(
            self,
            "engineering_approver_id",
            self.engineering_approver_id.strip(),
        )
        if self.expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware")
        object.__setattr__(self, "strategy_ids", self._normalized_scope(self.strategy_ids))
        object.__setattr__(self, "account_ids", self._normalized_scope(self.account_ids))
        object.__setattr__(
            self,
            "allowed_instruments",
            self._normalized_scope(self.allowed_instruments),
        )
        object.__setattr__(self, "max_notional_limit", Decimal(str(self.max_notional_limit)))

    @property
    def expired_at_utc(self) -> datetime:
        """Return the signoff expiry normalized to UTC for comparisons and evidence."""

        return self.expires_at.astimezone(UTC)

    def to_payload(self) -> dict[str, Any]:
        """Serialize signoff facts for manifests and runtime events."""

        return {
            "operator_id": self.operator_id,
            "reason": self.reason,
            "risk_approver_id": self.risk_approver_id,
            "engineering_approver_id": self.engineering_approver_id,
            "expires_at": self.expired_at_utc.isoformat(),
            "strategy_ids": list(self.strategy_ids),
            "account_ids": list(self.account_ids),
            "max_notional_limit": str(self.max_notional_limit),
            "allowed_instruments": list(self.allowed_instruments),
        }

    @staticmethod
    def _normalized_scope(values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(str(value).strip() for value in values if str(value).strip())
        return normalized


@dataclass(frozen=True, slots=True)
class LiveCapitalEnablementRequest:
    """Request to evaluate live-capital enablement for one intended order scope."""

    operator_signoff: OperatorSignoff | None
    strategy_id: str
    account_id: str
    instrument_id: str
    requested_notional: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "strategy_id", self.strategy_id.strip())
        object.__setattr__(self, "account_id", self.account_id.strip())
        object.__setattr__(self, "instrument_id", self.instrument_id.strip())
        object.__setattr__(self, "requested_notional", Decimal(str(self.requested_notional)))

    def evaluate(self, *, now: datetime | None = None) -> LiveCapitalEnablementDecision:
        """Evaluate dual-control, expiry, and request scope."""

        evaluated_at = now or datetime.now(UTC)
        if evaluated_at.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        signoff = self.operator_signoff
        reasons: list[str] = []
        if signoff is None:
            reasons.append("operator_signoff is required")
        else:
            reasons.extend(self._signoff_reasons(signoff, evaluated_at=evaluated_at))
        allowed = not reasons
        return LiveCapitalEnablementDecision(
            allowed=allowed,
            order_permission=(
                OrderSubmissionPermission.LIVE_ORDERS_ALLOWED
                if allowed
                else OrderSubmissionPermission.OBSERVATION_ONLY
            ),
            reason="; ".join(reasons) if reasons else "live capital signoff accepted",
            evaluated_at=evaluated_at.astimezone(UTC),
            operator_signoff=signoff,
            request=self,
        )

    def _signoff_reasons(
        self,
        signoff: OperatorSignoff,
        *,
        evaluated_at: datetime,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if not signoff.operator_id:
            reasons.append("operator_id is required")
        if not signoff.reason:
            reasons.append("reason is required")
        if not signoff.risk_approver_id:
            reasons.append("risk_approver_id is required")
        if not signoff.engineering_approver_id:
            reasons.append("engineering_approver_id is required")
        approvers = {
            signoff.operator_id,
            signoff.risk_approver_id,
            signoff.engineering_approver_id,
        }
        if "" not in approvers and len(approvers) != 3:
            reasons.append("operator, risk, and engineering approvers must be distinct")
        if signoff.expired_at_utc <= evaluated_at.astimezone(UTC):
            reasons.append("operator_signoff expired")
        if not signoff.strategy_ids:
            reasons.append("strategy_ids scope is required")
        elif self.strategy_id not in signoff.strategy_ids:
            reasons.append(f"strategy_id {self.strategy_id} is not approved")
        if not signoff.account_ids:
            reasons.append("account_ids scope is required")
        elif self.account_id not in signoff.account_ids:
            reasons.append(f"account_id {self.account_id} is not approved")
        if not signoff.allowed_instruments:
            reasons.append("allowed_instruments scope is required")
        elif self.instrument_id not in signoff.allowed_instruments:
            reasons.append(f"instrument_id {self.instrument_id} is not approved")
        if signoff.max_notional_limit <= Decimal("0"):
            reasons.append("max_notional_limit must be positive")
        elif self.requested_notional > signoff.max_notional_limit:
            reasons.append("requested_notional exceeds max_notional_limit")
        return tuple(reasons)

    def to_payload(self) -> dict[str, Any]:
        """Serialize requested live-capital scope."""

        return {
            "strategy_id": self.strategy_id,
            "account_id": self.account_id,
            "instrument_id": self.instrument_id,
            "requested_notional": str(self.requested_notional),
        }


@dataclass(frozen=True, slots=True)
class LiveCapitalEnablementDecision:
    """Decision resulting from a live-capital enablement request."""

    allowed: bool
    order_permission: OrderSubmissionPermission
    reason: str
    evaluated_at: datetime
    operator_signoff: OperatorSignoff | None
    request: LiveCapitalEnablementRequest

    @property
    def observation_only(self) -> bool:
        """Return whether this decision downgrades the runtime to observation-only."""

        return not self.allowed

    def checklist_evidence(self) -> str:
        """Return compact startup checklist evidence for this decision."""

        signoff = self.operator_signoff
        if signoff is None:
            return f"allowed={self.allowed};reason={self.reason}"
        return (
            f"allowed={self.allowed};"
            f"operator_id={signoff.operator_id};"
            f"risk_approver_id={signoff.risk_approver_id};"
            f"engineering_approver_id={signoff.engineering_approver_id};"
            f"expires_at={signoff.expired_at_utc.isoformat()};"
            f"strategy_ids={','.join(signoff.strategy_ids)};"
            f"account_ids={','.join(signoff.account_ids)};"
            f"allowed_instruments={','.join(signoff.allowed_instruments)};"
            f"max_notional_limit={signoff.max_notional_limit};"
            f"reason={self.reason}"
        )

    def to_payload(self) -> dict[str, Any]:
        """Serialize the decision for runtime events and manifests."""

        return {
            "allowed": self.allowed,
            "observation_only": self.observation_only,
            "order_submission_permission": self.order_permission.value,
            "reason": self.reason,
            "evaluated_at": self.evaluated_at.astimezone(UTC).isoformat(),
            "request": self.request.to_payload(),
            "operator_signoff": (
                self.operator_signoff.to_payload() if self.operator_signoff is not None else None
            ),
        }

    def to_runtime_event(self) -> RuntimeEvent:
        """Create normalized runtime evidence for the signoff decision."""

        return RuntimeEvent(
            kind="runtime.live_capital.signoff_decision",
            payload=self.to_payload(),
        )


@dataclass(frozen=True, slots=True)
class LiveCapitalOrderDecision:
    """Last-mile gate for real-money broker order submission."""

    runtime_mode: RuntimeMode | str
    order_submission_permission: OrderSubmissionPermission | str
    startup_decision_status: object
    operator_signoff_valid: bool
    market_data_permission: str
    market_data_freshness: str
    reconciliation_status: str
    kill_switch_active: bool
    broker_account_kind: str
    broker_account_code: str
    gateway_port: int
    approved_gateway_port_override: bool = False
    disabled_reason: str | None = None

    @classmethod
    def disabled(cls) -> LiveCapitalOrderDecision:
        """Return the default fail-closed live-capital order decision."""

        return cls(
            runtime_mode=RuntimeMode.LIVE,
            order_submission_permission=OrderSubmissionPermission.OBSERVATION_ONLY,
            startup_decision_status="block",
            operator_signoff_valid=False,
            market_data_permission="unknown",
            market_data_freshness="unknown",
            reconciliation_status="unknown",
            kill_switch_active=True,
            broker_account_kind="unknown",
            broker_account_code="",
            gateway_port=0,
            disabled_reason="LIVE_CAPITAL_DISABLED",
        )

    def assert_live_order_allowed(self) -> None:
        """Raise before a real-money order can reach an execution adapter."""

        reason = self.blocked_reason()
        if reason is not None:
            raise PermissionError(reason)

    def blocked_reason(self) -> str | None:
        """Return the first blocking reason for live-capital order submission."""

        if self.disabled_reason is not None:
            return self.disabled_reason
        if RuntimeMode.from_value(self.runtime_mode) is not RuntimeMode.LIVE:
            return "LIVE_RUNTIME_MODE_REQUIRED"
        if (
            OrderSubmissionPermission(self.order_submission_permission)
            is not OrderSubmissionPermission.LIVE_ORDERS_ALLOWED
        ):
            return "LIVE_ORDER_PERMISSION_REQUIRED"
        if self._status_value(self.startup_decision_status) != "allow_live":
            return "LIVE_STARTUP_NOT_ALLOWED"
        if not self.operator_signoff_valid:
            return "LIVE_OPERATOR_SIGNOFF_REQUIRED"
        if self.market_data_permission.strip().lower() != "live":
            return "LIVE_MARKET_DATA_PERMISSION_REQUIRED"
        if self.market_data_freshness.strip().lower() != "fresh":
            return "LIVE_MARKET_DATA_NOT_FRESH"
        if self.reconciliation_status.strip().lower() != "clean":
            return "LIVE_RECONCILIATION_NOT_CLEAN"
        if self.kill_switch_active:
            return "LIVE_KILL_SWITCH_ACTIVE"
        if self.broker_account_kind.strip().lower() != "live":
            return "LIVE_ACCOUNT_KIND_REQUIRED"
        if not _is_live_account_code(self.broker_account_code):
            return "LIVE_ACCOUNT_CODE_REQUIRED"
        if self.gateway_port != 4001 and not self.approved_gateway_port_override:
            return "LIVE_GATEWAY_PORT_REQUIRED"
        return None

    @staticmethod
    def _status_value(value: object) -> str:
        raw_value = getattr(value, "value", value)
        return str(raw_value).strip().lower()


@dataclass(frozen=True, slots=True)
class LiveCapitalReadinessDecision:
    """Decision for whether prerequisite evidence permits live-capital enablement."""

    ready: bool
    reason_code: str | None
    evidence_path: Path | None = None

    @classmethod
    def from_kill_switch_drill_evidence(cls, evidence_path: Path) -> LiveCapitalReadinessDecision:
        """Require valid kill-switch drill evidence before live capital can be ready."""

        if not evidence_path.exists():
            return cls(
                ready=False,
                reason_code="KILL_SWITCH_DRILL_EVIDENCE_MISSING",
                evidence_path=evidence_path,
            )
        try:
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return cls(
                ready=False,
                reason_code="KILL_SWITCH_DRILL_EVIDENCE_INVALID",
                evidence_path=evidence_path,
            )
        if not isinstance(payload, dict):
            return cls(
                ready=False,
                reason_code="KILL_SWITCH_DRILL_EVIDENCE_INVALID",
                evidence_path=evidence_path,
            )
        if cls._payload_satisfies_kill_switch_gate(payload):
            return cls(ready=True, reason_code=None, evidence_path=evidence_path)
        return cls(
            ready=False,
            reason_code="KILL_SWITCH_DRILL_EVIDENCE_INCOMPLETE",
            evidence_path=evidence_path,
        )

    @staticmethod
    def _payload_satisfies_kill_switch_gate(payload: dict[str, Any]) -> bool:
        manifest = payload.get("manifest")
        if not isinstance(manifest, dict):
            return False
        required_manifest_flags = (
            "kill_switch_blocks_new_orders",
            "kill_switch_allows_safety_cancel",
            "kill_switch_deactivation_requires_authorized_signoff",
            "live_capital_disabled_by_default",
            "deterministic_no_network",
        )
        return (
            payload.get("schema_version") == 1
            and payload.get("collector") == "kill_switch_drill"
            and payload.get("live_orders_enabled") is False
            and all(manifest.get(flag) is True for flag in required_manifest_flags)
        )


def _is_live_account_code(account_code: str) -> bool:
    normalized = account_code.strip().upper()
    return normalized.startswith("DU") and not normalized.startswith("DUP")


__all__ = [
    "LiveCapitalEnablementDecision",
    "LiveCapitalEnablementRequest",
    "LiveCapitalOrderDecision",
    "LiveCapitalReadinessDecision",
    "OperatorSignoff",
]
