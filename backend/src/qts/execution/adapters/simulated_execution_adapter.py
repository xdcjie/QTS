"""Execution adapter that applies backtest fill-cost assumptions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from qts.core.ids import AccountId, BrokerId, CorrelationId, OrderId, StrategyId
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
    OrderType,
    TimeInForce,
)
from qts.execution.broker import BrokerCapabilities
from qts.execution.simulator.fill_model import ImmediateFillModel


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
class _FillDecision:
    """Outcome of bar-touch evaluation for one order."""

    triggered: bool
    fill_price: Decimal


_UNSUPPORTED_SIM_ORDER_TYPES: frozenset[OrderType] = frozenset(
    {
        OrderType.TRAILING_STOP,
        OrderType.MARKET_ON_OPEN,
        OrderType.MARKET_ON_CLOSE,
        OrderType.ICEBERG,
    }
)
_SIM_SUPPORTED_ORDER_TYPES: frozenset[OrderType] = (
    frozenset(OrderType) - _UNSUPPORTED_SIM_ORDER_TYPES
)


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
                    supports_stop_orders=True,
                    supported_order_types=_SIM_SUPPORTED_ORDER_TYPES,
                    supported_time_in_force=frozenset(TimeInForce),
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
        bar_high: Decimal | None = None,
        bar_low: Decimal | None = None,
        bar_time: datetime | None = None,
    ) -> ExecutionReport:
        """Execute one order against a single bar's price range.

        The adapter requires ``bar_high`` and ``bar_low`` for non-MARKET orders;
        when callers omit them (legacy market-only paths), the market price is
        treated as a single-tick bar. LIMIT/STOP variants emit an ACCEPTED
        no-fill report when the bar's range did not cross the trigger price.
        Order types that need persistent state (trailing stop, MOO/MOC,
        iceberg) raise :class:`NotImplementedError` rather than masquerading as
        market orders.
        """
        _ = account_id, strategy_id, client_order_id, correlation_id
        if market_price < Decimal("0"):
            raise ValueError("market_price must be non-negative")
        self._validate_order(intent)

        spec = intent.order_spec
        if spec.order_type in _UNSUPPORTED_SIM_ORDER_TYPES:
            raise NotImplementedError(
                f"simulated execution does not yet support {spec.order_type.value} orders"
            )

        high, low = self._resolve_bar_range(market_price, bar_high, bar_low)
        decision = self._evaluate_fill(
            intent, market_price=market_price, bar_high=high, bar_low=low
        )
        if not decision.triggered:
            return ExecutionReport(
                report_id=f"{broker_order_id}-report-1",
                broker_order_id=broker_order_id,
                status=ExecutionReportStatus.ACCEPTED,
                filled_quantity=Decimal("0"),
                fill_price=None,
                fill_id=None,
                fill_time=bar_time,
            )

        base_price = decision.fill_price
        slippage = base_price * self.cost_model.slippage_bps / Decimal("10000")
        fill_price = (
            base_price + slippage if intent.side is OrderSide.BUY else base_price - slippage
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
            slippage=abs(fill_price - base_price),
            fill_time=bar_time,
        )

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

    def execution_assumptions_payload(self) -> dict[str, object]:
        """Serialize simulated execution assumptions for report manifests."""
        capabilities = self.capabilities
        if capabilities is None:
            raise RuntimeError("simulated execution capabilities are not configured")
        payload = ImmediateFillModel().to_manifest_payload()
        payload.update(
            {
                "slippage_model_name": self._slippage_model_name(),
                "slippage_model_version": "1",
                "commission_model_name": self._commission_model_name(),
                "commission_model_version": "1",
                "broker_capability_model": capabilities.to_manifest_payload(),
                "unsupported_order_rejection_policy": "reject_and_emit_runtime_event",
                "market_data_latency_model": "zero_latency_replay",
                "bar_touch_rule": "limit_requires_bar_traversal",
            }
        )
        return payload

    def broker_capability_payload(self) -> dict[str, object]:
        """Serialize broker capability assumptions used by this adapter."""
        capabilities = self.capabilities
        if capabilities is None:
            raise RuntimeError("simulated execution capabilities are not configured")
        return capabilities.to_manifest_payload()

    def _validate_order(self, intent: OrderIntent) -> None:
        capabilities = self.capabilities
        if capabilities is None:
            raise RuntimeError("simulated execution capabilities are not configured")
        if not capabilities.supports_order_type(intent.order_spec.order_type):
            if intent.order_spec.order_type is OrderType.MARKET:
                raise ValueError("market orders are not supported by broker capabilities")
            raise ValueError("order type is not supported by broker capabilities")
        if not capabilities.supports_tif(intent.order_spec.time_in_force):
            raise ValueError("time in force is not supported by broker capabilities")
        if (
            not capabilities.supports_fractional
            and intent.quantity != intent.quantity.to_integral_value()
        ):
            raise ValueError("fractional quantity is not supported")
        capabilities.validate_order_quantity(intent.quantity)

    @staticmethod
    def _resolve_bar_range(
        market_price: Decimal,
        bar_high: Decimal | None,
        bar_low: Decimal | None,
    ) -> tuple[Decimal, Decimal]:
        if bar_high is None and bar_low is None:
            return market_price, market_price
        if bar_high is None or bar_low is None:
            raise ValueError("bar_high and bar_low must be provided together")
        if bar_high < bar_low:
            raise ValueError("bar_high must be greater than or equal to bar_low")
        if market_price < bar_low or market_price > bar_high:
            raise ValueError("market_price must lie within the bar range")
        return bar_high, bar_low

    def _evaluate_fill(
        self,
        intent: OrderIntent,
        *,
        market_price: Decimal,
        bar_high: Decimal,
        bar_low: Decimal,
    ) -> _FillDecision:
        spec = intent.order_spec
        order_type = spec.order_type

        if order_type is OrderType.MARKET:
            return _FillDecision(triggered=True, fill_price=market_price)

        if order_type is OrderType.BRACKET:
            # Parent leg fills at market; OCO children are owned by OrderManager.
            return _FillDecision(triggered=True, fill_price=market_price)

        if order_type is OrderType.LIMIT:
            return self._evaluate_limit(intent, bar_high=bar_high, bar_low=bar_low)

        if order_type is OrderType.STOP:
            return self._evaluate_stop(intent, bar_high=bar_high, bar_low=bar_low)

        if order_type is OrderType.STOP_LIMIT:
            return self._evaluate_stop_limit(intent, bar_high=bar_high, bar_low=bar_low)

        raise NotImplementedError(
            f"simulated execution does not yet support {order_type.value} orders"
        )

    @staticmethod
    def _evaluate_limit(
        intent: OrderIntent,
        *,
        bar_high: Decimal,
        bar_low: Decimal,
    ) -> _FillDecision:
        limit_price = intent.order_spec.limit_price
        if limit_price is None:
            raise ValueError("LIMIT order requires limit_price")
        if intent.side is OrderSide.BUY:
            if bar_low <= limit_price:
                # Fill at the better of the limit price and the bar open proxy
                # (we treat bar_high as the worst-case fillable price when
                # the bar gapped through the limit).
                fill_price = min(limit_price, bar_high)
                return _FillDecision(triggered=True, fill_price=fill_price)
            return _FillDecision(triggered=False, fill_price=limit_price)
        if bar_high >= limit_price:
            fill_price = max(limit_price, bar_low)
            return _FillDecision(triggered=True, fill_price=fill_price)
        return _FillDecision(triggered=False, fill_price=limit_price)

    @staticmethod
    def _evaluate_stop(
        intent: OrderIntent,
        *,
        bar_high: Decimal,
        bar_low: Decimal,
    ) -> _FillDecision:
        stop_price = intent.order_spec.stop_price
        if stop_price is None:
            raise ValueError("STOP order requires stop_price")
        if intent.side is OrderSide.BUY:
            if bar_high >= stop_price:
                fill_price = max(stop_price, bar_low)
                return _FillDecision(triggered=True, fill_price=fill_price)
            return _FillDecision(triggered=False, fill_price=stop_price)
        if bar_low <= stop_price:
            fill_price = min(stop_price, bar_high)
            return _FillDecision(triggered=True, fill_price=fill_price)
        return _FillDecision(triggered=False, fill_price=stop_price)

    @staticmethod
    def _evaluate_stop_limit(
        intent: OrderIntent,
        *,
        bar_high: Decimal,
        bar_low: Decimal,
    ) -> _FillDecision:
        spec = intent.order_spec
        if spec.stop_price is None or spec.limit_price is None:
            raise ValueError("STOP_LIMIT order requires stop_price and limit_price")
        if intent.side is OrderSide.BUY:
            stop_triggered = bar_high >= spec.stop_price
            limit_marketable = stop_triggered and bar_low <= spec.limit_price
            if limit_marketable:
                fill_price = min(spec.limit_price, bar_high)
                return _FillDecision(triggered=True, fill_price=fill_price)
            return _FillDecision(triggered=False, fill_price=spec.limit_price)
        stop_triggered = bar_low <= spec.stop_price
        limit_marketable = stop_triggered and bar_high >= spec.limit_price
        if limit_marketable:
            fill_price = max(spec.limit_price, bar_low)
            return _FillDecision(triggered=True, fill_price=fill_price)
        return _FillDecision(triggered=False, fill_price=spec.limit_price)

    def _slippage_model_name(self) -> str:
        return "zero" if self.cost_model.slippage_bps == Decimal("0") else "basis_points"

    def _commission_model_name(self) -> str:
        if self.cost_model.fixed_commission_per_contract == Decimal("0"):
            return "zero"
        return "fixed_per_contract"


__all__ = ["SimulatedExecutionAdapter", "SimulatedExecutionCostModel"]
