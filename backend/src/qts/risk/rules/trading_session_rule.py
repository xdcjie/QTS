"""Trading session eligibility risk rule."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from qts.domain.risk import OrderRiskRequest, RiskDecision
from qts.registry.calendar_registry import MarketSession


class SessionLookup(Protocol):
    """Calendar session lookup required by the rule."""

    def session_for(self, calendar_id: str, session_date: date) -> MarketSession:
        """Return the internal market session for the date."""


@dataclass(frozen=True, slots=True)
class TradingSessionRule:
    """Reject orders whose order time is outside the configured session."""

    calendar_registry: SessionLookup
    calendar_id: str
    session_date: date

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Perform check."""
        if request.order_time is None:
            return RiskDecision.rejected(
                "MISSING_ORDER_TIME",
                "order_time is required for trading session risk",
            )
        session = self.calendar_registry.session_for(self.calendar_id, self.session_date)
        if not session.interval.contains(request.order_time):
            return RiskDecision.rejected(
                "OUTSIDE_TRADING_SESSION",
                "order_time is outside the trading session",
            )
        return RiskDecision.approve()


__all__ = ["TradingSessionRule"]
