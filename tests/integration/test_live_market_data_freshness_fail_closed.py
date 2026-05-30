"""Integration: live-required freshness rule fails closed on missing context (DR-016)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.risk.rules.market_data_freshness import MarketDataFreshnessRiskRule

from tests.support.risk_runtime_harness import RiskRuntimeHarness


def test_live_required_mode_rejects_order_with_missing_market_data_context() -> None:
    harness = RiskRuntimeHarness(
        rules=[MarketDataFreshnessRiskRule(require_market_data_context=True)],
        initial_cash=Decimal("1000000"),
    )
    # No market-data context provided -> fail closed in live-required mode.
    result = harness.submit(
        target_quantity="1", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100"
    )
    assert result.orders == ()
    assert result.risk_decisions[0].reason_code == "MARKET_DATA_CONTEXT_REQUIRED"


def test_optional_mode_allows_missing_market_data_context() -> None:
    harness = RiskRuntimeHarness(
        rules=[MarketDataFreshnessRiskRule(require_market_data_context=False)],
        initial_cash=Decimal("1000000"),
    )
    result = harness.submit(
        target_quantity="1", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100"
    )
    assert result.orders
    assert all(d.approved for d in result.risk_decisions)
