from __future__ import annotations

from decimal import Decimal

from qts.core.ids import BrokerId
from qts.execution.adapters.brokerage_capabilities import brokerage_model_for_name
from qts.execution.broker import BrokerOrderType, TimeInForce
from qts.execution.brokerage_model import BrokerageModel


def test_ibkr_equity_brokerage_model_estimates_costs_and_capabilities() -> None:
    model = brokerage_model_for_name("IBKR_EQUITY")

    assert model.model_id == "ibkr-equity-assumption-v1"
    assert model.commission_for_notional(Decimal("10000")) == Decimal("5.0000")
    assert model.initial_margin_for_notional(Decimal("10000")) == Decimal("5000.00")
    assert model.slippage_for_notional(Decimal("10000")) == Decimal("1")
    assert model.supports("equity", BrokerOrderType.LIMIT, TimeInForce.DAY)
    assert not model.supports("future", BrokerOrderType.LIMIT, TimeInForce.DAY)
    assert not model.supports("equity", BrokerOrderType.STOP, TimeInForce.DAY)


def test_simulated_brokerage_model_has_zero_cost_broad_capability_defaults() -> None:
    model = BrokerageModel.simulated()

    assert model.commission_for_notional(Decimal("10000")) == Decimal("0")
    assert model.initial_margin_for_notional(Decimal("10000")) == Decimal("0")
    assert model.slippage_for_notional(Decimal("10000")) == Decimal("0")
    assert model.supports("equity", BrokerOrderType.MARKET, TimeInForce.DAY)
    assert model.capabilities.supports_fractional is True


def test_brokerage_model_manifest_serializes_auditable_assumptions() -> None:
    payload = brokerage_model_for_name("IBKR_EQUITY").to_manifest_payload()

    assert payload["model_id"] == "ibkr-equity-assumption-v1"
    assert payload["commission_rate"] == "0.0005"
    assert payload["minimum_commission"] == "1"
    assert payload["initial_margin_rate"] == "0.50"
    assert payload["slippage_bps"] == "1"
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
