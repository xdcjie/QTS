from __future__ import annotations

from decimal import Decimal

from qts.core.ids import BrokerId
from qts.domain.orders import OrderType, TimeInForce
from qts.execution.adapters.brokerage_capabilities import brokerage_model_for_name
from qts.execution.brokerage_model import BrokerageModel


def test_ibkr_equity_brokerage_model_estimates_costs_and_capabilities() -> None:
    model = brokerage_model_for_name("IBKR_EQUITY")

    assert model.model_id == "ibkr-equity-assumption-v1"
    assert model.commission_for_notional(Decimal("10000")) == Decimal("5.0000")
    assert model.initial_margin_for_notional(Decimal("10000")) == Decimal("5000.00")
    assert model.slippage_for_notional(Decimal("10000")) == Decimal("1")
    assert model.supports("equity", OrderType.LIMIT, TimeInForce.DAY)
    assert not model.supports("future", OrderType.LIMIT, TimeInForce.DAY)
    assert not model.supports("equity", OrderType.STOP, TimeInForce.DAY)


def test_simulated_brokerage_model_has_zero_cost_broad_capability_defaults() -> None:
    model = BrokerageModel.simulated()

    assert model.commission_for_notional(Decimal("10000")) == Decimal("0")
    assert model.initial_margin_for_notional(Decimal("10000")) == Decimal("0")
    assert model.slippage_for_notional(Decimal("10000")) == Decimal("0")
    assert model.supports("equity", OrderType.MARKET, TimeInForce.DAY)
    assert model.capabilities.supports_fractional is True


def test_brokerage_model_manifest_serializes_auditable_assumptions() -> None:
    payload = brokerage_model_for_name("IBKR_EQUITY").to_manifest_payload()

    assert payload["model_id"] == "ibkr-equity-assumption-v1"
    assert payload["commission_rate"] == "0.0005"
    assert payload["minimum_commission"] == "1"
    assert payload["initial_margin_rate"] == "0.50"
    assert payload["slippage_bps"] == "1"
    assert payload["requires_live_market_data"] is True
    assert payload["capabilities"] == {
        "broker_id": BrokerId("ibkr-equity").value,
        "supports_market_orders": True,
        "supports_limit_orders": True,
        "supports_stop_orders": False,
        "supports_cancel": True,
        "supports_replace": False,
        "supports_fractional": False,
        "supports_short": True,
        "min_order_quantity": "1",
        "lot_size": "1",
        "min_tick": None,
        "max_order_quantity": None,
        "supported_asset_classes": ["equity"],
        "supported_order_types": ["limit", "market"],
        "supported_time_in_force": ["day", "gtc"],
    }


def test_brokerage_model_live_market_data_requirement_feeds_risk_engine() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.risk import MarketDataRiskContext, OrderRiskRequest
    from qts.risk import RiskEngine

    model = brokerage_model_for_name("IBKR_EQUITY")
    engine = RiskEngine([]).with_brokerage_model(model)

    decision = engine.check(
        OrderRiskRequest(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            quantity=Decimal("1"),
            price=Decimal("100"),
            multiplier=Decimal("1"),
            market_data=MarketDataRiskContext(permission_state="delayed"),
        )
    )

    assert model.requires_live_market_data is True
    assert decision.reason_code == "MARKET_DATA_DELAYED_FOR_LIVE_ORDER"
    assert (
        RiskEngine([])
        .with_brokerage_model(BrokerageModel.simulated())
        .check(
            OrderRiskRequest(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                quantity=Decimal("1"),
                price=Decimal("100"),
                multiplier=Decimal("1"),
                market_data=MarketDataRiskContext(permission_state="delayed"),
            )
        )
        .approved
    )
