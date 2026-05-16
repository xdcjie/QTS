"""Runtime order processing result evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qts.execution.broker import BrokerExecutionReport, BrokerOrderRequest


@dataclass(frozen=True, slots=True)
class RuntimeOrderResult:
    """Result of runtime order processing."""

    request: BrokerOrderRequest | None
    accepted: bool
    report: BrokerExecutionReport | None = None
    reason_code: str | None = None

    def to_evidence(self) -> dict[str, Any]:
        """Serialize order permission evidence for runtime events."""
        request_payload: dict[str, Any] | None = None
        if self.request is not None:
            request_payload = {
                "order_id": self.request.order_id.value,
                "client_order_id": self.request.client_order_id,
                "account_id": self.request.account_id.value,
                "strategy_id": (
                    self.request.strategy_id.value if self.request.strategy_id is not None else None
                ),
                "instrument_id": self.request.instrument_id.value,
                "side": self.request.side.value,
                "quantity": str(self.request.quantity),
            }
        return {
            "accepted": self.accepted,
            "reason_code": self.reason_code,
            "request": request_payload,
            "report": self.report is not None,
        }


__all__ = ["RuntimeOrderResult"]
