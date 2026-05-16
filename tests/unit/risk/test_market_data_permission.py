from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.risk import OrderRiskRequest, RiskDecision


def _request(*, permission_state: str | None = "live", stale: bool = False) -> OrderRiskRequest:
    from qts.domain.risk import MarketDataRiskContext, OrderRiskRequest

    return OrderRiskRequest(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        quantity=Decimal("1"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        order_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        market_data=MarketDataRiskContext(
            permission_state=permission_state,
            stale=stale,
            evidence={
                "source_id": "ibkr-paper-md",
                "permission_state": permission_state,
                "age_seconds": 61,
                "max_age_seconds": 30,
            },
        ),
    )


def _market_data_evidence(decision: RiskDecision) -> Mapping[str, object]:
    market_data = decision.evidence["market_data"]
    assert isinstance(market_data, Mapping)
    return market_data


def test_market_data_permission_rule_rejects_delayed_live_orders_with_evidence() -> None:
    from qts.risk.rules.market_data_permission import MarketDataPermissionRiskRule

    decision = MarketDataPermissionRiskRule().check(_request(permission_state="delayed"))

    assert decision.reason_code == "MARKET_DATA_DELAYED_FOR_LIVE_ORDER"
    assert _market_data_evidence(decision)["permission_state"] == "delayed"


def test_market_data_permission_rule_rejects_frozen_unavailable_and_unknown() -> None:
    from qts.risk.rules.market_data_permission import MarketDataPermissionRiskRule

    rule = MarketDataPermissionRiskRule()

    assert (
        rule.check(_request(permission_state="frozen")).reason_code
        == "MARKET_DATA_FROZEN_FOR_LIVE_ORDER"
    )
    assert (
        rule.check(_request(permission_state="unavailable")).reason_code
        == "MARKET_DATA_UNAVAILABLE"
    )
    assert (
        rule.check(_request(permission_state=None)).reason_code == "MARKET_DATA_PERMISSION_UNKNOWN"
    )


def test_market_data_freshness_rule_rejects_stale_data_with_evidence() -> None:
    from qts.risk.rules.market_data_freshness import MarketDataFreshnessRiskRule

    decision = MarketDataFreshnessRiskRule().check(_request(stale=True))

    assert decision.reason_code == "MARKET_DATA_STALE"
    assert _market_data_evidence(decision)["age_seconds"] == 61


def test_risk_engine_forces_market_data_permission_and_freshness_rules() -> None:
    from qts.risk.risk_engine import RiskEngine

    engine = RiskEngine([], require_live_market_data=True)

    delayed = engine.check(_request(permission_state="delayed"))
    frozen = engine.check(_request(permission_state="frozen"))
    unavailable = engine.check(_request(permission_state="unavailable"))
    stale = engine.check(_request(stale=True))

    assert delayed.reason_code == "MARKET_DATA_DELAYED_FOR_LIVE_ORDER"
    assert frozen.reason_code == "MARKET_DATA_FROZEN_FOR_LIVE_ORDER"
    assert unavailable.reason_code == "MARKET_DATA_UNAVAILABLE"
    assert stale.reason_code == "MARKET_DATA_STALE"
    assert _market_data_evidence(delayed)["source_id"] == "ibkr-paper-md"
    assert _market_data_evidence(stale)["age_seconds"] == 61
