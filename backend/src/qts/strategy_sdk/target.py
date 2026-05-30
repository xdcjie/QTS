"""Target intent API objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from uuid import uuid4

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
    intent_id: str = field(default_factory=lambda: str(uuid4()))
    order_spec: OrderSpec = field(default_factory=OrderSpec)
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType({str(key): str(value) for key, value in self.metadata.items()}),
        )

    @property
    def spec(self) -> OrderSpec:
        """Return the typed execution specification for this target."""
        return self.order_spec


__all__ = ["OrderSpec", "OrderType", "TargetIntent", "TargetIntentType"]
