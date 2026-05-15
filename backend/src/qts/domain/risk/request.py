"""Risk request models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import InstrumentId, StrategyId
from qts.core.time import require_aware_datetime
from qts.domain.risk.market_data_context import MarketDataRiskContext


@dataclass(frozen=True, slots=True)
class OrderRiskRequest:
    """Pre-trade risk input for a proposed order."""

    instrument_id: InstrumentId
    quantity: Decimal
    price: Decimal
    multiplier: Decimal
    order_time: datetime | None = None
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    market_data: MarketDataRiskContext | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if self.price < Decimal("0"):
            raise ValueError("price must be non-negative")
        if self.multiplier <= Decimal("0"):
            raise ValueError("multiplier must be positive")
        if self.order_time is not None:
            require_aware_datetime(self.order_time, name="order_time")
        for strategy_id in self.contributing_strategy_ids:
            if not isinstance(strategy_id, StrategyId):
                raise TypeError("contributing_strategy_ids must contain StrategyId values")

    @property
    def notional(self) -> Decimal:
        """Perform notional."""
        return self.quantity * self.price * self.multiplier


__all__ = ["OrderRiskRequest"]
