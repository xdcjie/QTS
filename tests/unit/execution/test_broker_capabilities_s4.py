from __future__ import annotations

from decimal import Decimal

from qts.core.ids import BrokerId
from qts.domain.orders import OrderType, TimeInForce
from qts.execution.broker import BrokerCapabilities


def test_broker_capabilities_model_order_types_tif_short_and_fractional_support() -> None:
    capabilities = BrokerCapabilities(
        broker_id=BrokerId("ibkr-live"),
        supported_order_types=frozenset({OrderType.MARKET, OrderType.LIMIT}),
        supported_time_in_force=frozenset({TimeInForce.DAY, TimeInForce.GTC}),
        supports_fractional=False,
        supports_short=True,
        min_order_quantity=Decimal("1"),
        lot_size=Decimal("1"),
        min_tick=Decimal("0.01"),
        max_order_quantity=Decimal("1000"),
    )

    assert capabilities.supports_order_type(OrderType.MARKET)
    assert not capabilities.supports_order_type(OrderType.STOP)
    assert capabilities.supports_tif(TimeInForce.GTC)
    assert capabilities.supports_short is True
    assert capabilities.min_order_quantity == Decimal("1")
    assert capabilities.lot_size == Decimal("1")
    assert capabilities.min_tick == Decimal("0.01")


def test_brokerage_model_mapping_lives_at_adapter_boundary() -> None:
    from qts.execution.adapters.brokerage_capabilities import (
        broker_capabilities_for_model,
        brokerage_model_for_name,
    )

    capabilities = broker_capabilities_for_model("IBKR_FUTURES")

    assert capabilities == brokerage_model_for_name("IBKR_FUTURES").capabilities
    assert capabilities.broker_id == BrokerId("ibkr-futures")
    assert capabilities.supports_order_type(OrderType.MARKET)
    assert capabilities.supports_tif(TimeInForce.DAY)
    assert capabilities.supports_fractional is False
    assert capabilities.supported_asset_classes == frozenset({"future"})


def test_broker_capabilities_supports_replace_defaults_to_false() -> None:
    capabilities = BrokerCapabilities(broker_id=BrokerId("test-broker"))

    assert capabilities.supports_replace is False

    manifest = capabilities.to_manifest_payload()
    assert manifest["supports_replace"] is False
