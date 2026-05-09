from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest
from qts.registry.calendar_registry import MarketSession


@dataclass(frozen=True)
class _CalendarRegistry:
    session: MarketSession

    def session_for(self, calendar_id: str, session_date: date) -> MarketSession:
        assert calendar_id == "XNYS"
        assert session_date == date(2026, 1, 2)
        return self.session


def _request(order_time: datetime) -> OrderRiskRequest:
    from qts.core.ids import InstrumentId

    return OrderRiskRequest(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        quantity=Decimal("1"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        order_time=order_time,
    )


def test_trading_session_rule_approves_orders_inside_session() -> None:
    from qts.core.time import TimeInterval
    from qts.risk.rules.trading_session_rule import TradingSessionRule

    open_time = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    close_time = datetime(2026, 1, 2, 21, 0, tzinfo=UTC)
    session = MarketSession(
        calendar_id="XNYS",
        session_id="2026-01-02",
        interval=TimeInterval(start=open_time, end=close_time),
    )

    decision = TradingSessionRule(
        calendar_registry=_CalendarRegistry(session),
        calendar_id="XNYS",
        session_date=date(2026, 1, 2),
    ).check(_request(open_time + timedelta(minutes=1)))

    assert decision.approved


def test_trading_session_rule_rejects_orders_outside_session() -> None:
    from qts.core.time import TimeInterval
    from qts.risk.rules.trading_session_rule import TradingSessionRule

    open_time = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    close_time = datetime(2026, 1, 2, 21, 0, tzinfo=UTC)
    session = MarketSession(
        calendar_id="XNYS",
        session_id="2026-01-02",
        interval=TimeInterval(start=open_time, end=close_time),
    )

    decision = TradingSessionRule(
        calendar_registry=_CalendarRegistry(session),
        calendar_id="XNYS",
        session_date=date(2026, 1, 2),
    ).check(_request(close_time))

    assert not decision.approved
    assert decision.reason_code == "OUTSIDE_TRADING_SESSION"
