"""Gate tests for market-data freshness fail-closed behaviour (DR-016)."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.risk import MarketDataRiskContext, OrderRiskRequest, RiskDecisionStatus
from qts.risk.rules.market_data_freshness import MarketDataFreshnessRiskRule

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _request(context: MarketDataRiskContext | None) -> OrderRiskRequest:
    return OrderRiskRequest(
        instrument_id=_INSTRUMENT,
        quantity=Decimal("1"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        market_data=context,
    )


def test_missing_context_fails_closed_in_live_required_mode() -> None:
    decision = MarketDataFreshnessRiskRule(require_market_data_context=True).check(_request(None))
    assert decision.status is RiskDecisionStatus.REJECTED
    assert decision.reason_code == "MARKET_DATA_CONTEXT_REQUIRED"


def test_missing_context_allowed_when_not_required() -> None:
    decision = MarketDataFreshnessRiskRule().check(_request(None))
    assert decision.approved


def test_stale_context_rejected_in_both_modes() -> None:
    stale = MarketDataRiskContext(permission_state="live", stale=True)
    for rule in (
        MarketDataFreshnessRiskRule(require_market_data_context=True),
        MarketDataFreshnessRiskRule(require_market_data_context=False),
    ):
        decision = rule.check(_request(stale))
        assert decision.status is RiskDecisionStatus.REJECTED
        assert decision.reason_code == "MARKET_DATA_STALE"


def test_fresh_context_approved() -> None:
    fresh = MarketDataRiskContext(permission_state="live", stale=False)
    decision = MarketDataFreshnessRiskRule(require_market_data_context=True).check(_request(fresh))
    assert decision.approved
