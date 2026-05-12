"""Backtest intent processing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.backtest.instrument_context import BacktestInstrumentContext
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


@dataclass(frozen=True, slots=True)
class BacktestProcessedIntent:
    """Orders and fills generated for a single strategy intent."""

    orders: tuple[Order, ...]
    fills: tuple[OrderFill, ...]


class BacktestIntentProcessor:
    """Translate strategy target intents into validated, executed backtest orders."""

    def __init__(
        self,
        *,
        risk_engine: RiskEngine,
        instrument_context: BacktestInstrumentContext,
        multiplier_for: Callable[[InstrumentId], Decimal],
    ) -> None:
        """Perform __init__."""
        self._risk_engine = risk_engine
        self._instrument_context = instrument_context
        self._multiplier_for = multiplier_for

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
    ) -> BacktestProcessedIntent:
        """Process a single target intent and return produced orders/fills."""

        snapshot = account_actor.snapshot()
        target_instrument = self._instrument_context.order_instrument_for_intent(
            intent,
            bar=bar,
        )
        order_requests: list[tuple[InstrumentId, Decimal, Decimal]] = []

        if self._instrument_context.is_continuous(intent.asset.instrument_id):
            related_contracts = self._instrument_context.related_contracts_for(
                intent.asset.instrument_id
            )
            for instrument_id, position in snapshot.positions.items():
                if instrument_id == target_instrument:
                    continue
                if instrument_id not in related_contracts:
                    continue
                quantity = position.quantity
                if quantity != Decimal("0"):
                    order_requests.append(
                        (
                            instrument_id,
                            -quantity,
                            self._instrument_context.market_price_for_intent(
                                intent,
                                instrument_id=instrument_id,
                                bar=bar,
                            ),
                        )
                    )

        current_quantity = snapshot.positions.get(
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
            order_requests.append(
                (
                    target_instrument,
                    quantity_delta,
                    self._instrument_context.market_price_for_intent(
                        intent,
                        instrument_id=target_instrument,
                        bar=bar,
                    ),
                )
            )

        if not order_requests:
            return BacktestProcessedIntent(orders=(), fills=())

        orders: list[Order] = []
        fills: list[OrderFill] = []
        for index, (instrument_id, quantity_delta, market_price) in enumerate(order_requests):
            processed = self._process_order_delta(
                instrument_id=instrument_id,
                quantity_delta=quantity_delta,
                market_price=market_price,
                order_time=bar.end_time,
                order_manager_actor=order_manager_actor,
                order_manager_ref=order_manager_ref,
                execution_ref=execution_ref,
                account_ref=account_ref,
                order_number=order_number + index,
            )
            orders.extend(processed.orders)
            fills.extend(processed.fills)

        return BacktestProcessedIntent(orders=tuple(orders), fills=tuple(fills))

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
    ) -> BacktestProcessedIntent:
        """Perform _process_order_delta."""
        if quantity_delta == Decimal("0"):
            return BacktestProcessedIntent(orders=(), fills=())

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
            return BacktestProcessedIntent(orders=(), fills=())

        before_fill_count = order_manager_actor.fill_count
        order_id = OrderId(f"bt-{order_number:06d}")
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
                broker_order_id=f"sim-{order_number:06d}",
                market_price=market_price,
            )
        )
        order_manager_ref.process_all()
        execution_ref.process_all()
        order_manager_ref.process_all()
        account_ref.process_all()

        fills = order_manager_actor.fills_since(before_fill_count)
        if not fills:
            return BacktestProcessedIntent(
                orders=(order_manager_actor.get_order(order_id),), fills=()
            )

        return BacktestProcessedIntent(
            orders=(order_manager_actor.get_order(order_id),),
            fills=fills,
        )

    @staticmethod
    def _desired_quantity(
        intent: TargetIntent,
        *,
        current_quantity: Decimal,
        bar: Bar,
    ) -> Decimal:
        """Perform _desired_quantity."""
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


__all__ = ["BacktestIntentProcessor", "BacktestProcessedIntent"]
