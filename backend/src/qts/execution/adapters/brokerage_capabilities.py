"""Brokerage-model capability mappings for execution adapters."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import BrokerId
from qts.execution.broker import BrokerCapabilities, BrokerOrderType, TimeInForce


def broker_capabilities_for_model(brokerage_model: str) -> BrokerCapabilities:
    """Return conservative execution capabilities for a named brokerage model."""

    model = brokerage_model.strip().upper()
    if not model:
        raise ValueError("brokerage_model must not be empty")
    if model == "CUSTOM":
        return BrokerCapabilities(
            broker_id=BrokerId("custom"),
            supports_fractional=True,
        )
    if model == "IBKR_EQUITY":
        return BrokerCapabilities(
            broker_id=BrokerId("ibkr-equity"),
            supported_order_types=frozenset({BrokerOrderType.MARKET, BrokerOrderType.LIMIT}),
            supported_time_in_force=frozenset({TimeInForce.DAY, TimeInForce.GTC}),
            supports_fractional=False,
            supports_short=True,
            min_order_quantity=Decimal("1"),
            lot_size=Decimal("1"),
            supported_asset_classes=frozenset({"equity"}),
        )
    if model == "IBKR_FUTURES":
        return BrokerCapabilities(
            broker_id=BrokerId("ibkr-futures"),
            supported_order_types=frozenset({BrokerOrderType.MARKET, BrokerOrderType.LIMIT}),
            supported_time_in_force=frozenset({TimeInForce.DAY, TimeInForce.GTC}),
            supports_fractional=False,
            supports_short=True,
            min_order_quantity=Decimal("1"),
            lot_size=Decimal("1"),
            supported_asset_classes=frozenset({"future"}),
        )
    if model == "IBKR_OPTIONS":
        return BrokerCapabilities(
            broker_id=BrokerId("ibkr-options"),
            supported_order_types=frozenset({BrokerOrderType.MARKET, BrokerOrderType.LIMIT}),
            supported_time_in_force=frozenset({TimeInForce.DAY, TimeInForce.GTC}),
            supports_fractional=False,
            supports_short=False,
            min_order_quantity=Decimal("1"),
            lot_size=Decimal("1"),
            supported_asset_classes=frozenset({"option"}),
        )
    raise ValueError(f"unsupported brokerage_model: {brokerage_model}")


__all__ = ["broker_capabilities_for_model"]
