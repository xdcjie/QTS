"""Risk request models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import InstrumentId, StrategyId
from qts.core.time import require_aware_datetime
from qts.domain.orders import OrderSpec
from qts.domain.risk.market_data_context import MarketDataRiskContext


@dataclass(frozen=True, slots=True)
class OrderRiskRequest:
    """Pre-trade risk input for a proposed order."""

    instrument_id: InstrumentId
    quantity: Decimal
    price: Decimal
    multiplier: Decimal
    order_spec: OrderSpec = OrderSpec()
    order_time: datetime | None = None
    current_position: Decimal = Decimal("0")
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    aggregation_decision_id: str | None = None
    conflict_reason: str | None = None
    market_data: MarketDataRiskContext | None = None
    account_equity: Decimal | None = None
    current_exposure: Decimal = Decimal("0")
    intraday_pnl: Decimal | None = None
    current_notional_by_instrument: Mapping[InstrumentId, Decimal] | None = None
    volatility: Decimal | None = None

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
        if self.aggregation_decision_id is not None and not self.aggregation_decision_id.strip():
            raise ValueError("aggregation_decision_id must not be empty")
        if self.conflict_reason is not None and not self.conflict_reason.strip():
            raise ValueError("conflict_reason must not be empty")
        if self.account_equity is not None and self.account_equity <= Decimal("0"):
            raise ValueError("account_equity must be positive")
        if self.current_exposure < Decimal("0"):
            raise ValueError("current_exposure must be non-negative")
        if self.current_notional_by_instrument is not None:
            for instrument_id, notional in self.current_notional_by_instrument.items():
                if not isinstance(instrument_id, InstrumentId):
                    raise TypeError("current_notional_by_instrument keys must be InstrumentId")
                if notional < Decimal("0"):
                    raise ValueError("current instrument notional must be non-negative")
        if self.volatility is not None and self.volatility < Decimal("0"):
            raise ValueError("volatility must be non-negative")

    @property
    def notional(self) -> Decimal:
        """Perform notional."""
        return self.quantity * self.price * self.multiplier


__all__ = ["OrderRiskRequest"]
