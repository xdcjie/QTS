"""Execution adapter that applies backtest fill-cost assumptions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from qts.core.ids import AccountId, BrokerId, CorrelationId, OrderId, StrategyId
from qts.domain.orders import OrderSide
from qts.execution.broker import BrokerCapabilities, BrokerOrderType
from qts.execution.order_manager import ExecutionReport, ExecutionReportStatus, OrderIntent


class SimulatedExecutionCostModel(Protocol):
    """Cost-model fields required by simulated execution."""

    @property
    def fixed_commission_per_contract(self) -> Decimal:
        """Fixed commission charged per filled unit."""
        ...

    @property
    def slippage_bps(self) -> Decimal:
        """Slippage applied to simulated market fills."""
        ...


@dataclass(frozen=True, slots=True)
class SimulatedExecutionAdapter:
    """Apply deterministic commission and slippage assumptions for backtests."""

    cost_model: SimulatedExecutionCostModel
    capabilities: BrokerCapabilities | None = None

    def __post_init__(self) -> None:
        """Validate and normalize cost-model-backed configuration."""
        if self.cost_model is None:
            raise ValueError("cost_model is required")
        if self.capabilities is None:
            object.__setattr__(
                self,
                "capabilities",
                BrokerCapabilities(
                    broker_id=BrokerId("simulated"),
                    supports_fractional=True,
                ),
            )

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        """Execute a market order with cost-model adjustments."""
        _ = account_id, strategy_id, client_order_id, correlation_id
        if market_price < Decimal("0"):
            raise ValueError("market_price must be non-negative")
        self._validate_market_order(intent)
        slippage = market_price * self.cost_model.slippage_bps / Decimal("10000")
        fill_price = (
            market_price + slippage if intent.side is OrderSide.BUY else market_price - slippage
        )
        commission = self.cost_model.fixed_commission_per_contract * intent.quantity
        return ExecutionReport(
            report_id=f"{broker_order_id}-report-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=fill_price,
            fill_id=f"{broker_order_id}-fill-1",
            commission=commission,
            slippage=abs(fill_price - market_price),
        )

    def _validate_market_order(self, intent: OrderIntent) -> None:
        capabilities = self.capabilities
        if capabilities is None:
            raise RuntimeError("simulated execution capabilities are not configured")
        if not capabilities.supports_order_type(BrokerOrderType.MARKET):
            raise ValueError("market orders are not supported by broker capabilities")
        if (
            not capabilities.supports_fractional
            and intent.quantity != intent.quantity.to_integral_value()
        ):
            raise ValueError("fractional quantity is not supported")
        capabilities.validate_order_quantity(intent.quantity)

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        """Return a deterministic cancellation report for actor parity."""
        _ = order_id, account_id, strategy_id, client_order_id, correlation_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancel-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


__all__ = ["SimulatedExecutionAdapter", "SimulatedExecutionCostModel"]
