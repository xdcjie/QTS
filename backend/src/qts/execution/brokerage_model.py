"""Brokerage model assumptions owned by the execution boundary."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import BrokerId
from qts.domain.orders import OrderType, TimeInForce
from qts.execution.broker import BrokerCapabilities


@dataclass(frozen=True, slots=True)
class BrokerageModel:
    """Fee, margin, slippage, and capability assumptions for execution."""

    model_id: str
    capabilities: BrokerCapabilities
    commission_rate: Decimal = Decimal("0")
    minimum_commission: Decimal = Decimal("0")
    initial_margin_rate: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")
    requires_live_market_data: bool = False

    def __post_init__(self) -> None:
        model_id = self.model_id.strip()
        if not model_id:
            raise ValueError("model_id must not be empty")
        object.__setattr__(self, "model_id", model_id)
        object.__setattr__(self, "commission_rate", Decimal(str(self.commission_rate)))
        object.__setattr__(self, "minimum_commission", Decimal(str(self.minimum_commission)))
        object.__setattr__(self, "initial_margin_rate", Decimal(str(self.initial_margin_rate)))
        object.__setattr__(self, "slippage_bps", Decimal(str(self.slippage_bps)))
        if self.commission_rate < Decimal("0"):
            raise ValueError("commission_rate must be non-negative")
        if self.minimum_commission < Decimal("0"):
            raise ValueError("minimum_commission must be non-negative")
        if self.initial_margin_rate < Decimal("0"):
            raise ValueError("initial_margin_rate must be non-negative")
        if self.slippage_bps < Decimal("0"):
            raise ValueError("slippage_bps must be non-negative")

    @classmethod
    def custom(cls) -> BrokerageModel:
        """Return a broad custom model for user-supplied broker assumptions."""
        return cls(
            model_id="custom-assumption-v1",
            capabilities=BrokerCapabilities(
                broker_id=BrokerId("custom"),
                supports_fractional=True,
                supports_stop_orders=True,
                supported_order_types=frozenset(OrderType),
                supported_time_in_force=frozenset(TimeInForce),
            ),
        )

    @classmethod
    def simulated(cls) -> BrokerageModel:
        """Return the default deterministic simulated execution assumptions."""
        return cls(
            model_id="simulated-default-v1",
            capabilities=BrokerCapabilities(
                broker_id=BrokerId("simulated"),
                supports_fractional=True,
                supports_stop_orders=True,
                supported_order_types=frozenset(OrderType),
                supported_time_in_force=frozenset(TimeInForce),
            ),
        )

    @property
    def supported_order_types(self) -> frozenset[OrderType]:
        """Return the brokerage-accepted order types for risk-time gating."""
        return self.capabilities.supported_order_types or frozenset(OrderType)

    def commission_for_notional(self, notional: Decimal) -> Decimal:
        """Estimate commission from notional under this model."""
        normalized = self._validate_notional(notional)
        if normalized == Decimal("0"):
            return Decimal("0")
        commission = normalized * self.commission_rate
        if commission < self.minimum_commission:
            return self.minimum_commission
        return commission

    def initial_margin_for_notional(self, notional: Decimal) -> Decimal:
        """Estimate initial margin from notional under this model."""
        return self._validate_notional(notional) * self.initial_margin_rate

    def slippage_for_notional(self, notional: Decimal) -> Decimal:
        """Estimate absolute notional slippage under this model."""
        return self._validate_notional(notional) * self.slippage_bps / Decimal("10000")

    def supports(
        self,
        asset_class: str,
        order_type: OrderType,
        time_in_force: TimeInForce,
    ) -> bool:
        """Return whether the model supports the requested execution shape."""
        return (
            self.capabilities.supports_asset_class(asset_class)
            and self.capabilities.supports_order_type(order_type)
            and self.capabilities.supports_tif(time_in_force)
        )

    def to_manifest_payload(self) -> dict[str, object]:
        """Serialize auditable brokerage assumptions."""
        return {
            "model_id": self.model_id,
            "commission_rate": str(self.commission_rate),
            "minimum_commission": str(self.minimum_commission),
            "initial_margin_rate": str(self.initial_margin_rate),
            "slippage_bps": str(self.slippage_bps),
            "requires_live_market_data": self.requires_live_market_data,
            "capabilities": self.capabilities.to_manifest_payload(),
        }

    def _validate_notional(self, notional: Decimal) -> Decimal:
        normalized = Decimal(str(notional))
        if normalized < Decimal("0"):
            raise ValueError("notional must be non-negative")
        return normalized


__all__ = ["BrokerageModel"]
