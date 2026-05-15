"""Runtime order permission vocabulary."""

from __future__ import annotations

from enum import StrEnum


class LiveOrderPermission(StrEnum):
    """Explicit order permission for broker-capable runtime modes."""

    OBSERVATION_ONLY = "observation_only"
    PAPER_ORDERS_ALLOWED = "paper_orders_allowed"
    LIVE_ORDERS_ALLOWED = "live_orders_allowed"

    @property
    def allows_order_submission(self) -> bool:
        """Return whether any broker order submission is allowed."""
        return self is not LiveOrderPermission.OBSERVATION_ONLY

    @property
    def allows_live_orders(self) -> bool:
        """Return whether real-money live order submission is allowed."""
        return self is LiveOrderPermission.LIVE_ORDERS_ALLOWED


__all__ = [
    "LiveOrderPermission",
]
