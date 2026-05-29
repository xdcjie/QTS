"""Strategy actor boundary."""

from __future__ import annotations

from dataclasses import dataclass

from qts.domain.market_data import Bar
from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorUnhandledMessageError
from qts.runtime.actor_ref import ActorRef
from qts.strategy_sdk import DataView, PortfolioView, Strategy, StrategyContext, TargetIntent


@dataclass(frozen=True, slots=True)
class StrategyBarEvent:
    """Completed strategy-facing bar delivered to a strategy actor."""

    bar: Bar
    data: DataView
    portfolio: PortfolioView


@dataclass(frozen=True, slots=True)
class StrategyBarResult:
    """New strategy intents emitted while handling one bar."""

    bar: Bar
    intents: tuple[TargetIntent, ...]


@dataclass(frozen=True, slots=True)
class StrategyFinalize:
    """Request strategy finalization."""


@dataclass(frozen=True, slots=True)
class StrategyFinalized:
    """Strategy finalization completed."""

    intents: tuple[TargetIntent, ...]


class StrategyActor(Actor):
    """Actor-owned strategy instance and user-facing context."""

    def __init__(
        self,
        *,
        strategy: Strategy,
        context: StrategyContext,
        result_ref: ActorRef,
    ) -> None:
        """Perform __init__."""
        self._strategy = strategy
        self._context = context
        self._result_ref = result_ref
        self._strategy.initialize(self._context)

    def handle(self, message: object) -> None:
        """Perform handle."""
        if isinstance(message, StrategyBarEvent):
            self._handle_bar(message)
            return
        if isinstance(message, StrategyFinalize):
            self._handle_finalize()
            return
        raise ActorUnhandledMessageError(f"unsupported strategy message: {type(message).__name__}")

    def _handle_bar(self, message: StrategyBarEvent) -> None:
        """Perform _handle_bar."""
        self._context.data = message.data
        self._context.portfolio = message.portfolio
        self._context.indicator.update_from_bar(message.bar)
        before_count = len(self._context.intents)
        self._strategy.on_bar(self._context, message.bar)
        self._result_ref.tell(
            StrategyBarResult(
                bar=message.bar,
                intents=self._context.intents[before_count:],
            )
        )

    def _handle_finalize(self) -> None:
        """Perform _handle_finalize."""
        before_count = len(self._context.intents)
        self._strategy.finalize(self._context)
        self._result_ref.tell(StrategyFinalized(intents=self._context.intents[before_count:]))


__all__ = [
    "StrategyActor",
    "StrategyBarEvent",
    "StrategyBarResult",
    "StrategyFinalize",
    "StrategyFinalized",
]
