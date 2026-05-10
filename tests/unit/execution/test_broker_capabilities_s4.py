from __future__ import annotations

from decimal import Decimal

from qts.core.ids import BrokerId
from qts.execution.broker import BrokerCapabilities, BrokerOrderType, TimeInForce


def test_broker_capabilities_model_order_types_tif_short_and_fractional_support() -> None:
    capabilities = BrokerCapabilities(
        broker_id=BrokerId("ibkr-live"),
        supported_order_types=frozenset({BrokerOrderType.MARKET, BrokerOrderType.LIMIT}),
        supported_time_in_force=frozenset({TimeInForce.DAY, TimeInForce.GTC}),
        supports_fractional=False,
        supports_short=True,
        max_order_quantity=Decimal("1000"),
    )

    assert capabilities.supports_order_type(BrokerOrderType.MARKET)
    assert not capabilities.supports_order_type(BrokerOrderType.STOP)
    assert capabilities.supports_tif(TimeInForce.GTC)
    assert capabilities.supports_short is True
