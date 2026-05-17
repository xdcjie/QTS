"""Brokerage-model capability access for execution adapters."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import BrokerId
from qts.execution.broker import BrokerCapabilities, BrokerOrderType, TimeInForce
from qts.execution.brokerage_model import BrokerageModel


def brokerage_model_for_name(brokerage_model: str) -> BrokerageModel:
    """Resolve broker-specific model assumptions at the adapter boundary."""
    model = brokerage_model.strip().upper()
    if not model:
        raise ValueError("brokerage_model must not be empty")
    if model == "CUSTOM":
        return BrokerageModel.custom()
    if model in {"SIMULATED", "SIMULATED_DEFAULT"}:
        return BrokerageModel.simulated()
    if model == "IBKR_EQUITY":
        return BrokerageModel(
            model_id="ibkr-equity-assumption-v1",
            capabilities=BrokerCapabilities(
                broker_id=BrokerId("ibkr-equity"),
                supported_order_types=frozenset({BrokerOrderType.MARKET, BrokerOrderType.LIMIT}),
                supported_time_in_force=frozenset({TimeInForce.DAY, TimeInForce.GTC}),
                supports_fractional=False,
                supports_short=True,
                min_order_quantity=Decimal("1"),
                lot_size=Decimal("1"),
                supported_asset_classes=frozenset({"equity"}),
            ),
            commission_rate=Decimal("0.0005"),
            minimum_commission=Decimal("1"),
            initial_margin_rate=Decimal("0.50"),
            slippage_bps=Decimal("1"),
        )
    if model == "IBKR_FUTURES":
        return BrokerageModel(
            model_id="ibkr-futures-assumption-v1",
            capabilities=BrokerCapabilities(
                broker_id=BrokerId("ibkr-futures"),
                supported_order_types=frozenset({BrokerOrderType.MARKET, BrokerOrderType.LIMIT}),
                supported_time_in_force=frozenset({TimeInForce.DAY, TimeInForce.GTC}),
                supports_fractional=False,
                supports_short=True,
                min_order_quantity=Decimal("1"),
                lot_size=Decimal("1"),
                supported_asset_classes=frozenset({"future"}),
            ),
            initial_margin_rate=Decimal("0.10"),
            slippage_bps=Decimal("1"),
        )
    if model == "IBKR_OPTIONS":
        return BrokerageModel(
            model_id="ibkr-options-assumption-v1",
            capabilities=BrokerCapabilities(
                broker_id=BrokerId("ibkr-options"),
                supported_order_types=frozenset({BrokerOrderType.MARKET, BrokerOrderType.LIMIT}),
                supported_time_in_force=frozenset({TimeInForce.DAY, TimeInForce.GTC}),
                supports_fractional=False,
                supports_short=False,
                min_order_quantity=Decimal("1"),
                lot_size=Decimal("1"),
                supported_asset_classes=frozenset({"option"}),
            ),
            initial_margin_rate=Decimal("1"),
            slippage_bps=Decimal("1"),
        )
    raise ValueError(f"unsupported brokerage_model: {brokerage_model}")


def broker_capabilities_for_model(brokerage_model: str) -> BrokerCapabilities:
    """Return conservative execution capabilities for a named brokerage model."""

    return brokerage_model_for_name(brokerage_model).capabilities


__all__ = ["broker_capabilities_for_model", "brokerage_model_for_name"]
