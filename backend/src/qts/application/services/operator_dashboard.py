"""Operator dashboard status projection owner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from qts.application.dto import OperatorDashboardStatusDTO, OperatorStatusFieldDTO


class OperatorDashboardService:
    """Owns default operator dashboard status projection."""

    def __init__(self, *, status_override: OperatorDashboardStatusDTO | None = None) -> None:
        self._status_override = status_override

    def status(
        self,
        *,
        runtime_state: str,
        runtime_mode: str,
        kill_switch_state: dict[str, object],
    ) -> OperatorDashboardStatusDTO:
        """Return the application-owned operator dashboard state."""
        if self._status_override is not None:
            return self._status_override
        observed_at = datetime.now(UTC)
        return OperatorDashboardStatusDTO(
            runtime_state=self._field(runtime_state, observed_at),
            runtime_mode=self._field(runtime_mode, observed_at),
            order_permission_state=self._field("enabled", observed_at),
            broker_connection_state=self._field("disconnected", observed_at),
            market_data_permission_state=self._field("enabled", observed_at),
            stale_subscriptions=self._field((), observed_at),
            open_orders=self._field((), observed_at),
            positions=self._field((), observed_at),
            cash_snapshot=self._field((), observed_at),
            kill_switch_state=self._field(kill_switch_state, observed_at),
            last_reconciliation_result=self._field(
                {"status": "not_requested", "drift_count": 0},
                observed_at,
            ),
            unresolved_broker_callbacks=self._field((), observed_at),
            event_sink=self._field({"path": None, "hash": None, "row_count": 0}, observed_at),
            latest_manifest=self._field({"path": None, "hash": None}, observed_at),
        )

    @staticmethod
    def _field(value: Any, observed_at: datetime) -> OperatorStatusFieldDTO:
        return OperatorStatusFieldDTO(value=value, timestamp=observed_at)


__all__ = ["OperatorDashboardService"]
