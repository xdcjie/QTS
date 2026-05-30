"""Strategy actor boundary."""

from __future__ import annotations

from dataclasses import dataclass

from qts.domain.market_data import Bar
from qts.domain.orders import CancelIntent, OrderFill
from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorUnhandledMessageError
from qts.runtime.actor_ref import ActorRef
from qts.strategy_sdk import DataView, PortfolioView, Strategy, StrategyContext, TargetIntent
from qts.strategy_sdk.events import Fill, TimerScheduler


@dataclass(frozen=True, slots=True)
class StrategyBarEvent:
    """Completed strategy-facing bar delivered to a strategy actor."""

    bar: Bar
    data: DataView
    portfolio: PortfolioView


@dataclass(frozen=True, slots=True)
class StrategyBarResult:
    """New strategy intents and cancel intents emitted while handling one bar."""

    bar: Bar
    intents: tuple[TargetIntent, ...]
    cancel_intents: tuple[CancelIntent, ...] = ()


@dataclass(frozen=True, slots=True)
class StrategyFillEvent:
    """Validated fills delivered to a strategy actor for ``on_fill`` dispatch."""

    fills: tuple[OrderFill, ...]


@dataclass(frozen=True, slots=True)
class StrategyFinalize:
    """Request strategy finalization."""


@dataclass(frozen=True, slots=True)
class StrategyFinalized:
    """Strategy finalization completed."""

    intents: tuple[TargetIntent, ...]
    cancel_intents: tuple[CancelIntent, ...] = ()


class StrategyActor(Actor):
    """Actor-owned strategy instance and user-facing context."""

    def __init__(
        self,
        *,
        strategy: Strategy,
        context: StrategyContext,
        result_ref: ActorRef,
    ) -> None:
        """Initialize the strategy, context, and timer scheduler, then run initialize()."""
        self._strategy = strategy
        self._context = context
        self._result_ref = result_ref
        self._strategy.initialize(self._context)
        self._timer_scheduler = TimerScheduler()
        for subscription in self._context.timer_subscriptions:
            self._timer_scheduler.register(subscription)

    def handle(self, message: object) -> None:
        """Dispatch bar, fill, and finalize messages to their handlers."""
        if isinstance(message, StrategyBarEvent):
            self._handle_bar(message)
            return
        if isinstance(message, StrategyFillEvent):
            self._handle_fills(message)
            return
        if isinstance(message, StrategyFinalize):
            self._handle_finalize()
            return
        raise ActorUnhandledMessageError(f"unsupported strategy message: {type(message).__name__}")

    def _handle_bar(self, message: StrategyBarEvent) -> None:
        """Fire due timers, run on_bar, and return new intents and cancel intents."""
        self._context.data = message.data
        self._context.portfolio = message.portfolio
        self._context.indicator.update_from_bar(message.bar)
        before_intents = len(self._context.intents)
        before_cancels = len(self._context.cancel_intents)
        for timer in self._timer_scheduler.due(message.bar.end_time):
            self._strategy.on_timer(self._context, timer)
        self._strategy.on_bar(self._context, message.bar)
        self._result_ref.tell(
            StrategyBarResult(
                bar=message.bar,
                intents=self._context.intents[before_intents:],
                cancel_intents=self._context.cancel_intents[before_cancels:],
            )
        )

    def _handle_fills(self, message: StrategyFillEvent) -> None:
        """Deliver validated fills to the strategy as SDK fill events."""
        for order_fill in message.fills:
            self._strategy.on_fill(self._context, _to_sdk_fill(order_fill))

    def _handle_finalize(self) -> None:
        """Run strategy finalize() and emit the resulting intents and cancel intents."""
        before_intents = len(self._context.intents)
        before_cancels = len(self._context.cancel_intents)
        self._strategy.finalize(self._context)
        self._result_ref.tell(
            StrategyFinalized(
                intents=self._context.intents[before_intents:],
                cancel_intents=self._context.cancel_intents[before_cancels:],
            )
        )


def _to_sdk_fill(order_fill: OrderFill) -> Fill:
    """Convert an OrderManager-validated fill into a strategy-facing fill."""
    return Fill(
        fill_id=order_fill.fill_id,
        order_id=order_fill.order_id,
        instrument_id=order_fill.instrument_id,
        side=order_fill.side,
        quantity=order_fill.quantity,
        price=order_fill.price,
        commission=order_fill.commission,
        slippage=order_fill.slippage,
        account_id=order_fill.account_id,
        intent_id=order_fill.intent_id,
    )


__all__ = [
    "StrategyActor",
    "StrategyBarEvent",
    "StrategyBarResult",
    "StrategyFillEvent",
    "StrategyFinalize",
    "StrategyFinalized",
]
