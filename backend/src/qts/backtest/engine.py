"""Backtest engine MVP."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from qts.backtest.historical_data_portal import HistoricalDataPortal
from qts.backtest.replay_clock import ReplayClock
from qts.core.ids import InstrumentId, OrderId
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.domain.risk import OrderRiskRequest
from qts.execution.order_manager import Order, OrderIntent, OrderSide
from qts.portfolio.position_book import Position
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor, AccountSnapshot
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
from qts.runtime.mailbox import Mailbox
from qts.strategy_sdk import (
    PortfolioPosition,
    PortfolioView,
    Strategy,
    StrategyContext,
    TargetIntent,
)
from qts.strategy_sdk.target import TargetIntentType


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Backtest run result."""

    processed_bars: int
    final_account: AccountSnapshot
    orders: tuple[Order, ...]


class BacktestEngine:
    """Minimal single-process backtest engine using runtime actor flow."""

    def __init__(
        self,
        *,
        strategy: Strategy,
        bars: Iterable[Bar],
        initial_cash: Decimal,
        risk_engine: RiskEngine | None = None,
    ) -> None:
        self._strategy = strategy
        self._bars = tuple(sorted(bars, key=lambda bar: bar.end_time))
        self._initial_cash = initial_cash
        self._risk_engine = risk_engine or RiskEngine(
            [MaxNotionalRule(max_notional=initial_cash * Decimal("100"))]
        )

    def run(self) -> BacktestResult:
        bars_by_instrument: dict[InstrumentId, list[Bar]] = defaultdict(list)
        for bar in self._bars:
            bars_by_instrument[bar.instrument_id].append(bar)
        portal = HistoricalDataPortal(bars_by_instrument)
        clock = ReplayClock(bar.end_time for bar in self._bars)
        instrument_registry = _instrument_registry_for(self._bars)

        account_actor = AccountActor(initial_cash={"USD": self._initial_cash})
        account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
        execution_mailbox = Mailbox()
        order_manager_mailbox = Mailbox()
        order_manager_actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=execution_mailbox),
            account_ref=account_ref,
        )
        order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
        execution_ref = ActorRef(
            actor=ExecutionActor(order_manager_ref=order_manager_ref),
            mailbox=execution_mailbox,
        )

        ctx = StrategyContext(instrument_registry=instrument_registry)
        self._strategy.initialize(ctx)

        orders: list[Order] = []
        processed = 0
        for bar in self._bars:
            timestamp = clock.advance()
            if timestamp is None:
                break
            ctx.data = portal.data_view(as_of=timestamp)
            ctx.portfolio = _portfolio_view(account_actor.snapshot(), latest_bar=bar)
            before_count = len(ctx.intents)
            self._strategy.on_bar(ctx, bar)
            for intent in ctx.intents[before_count:]:
                order = _process_intent(
                    intent,
                    bar=bar,
                    account_actor=account_actor,
                    order_manager_actor=order_manager_actor,
                    order_manager_ref=order_manager_ref,
                    execution_ref=execution_ref,
                    account_ref=account_ref,
                    risk_engine=self._risk_engine,
                    order_number=len(orders) + 1,
                )
                if order is not None:
                    orders.append(order)
            processed += 1

        return BacktestResult(
            processed_bars=processed,
            final_account=account_actor.snapshot(),
            orders=tuple(orders),
        )


def _process_intent(
    intent: TargetIntent,
    *,
    bar: Bar,
    account_actor: AccountActor,
    order_manager_actor: OrderManagerActor,
    order_manager_ref: ActorRef,
    execution_ref: ActorRef,
    account_ref: ActorRef,
    risk_engine: RiskEngine,
    order_number: int,
) -> Order | None:
    current_quantity = (
        account_actor.snapshot()
        .positions.get(
            intent.asset.instrument_id,
            Position(instrument_id=intent.asset.instrument_id, quantity=Decimal("0")),
        )
        .quantity
    )
    desired_quantity = _desired_quantity(intent, current_quantity=current_quantity, bar=bar)
    quantity_delta = desired_quantity - current_quantity
    if quantity_delta == Decimal("0"):
        return None

    side = OrderSide.BUY if quantity_delta > Decimal("0") else OrderSide.SELL
    quantity = abs(quantity_delta)
    risk_decision = risk_engine.check(
        OrderRiskRequest(
            instrument_id=intent.asset.instrument_id,
            quantity=quantity,
            price=bar.close,
            multiplier=Decimal("1"),
        )
    )
    if not risk_decision.approved:
        return None

    order_id = OrderId(f"bt-{order_number:06d}")
    order_intent = OrderIntent(
        order_id=order_id,
        instrument_id=intent.asset.instrument_id,
        side=side,
        quantity=quantity,
    )
    order_manager_ref.tell(
        SubmitOrder(
            intent=order_intent,
            risk_decision=risk_decision,
            broker_order_id=f"sim-{order_number:06d}",
            market_price=bar.close,
        )
    )
    order_manager_ref.process_all()
    execution_ref.process_all()
    order_manager_ref.process_all()
    account_ref.process_all()
    return order_manager_actor.get_order(order_id)


def _desired_quantity(intent: TargetIntent, *, current_quantity: Decimal, bar: Bar) -> Decimal:
    if intent.intent_type is TargetIntentType.CLOSE:
        return Decimal("0")
    if intent.value is None:
        raise ValueError("target intent value is required")
    if intent.intent_type is TargetIntentType.QUANTITY:
        return intent.value
    if intent.intent_type is TargetIntentType.VALUE:
        return intent.value / bar.close
    if intent.intent_type is TargetIntentType.PERCENT:
        # MVP: percent target uses the current bar notional proxy for the asset.
        current_value = current_quantity * bar.close
        target_value = max(current_value, bar.close) * intent.value
        return target_value / bar.close
    raise ValueError(f"unsupported target intent type: {intent.intent_type}")


def _portfolio_view(snapshot: AccountSnapshot, *, latest_bar: Bar) -> PortfolioView:
    positions = {
        instrument_id: PortfolioPosition(
            quantity=position.quantity,
            market_value=position.quantity * latest_bar.close,
        )
        for instrument_id, position in snapshot.positions.items()
    }
    cash = snapshot.cash["USD"]
    equity = cash + sum((position.market_value for position in positions.values()), Decimal("0"))
    return PortfolioView(cash=cash, equity=equity, positions=positions)


def _instrument_registry_for(bars: Iterable[Bar]) -> InstrumentRegistry:
    registry = InstrumentRegistry()
    seen: set[InstrumentId] = set()
    for bar in bars:
        if bar.instrument_id in seen:
            continue
        seen.add(bar.instrument_id)
        symbol = _symbol_for(bar.instrument_id)
        registry.register(
            symbol,
            Instrument(
                instrument_id=bar.instrument_id,
                asset_class=AssetClass.EQUITY,
                exchange="BACKTEST",
                currency="USD",
                contract_spec=ContractSpec(
                    tick_size=Decimal("0.01"),
                    lot_size=Decimal("1"),
                    multiplier=Decimal("1"),
                    settlement=SettlementType.CASH,
                    calendar_id="BACKTEST",
                ),
            ),
        )
    return registry


def _symbol_for(instrument_id: InstrumentId) -> str:
    return instrument_id.value.rsplit(".", maxsplit=1)[-1]


__all__ = ["BacktestEngine", "BacktestResult"]
