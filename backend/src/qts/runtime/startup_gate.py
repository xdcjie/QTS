"""Broker runtime startup order gate."""

from __future__ import annotations

from dataclasses import dataclass

from qts.runtime.live import BrokerRuntimeStartupDecision
from qts.runtime.mode import RuntimeMode


@dataclass(frozen=True, slots=True)
class BrokerRuntimeStartupGate:
    """Convert startup decisions into fail-closed order-block reason codes."""

    mode: RuntimeMode
    startup_decision: BrokerRuntimeStartupDecision | None

    def blocked_reason(self) -> str | None:
        """Return the startup reason code that should block order submission."""
        if self.startup_decision is None:
            if self.mode is RuntimeMode.LIVE:
                return "LIVE_STARTUP_NOT_ALLOWED"
            if self.mode is RuntimeMode.PAPER_BROKER:
                return "BROKER_STARTUP_NOT_ALLOWED"
            return None
        if not self.startup_decision.order_permission.allows_order_submission:
            return "OBSERVATION_ONLY"
        if (
            self.mode is RuntimeMode.LIVE
            and not self.startup_decision.order_permission.allows_live_orders
        ):
            return "LIVE_ORDER_PERMISSION_REQUIRED"
        if (
            self.startup_decision.order_permission.allows_live_orders
            and not self.startup_decision.real_order_submission_enabled
        ):
            return "LIVE_STARTUP_NOT_ALLOWED"
        return None


__all__ = ["BrokerRuntimeStartupGate"]
