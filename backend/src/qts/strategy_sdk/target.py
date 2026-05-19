"""Target intent API objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from qts.domain.orders import OrderSpec, OrderType
from qts.strategy_sdk.asset_ref import AssetRef


class TargetIntentType(StrEnum):
    """Supported target intent kinds."""

    PERCENT = "percent"
    QUANTITY = "quantity"
    VALUE = "value"
    CLOSE = "close"


@dataclass(frozen=True, slots=True)
class TargetIntent:
    """Strategy-emitted intent, later handled by platform risk/order flow."""

    asset: AssetRef
    intent_type: TargetIntentType
    value: Decimal | None
    order_spec: OrderSpec = OrderSpec()

    @property
    def spec(self) -> OrderSpec:
        """Return the typed execution specification for this target."""
        return self.order_spec


__all__ = ["OrderSpec", "OrderType", "TargetIntent", "TargetIntentType"]
