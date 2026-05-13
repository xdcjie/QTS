"""Backtest intent processing."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from qts.core.ids import InstrumentId, OrderId
from qts.domain.market_data import Bar
from qts.domain.risk import OrderRiskRequest
from qts.execution.order_manager import Order, OrderFill, OrderIntent, OrderSide
from qts.portfolio.position_book import Position
from qts.risk.risk_engine import RiskEngine
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor
from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
from qts.strategy_sdk import TargetIntent
from qts.strategy_sdk.target import TargetIntentType


class InstrumentExecutionContext(Protocol):
    """Instrument resolution required to turn target intents into order plans."""

    def order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId:
        """Return the concrete instrument to order for a target intent."""
        ...

    def market_price_for_intent(
        self,
        intent: TargetIntent,
        *,
        instrument_id: InstrumentId,
        bar: Bar,
    ) -> Decimal:
        """Return the execution price for a planned order."""
        ...

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        """Return whether an instrument ID represents a continuous instrument."""
        ...

    def related_contracts_for(
        self, continuous_instrument_id: InstrumentId
    ) -> frozenset[InstrumentId]:
        """Return concrete contracts related to a continuous instrument."""
        ...


@dataclass(frozen=True, slots=True)
class ProcessedIntent:
    """Orders and fills generated for a single strategy intent."""

    orders: tuple[Order, ...]
    fills: tuple[OrderFill, ...]


@dataclass(frozen=True, slots=True)
class OrderPlan:
    """One concrete order delta planned from a strategy target intent."""

    instrument_id: InstrumentId
    quantity_delta: Decimal
    market_price: Decimal
    order_time: datetime | None


class OrderPlanBuilder:
    """Convert target intents and positions into concrete order plans."""

    def __init__(self, *, instrument_context: InstrumentExecutionContext) -> None:
        """Create an order plan builder."""
        self._instrument_context = instrument_context

    def build(
        self,
        intent: TargetIntent,
        *,
        bar: Bar,
        positions: Mapping[InstrumentId, Position],
    ) -> tuple[OrderPlan, ...]:
        """Build concrete order plans for a target intent."""
        target_instrument = self._instrument_context.order_instrument_for_intent(
            intent,
            bar=bar,
        )
        order_plans: list[OrderPlan] = []

        if self._instrument_context.is_continuous(intent.asset.instrument_id):
            related_contracts = self._instrument_context.related_contracts_for(
                intent.asset.instrument_id
            )
            for instrument_id, position in positions.items():
                if instrument_id == target_instrument:
                    continue
                if instrument_id not in related_contracts:
                    continue
                quantity = position.quantity
                if quantity != Decimal("0"):
                    order_plans.append(
                        OrderPlan(
                            instrument_id=instrument_id,
                            quantity_delta=-quantity,
                            market_price=self._instrument_context.market_price_for_intent(
                                intent,
                                instrument_id=instrument_id,
                                bar=bar,
                            ),
                            order_time=bar.end_time,
                        )
                    )

        current_quantity = positions.get(
            target_instrument,
            Position(instrument_id=target_instrument, quantity=Decimal("0")),
        ).quantity
        desired_quantity = self._desired_quantity(
            intent,
            current_quantity=current_quantity,
            bar=bar,
        )
        quantity_delta = desired_quantity - current_quantity
        if quantity_delta != Decimal("0"):
            order_plans.append(
                OrderPlan(
                    instrument_id=target_instrument,
                    quantity_delta=quantity_delta,
                    market_price=self._instrument_context.market_price_for_intent(
                        intent,
                        instrument_id=target_instrument,
                        bar=bar,
                    ),
                    order_time=bar.end_time,
                )
            )

        return tuple(order_plans)

    @staticmethod
    def _desired_quantity(
        intent: TargetIntent,
        *,
        current_quantity: Decimal,
        bar: Bar,
    ) -> Decimal:
        """Return the desired quantity implied by a target intent."""
        if intent.intent_type is TargetIntentType.CLOSE:
            return Decimal("0")

        if intent.value is None:
            raise ValueError("target intent value is required")

        if intent.intent_type is TargetIntentType.QUANTITY:
            return intent.value
        if intent.intent_type is TargetIntentType.VALUE:
            return intent.value / bar.close
        if intent.intent_type is TargetIntentType.PERCENT:
            current_value = current_quantity * bar.close
            target_value = max(current_value, bar.close) * intent.value
            return target_value / bar.close

        raise ValueError(f"unsupported target intent type: {intent.intent_type}")


class TargetIntentProcessor:
    """Translate strategy target intents into validated, executed backtest orders."""

    def __init__(
        self,
        *,
        risk_engine: RiskEngine,
        instrument_context: InstrumentExecutionContext,
        multiplier_for: Callable[[InstrumentId], Decimal],
        order_id_prefix: str = "bt",
        broker_order_id_prefix: str = "sim",
    ) -> None:
        """Perform __init__."""
        if not order_id_prefix.strip():
            raise ValueError("order_id_prefix must not be empty")
        if not broker_order_id_prefix.strip():
            raise ValueError("broker_order_id_prefix must not be empty")
        self._risk_engine = risk_engine
        self._order_plan_builder = OrderPlanBuilder(instrument_context=instrument_context)
        self._multiplier_for = multiplier_for
        self._order_id_prefix = order_id_prefix
        self._broker_order_id_prefix = broker_order_id_prefix

    def process_intent(
        self,
        intent: TargetIntent,
        *,
        bar: Bar,
        account_actor: AccountActor,
        order_manager_actor: OrderManagerActor,
        order_manager_ref: ActorRef,
        execution_ref: ActorRef,
        account_ref: ActorRef,
        order_number: int,
    ) -> ProcessedIntent:
        """Process a single target intent and return produced orders/fills."""

        snapshot = account_actor.snapshot()
        order_plans = self._order_plan_builder.build(
            intent,
            bar=bar,
            positions=snapshot.positions,
        )
        if not order_plans:
            return ProcessedIntent(orders=(), fills=())

        orders: list[Order] = []
        fills: list[OrderFill] = []
        for index, plan in enumerate(order_plans):
            processed = self._process_order_delta(
                instrument_id=plan.instrument_id,
                quantity_delta=plan.quantity_delta,
                market_price=plan.market_price,
                order_time=plan.order_time,
                order_manager_actor=order_manager_actor,
                order_manager_ref=order_manager_ref,
                execution_ref=execution_ref,
                account_ref=account_ref,
                order_number=order_number + index,
            )
            orders.extend(processed.orders)
            fills.extend(processed.fills)

        return ProcessedIntent(orders=tuple(orders), fills=tuple(fills))

    def _process_order_delta(
        self,
        *,
        instrument_id: InstrumentId,
        quantity_delta: Decimal,
        market_price: Decimal,
        order_time: datetime | None,
        order_manager_actor: OrderManagerActor,
        order_manager_ref: ActorRef,
        execution_ref: ActorRef,
        account_ref: ActorRef,
        order_number: int,
    ) -> ProcessedIntent:
        """Perform _process_order_delta."""
        if quantity_delta == Decimal("0"):
            return ProcessedIntent(orders=(), fills=())

        side = OrderSide.BUY if quantity_delta > Decimal("0") else OrderSide.SELL
        quantity = abs(quantity_delta)
        risk_decision = self._risk_engine.check(
            OrderRiskRequest(
                instrument_id=instrument_id,
                quantity=quantity,
                price=market_price,
                multiplier=self._multiplier_for(instrument_id),
                order_time=order_time,
            )
        )

        if not risk_decision.approved:
            return ProcessedIntent(orders=(), fills=())

        before_fill_count = order_manager_actor.fill_count
        order_id = OrderId(f"{self._order_id_prefix}-{order_number:06d}")
        order_intent = OrderIntent(
            order_id=order_id,
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
        )
        order_manager_ref.tell(
            SubmitOrder(
                intent=order_intent,
                risk_decision=risk_decision,
                broker_order_id=f"{self._broker_order_id_prefix}-{order_number:06d}",
                market_price=market_price,
            )
        )
        order_manager_ref.process_all()
        execution_ref.process_all()
        order_manager_ref.process_all()
        account_ref.process_all()

        fills = order_manager_actor.fills_since(before_fill_count)
        if not fills:
            return ProcessedIntent(orders=(order_manager_actor.get_order(order_id),), fills=())

        return ProcessedIntent(
            orders=(order_manager_actor.get_order(order_id),),
            fills=fills,
        )


__all__ = [
    "InstrumentExecutionContext",
    "OrderPlan",
    "OrderPlanBuilder",
    "ProcessedIntent",
    "TargetIntentProcessor",
]
