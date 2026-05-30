"""Runtime target-intent processing."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol

from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.domain.market_data import Bar
from qts.domain.orders import (
    Order,
    OrderFill,
    OrderIntent,
    OrderSide,
    OrderSpec,
)
from qts.domain.risk import MarketDataRiskContext, OrderRiskRequest, RiskDecision
from qts.portfolio.holdings import Holding
from qts.risk.risk_engine import RiskEngine

if TYPE_CHECKING:
    from qts.risk.intraday_pnl import IntradayPnlCalculator
    from qts.risk.margin.calculator import MarginCalculator
    from qts.risk.risk_state import RiskStateSnapshot

from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountSnapshot, GetAccountSnapshot
from qts.runtime.actors.order_manager_actor import (
    GetFillCount,
    GetFillsSince,
    GetOrder,
    SubmitOrder,
)
from qts.runtime.order_route_metadata import OrderRouteMetadata
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
    risk_decisions: tuple[RiskDecision, ...] = ()


@dataclass(frozen=True, slots=True)
class OrderPlan:
    """One concrete order delta planned from a strategy target intent."""

    account_id: AccountId
    instrument_id: InstrumentId
    quantity_delta: Decimal
    market_price: Decimal
    order_time: datetime | None
    order_spec: OrderSpec
    aggregation_decision_id: str | None = None
    intent_id: str | None = None


class OrderPlanBuilder:
    """Convert target intents and positions into concrete order plans."""

    def __init__(self, *, instrument_context: InstrumentExecutionContext) -> None:
        """Create an order plan builder."""
        self._instrument_context = instrument_context

    def build(
        self,
        intent: TargetIntent,
        *,
        account_id: AccountId,
        bar: Bar,
        positions: Mapping[InstrumentId, Holding],
        aggregation_decision_id: str | None = None,
        account_equity: Decimal | None = None,
        multiplier: Decimal = Decimal("1"),
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
                            account_id=account_id,
                            instrument_id=instrument_id,
                            quantity_delta=-quantity,
                            market_price=self._instrument_context.market_price_for_intent(
                                intent,
                                instrument_id=instrument_id,
                                bar=bar,
                            ),
                            order_time=bar.end_time,
                            order_spec=intent.order_spec,
                            aggregation_decision_id=aggregation_decision_id,
                            intent_id=intent.intent_id,
                        )
                    )

        current_quantity = positions.get(
            target_instrument,
            Holding(
                instrument_id=target_instrument,
                quantity=Decimal("0"),
                average_cost=Decimal("0"),
                realized_pnl=Decimal("0"),
            ),
        ).quantity
        target_market_price = self._instrument_context.market_price_for_intent(
            intent,
            instrument_id=target_instrument,
            bar=bar,
        )
        desired_quantity = self._desired_quantity(
            intent,
            current_quantity=current_quantity,
            market_price=target_market_price,
            account_equity=account_equity,
            multiplier=multiplier,
        )
        quantity_delta = desired_quantity - current_quantity
        if quantity_delta != Decimal("0"):
            order_plans.append(
                OrderPlan(
                    account_id=account_id,
                    instrument_id=target_instrument,
                    quantity_delta=quantity_delta,
                    market_price=target_market_price,
                    order_time=bar.end_time,
                    order_spec=intent.order_spec,
                    aggregation_decision_id=aggregation_decision_id,
                    intent_id=intent.intent_id,
                )
            )

        return tuple(order_plans)

    @staticmethod
    def _desired_quantity(
        intent: TargetIntent,
        *,
        current_quantity: Decimal,
        market_price: Decimal,
        account_equity: Decimal | None = None,
        multiplier: Decimal = Decimal("1"),
    ) -> Decimal:
        """Return the desired quantity implied by a target intent."""
        if intent.intent_type is TargetIntentType.CLOSE:
            return Decimal("0")

        if intent.value is None:
            raise ValueError("target intent value is required")

        if intent.intent_type is TargetIntentType.QUANTITY:
            return intent.value
        if intent.intent_type is TargetIntentType.VALUE:
            return intent.value / market_price
        if intent.intent_type is TargetIntentType.PERCENT:
            if account_equity is None:
                raise ValueError("account_equity is required for PERCENT intent")
            if account_equity <= Decimal("0"):
                raise ValueError("account_equity must be positive for PERCENT intent")
            target_value = account_equity * intent.value
            return target_value / (market_price * multiplier)

        raise ValueError(f"unsupported target intent type: {intent.intent_type}")


class TargetIntentProcessor:
    """Translate strategy target intents into validated runtime order submissions."""

    def __init__(
        self,
        *,
        risk_engine: RiskEngine,
        instrument_context: InstrumentExecutionContext,
        multiplier_for: Callable[[InstrumentId], Decimal],
        broker_id: BrokerId,
        order_id_prefix: str = "bt",
        broker_order_id_prefix: str = "sim",
        margin_calculator: MarginCalculator | None = None,
        intraday_pnl_calculator: IntradayPnlCalculator | None = None,
    ) -> None:
        """Perform __init__."""
        if not order_id_prefix.strip():
            raise ValueError("order_id_prefix must not be empty")
        if not broker_order_id_prefix.strip():
            raise ValueError("broker_order_id_prefix must not be empty")
        self._risk_engine = risk_engine
        self._instrument_context = instrument_context
        self._order_plan_builder = OrderPlanBuilder(instrument_context=instrument_context)
        self._multiplier_for = multiplier_for
        self._broker_id = broker_id
        self._order_id_prefix = order_id_prefix
        self._broker_order_id_prefix = broker_order_id_prefix
        self._margin_calculator = margin_calculator
        self._intraday_pnl_calculator = intraday_pnl_calculator

    def process_intent(
        self,
        intent: TargetIntent,
        *,
        bar: Bar,
        account_ref: ActorRef,
        order_manager_ref: ActorRef,
        execution_ref: ActorRef,
        account_id: AccountId | None,
        strategy_id: StrategyId,
        correlation_id: CorrelationId,
        contributing_strategy_ids: tuple[StrategyId, ...] = (),
        aggregation_decision_id: str | None = None,
        conflict_reason: str | None = None,
        market_data_context: MarketDataRiskContext | None = None,
        order_number: int,
    ) -> ProcessedIntent:
        """Process a single target intent; account_id is required for routing."""
        if account_id is None:
            raise ValueError("account_id is required")

        snapshot: AccountSnapshot = account_ref.ask(GetAccountSnapshot())
        marks = self._build_mark_map(intent, bar=bar, positions=snapshot.positions)
        multipliers = {instr_id: self._multiplier_for(instr_id) for instr_id in snapshot.positions}

        # Deferred import to break circular dependency between qts.risk.risk_state
        # and qts.runtime.intent_processing.
        from qts.risk.risk_state import RiskStateSnapshot as _RiskStateSnapshot

        intraday_pnl = Decimal("0")
        if self._intraday_pnl_calculator is not None:
            intraday_pnl = self._intraday_pnl_calculator.compute(
                session_id=self._session_id_for(bar),
                holdings=snapshot.positions,
                marks=marks,
                multipliers=multipliers,
            )

        risk_state = _RiskStateSnapshot.from_account(
            snapshot,
            marks=marks,
            multipliers=multipliers,
            intraday_pnl=intraday_pnl,
            margin_calculator=self._margin_calculator,
        )
        account_equity = risk_state.account_equity
        multiplier = self._multiplier_for(
            self._instrument_context.order_instrument_for_intent(intent, bar=bar),
        )
        order_plans = self._order_plan_builder.build(
            intent,
            account_id=account_id,
            bar=bar,
            positions=snapshot.positions,
            aggregation_decision_id=aggregation_decision_id,
            account_equity=account_equity,
            multiplier=multiplier,
        )
        if not order_plans:
            return ProcessedIntent(orders=(), fills=())

        orders: list[Order] = []
        fills: list[OrderFill] = []
        risk_decisions: list[RiskDecision] = []
        for index, plan in enumerate(order_plans):
            processed = self._process_order_delta(
                instrument_id=plan.instrument_id,
                quantity_delta=plan.quantity_delta,
                market_price=plan.market_price,
                order_time=plan.order_time,
                order_spec=plan.order_spec,
                order_manager_ref=order_manager_ref,
                execution_ref=execution_ref,
                account_ref=account_ref,
                account_id=plan.account_id,
                strategy_id=strategy_id,
                correlation_id=correlation_id,
                contributing_strategy_ids=contributing_strategy_ids,
                aggregation_decision_id=plan.aggregation_decision_id,
                conflict_reason=conflict_reason,
                market_data_context=market_data_context,
                order_number=order_number + index,
                risk_state=risk_state,
                intent_id=plan.intent_id,
            )
            orders.extend(processed.orders)
            fills.extend(processed.fills)
            risk_decisions.extend(processed.risk_decisions)

        return ProcessedIntent(
            orders=tuple(orders),
            fills=tuple(fills),
            risk_decisions=tuple(risk_decisions),
        )

    def _build_mark_map(
        self,
        intent: TargetIntent,
        *,
        bar: Bar,
        positions: Mapping[InstrumentId, Holding],
    ) -> dict[InstrumentId, Decimal]:
        """Build a mark-price map from the current bar for all held instruments."""
        marks: dict[InstrumentId, Decimal] = {}
        target_instrument = self._instrument_context.order_instrument_for_intent(
            intent,
            bar=bar,
        )
        marks[target_instrument] = self._instrument_context.market_price_for_intent(
            intent,
            instrument_id=target_instrument,
            bar=bar,
        )
        for instrument_id in positions:
            if instrument_id not in marks:
                try:
                    marks[instrument_id] = self._instrument_context.market_price_for_intent(
                        intent,
                        instrument_id=instrument_id,
                        bar=bar,
                    )
                except (KeyError, ValueError):
                    pass
        return marks

    @staticmethod
    def _session_id_for(bar: Bar) -> str:
        """Return the intraday-session key for the bar.

        The key is the bar's exchange-local ``session_id`` (a domain fact),
        not a UTC calendar date. Overnight sessions (e.g. COMEX GC/SI
        ``[18:00 ET, 17:00 ET)``) span two UTC dates within a single session;
        deriving the key from ``end_time.astimezone(UTC).date()`` would reset
        the intraday-loss window mid-session. See
        ``docs/domain/market_calendar_and_sessions.md``.
        """
        return bar.session_id

    def _projected_initial_margin(
        self,
        *,
        current_position: Decimal,
        signed_quantity_delta: Decimal,
        market_price: Decimal,
        multiplier: Decimal,
    ) -> Decimal | None:
        """Return the incremental initial margin of an order's exposure-increasing part.

        Only the portion of the order that increases absolute exposure consumes
        new margin; risk-reducing orders return zero. None is returned when no
        margin calculator is configured (the margin rule, if enabled, then fails
        closed on the missing context).
        """
        if self._margin_calculator is None:
            return None
        new_position = current_position + signed_quantity_delta
        increasing_quantity = max(abs(new_position) - abs(current_position), Decimal("0"))
        if increasing_quantity == Decimal("0"):
            return Decimal("0")
        notional = increasing_quantity * market_price * multiplier
        return self._margin_calculator.order_initial_margin(notional)

    def _process_order_delta(
        self,
        *,
        instrument_id: InstrumentId,
        quantity_delta: Decimal,
        market_price: Decimal,
        order_time: datetime | None,
        order_spec: OrderSpec,
        order_manager_ref: ActorRef,
        execution_ref: ActorRef,
        account_ref: ActorRef,
        account_id: AccountId,
        strategy_id: StrategyId,
        correlation_id: CorrelationId,
        contributing_strategy_ids: tuple[StrategyId, ...] = (),
        aggregation_decision_id: str | None = None,
        conflict_reason: str | None = None,
        market_data_context: MarketDataRiskContext | None = None,
        order_number: int,
        risk_state: RiskStateSnapshot | None = None,
        intent_id: str | None = None,
    ) -> ProcessedIntent:
        """Perform _process_order_delta."""
        if quantity_delta == Decimal("0"):
            return ProcessedIntent(orders=(), fills=())

        side = OrderSide.BUY if quantity_delta > Decimal("0") else OrderSide.SELL
        quantity = abs(quantity_delta)
        risk_request = OrderRiskRequest(
            instrument_id=instrument_id,
            quantity=quantity,
            price=market_price,
            multiplier=self._multiplier_for(instrument_id),
            order_spec=order_spec,
            order_time=order_time,
            contributing_strategy_ids=contributing_strategy_ids,
            aggregation_decision_id=aggregation_decision_id,
            conflict_reason=conflict_reason,
            market_data=market_data_context,
        )
        if risk_state is not None:
            current_position = risk_state.current_position(instrument_id)
            risk_request = replace(
                risk_request,
                account_equity=risk_state.account_equity,
                current_exposure=risk_state.current_exposure,
                intraday_pnl=risk_state.intraday_pnl,
                current_notional_by_instrument=risk_state.current_notional_by_instrument,
                current_position=current_position,
                signed_quantity_delta=quantity_delta,
                current_margin_requirement=risk_state.current_margin_requirement,
                available_margin=risk_state.available_margin,
                projected_initial_margin=self._projected_initial_margin(
                    current_position=current_position,
                    signed_quantity_delta=quantity_delta,
                    market_price=market_price,
                    multiplier=self._multiplier_for(instrument_id),
                ),
            )
        risk_decision = self._risk_engine.check(risk_request)
        if (
            risk_decision.contributing_strategy_ids != contributing_strategy_ids
            or risk_decision.aggregation_decision_id != aggregation_decision_id
            or risk_decision.conflict_reason != conflict_reason
        ):
            risk_decision = replace(
                risk_decision,
                contributing_strategy_ids=contributing_strategy_ids,
                aggregation_decision_id=aggregation_decision_id,
                conflict_reason=conflict_reason,
            )

        if not risk_decision.approved:
            return ProcessedIntent(orders=(), fills=(), risk_decisions=(risk_decision,))

        before_fill_count: int = order_manager_ref.ask(GetFillCount())
        order_id = OrderId(f"{self._order_id_prefix}-{order_number:06d}")
        client_order_id = f"{self._order_id_prefix}-client-{order_number:06d}"
        order_intent = OrderIntent(
            order_id=order_id,
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
            account_id=account_id,
            order_spec=order_spec,
            intent_id=intent_id,
        )
        route_metadata = OrderRouteMetadata(
            broker_id=self._broker_id,
            account_id=account_id,
            strategy_id=strategy_id,
            client_order_id=client_order_id,
            correlation_id=correlation_id,
            contributing_strategy_ids=contributing_strategy_ids,
            aggregation_decision_id=aggregation_decision_id,
        )
        order_manager_ref.tell(
            SubmitOrder(
                intent=order_intent,
                risk_decision=risk_decision,
                broker_order_id=f"{self._broker_order_id_prefix}-{order_number:06d}",
                market_price=market_price,
                account_id=account_id,
                strategy_id=strategy_id,
                route_metadata=route_metadata,
                bar_time=order_time,
            )
        )
        order_manager_ref.process_all()
        execution_ref.process_all()
        order_manager_ref.process_all()
        account_ref.process_all()

        fills: tuple[OrderFill, ...] = order_manager_ref.ask(GetFillsSince(index=before_fill_count))
        if not fills:
            return ProcessedIntent(
                orders=(order_manager_ref.ask(GetOrder(order_id=order_id)),),
                fills=(),
                risk_decisions=(risk_decision,),
            )

        return ProcessedIntent(
            orders=(order_manager_ref.ask(GetOrder(order_id=order_id)),),
            fills=fills,
            risk_decisions=(risk_decision,),
        )


__all__ = [
    "InstrumentExecutionContext",
    "OrderPlan",
    "OrderPlanBuilder",
    "ProcessedIntent",
    "TargetIntentProcessor",
]
