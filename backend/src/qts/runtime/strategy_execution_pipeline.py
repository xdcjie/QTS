"""Shared strategy execution pipeline."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.actors.signal_aggregator_actor import (
    AggregatedSignalBatch,
    SignalAggregatorActor,
    StrategySignalEvent,
)
from qts.runtime.actors.strategy_actor import (
    StrategyActor,
    StrategyBarEvent,
    StrategyBarResult,
    StrategyFinalize,
    StrategyFinalized,
)
from qts.runtime.mailbox import Mailbox
from qts.strategy_sdk import PortfolioView, Strategy, StrategyContext, TargetIntent
from qts.strategy_sdk.data_view import DataView

PortfolioViewBuilder = Callable[..., PortfolioView]


@dataclass(frozen=True, slots=True)
class StrategyExecutionResult:
    """Strategy intents emitted for one strategy-facing bar."""

    bar: Bar
    intents: tuple[TargetIntent, ...]


class StrategyExecutionPipeline:
    """Run strategy actors and signal aggregation for strategy-facing bars."""

    def __init__(
        self,
        *,
        strategy: Strategy,
        instrument_registry: InstrumentRegistry | None,
        future_chain_registry: FutureRollRegistry | None,
        portfolio_view: PortfolioViewBuilder,
        prune_history: bool,
        strategy_actor_type: type = StrategyActor,
        signal_aggregator_actor_type: type = SignalAggregatorActor,
    ) -> None:
        """Create a mode-agnostic strategy execution pipeline."""
        self._portfolio_view = portfolio_view
        self._strategy_bars_by_instrument: dict[InstrumentId, list[Bar]] = defaultdict(list)
        self._ctx = StrategyContext(
            instrument_registry=instrument_registry,
            future_chain_registry=future_chain_registry,
        )
        self._strategy_result_mailbox = Mailbox()
        self._strategy_ref = ActorRef(
            actor=strategy_actor_type(
                strategy=strategy,
                context=self._ctx,
                result_ref=ActorRef(mailbox=self._strategy_result_mailbox),
            ),
            mailbox=Mailbox(),
        )
        self._signal_result_mailbox = Mailbox()
        self._signal_ref = ActorRef(
            actor=signal_aggregator_actor_type(
                result_ref=ActorRef(mailbox=self._signal_result_mailbox)
            ),
            mailbox=Mailbox(),
        )
        self._history_limit = self._history_limit_from_subscriptions() if prune_history else None

    def execute_bar(
        self,
        bar: Bar,
        *,
        account_snapshot: AccountSnapshot | object,
        latest_prices: Mapping[InstrumentId, Decimal],
        aggregate_signals: bool,
    ) -> StrategyExecutionResult:
        """Execute strategy logic for one completed strategy-facing bar."""
        history = self._strategy_bars_by_instrument[bar.instrument_id]
        history.append(bar)
        if self._history_limit is not None and len(history) > self._history_limit:
            del history[: len(history) - self._history_limit]
        self._strategy_ref.tell(
            StrategyBarEvent(
                bar=bar,
                data=DataView(
                    bars=self._strategy_bars_by_instrument,
                    as_of=bar.end_time,
                ),
                portfolio=self._portfolio_view(
                    account_snapshot,
                    latest_prices=latest_prices,
                ),
            )
        )
        self._strategy_ref.process_all()
        strategy_result = self._take_strategy_bar_result()
        if not aggregate_signals:
            return StrategyExecutionResult(bar=bar, intents=())

        self._signal_ref.tell(
            StrategySignalEvent(
                bar=bar,
                intents=strategy_result.intents,
            )
        )
        self._signal_ref.process_all()
        signal_batch = self._take_signal_batch()
        return StrategyExecutionResult(bar=bar, intents=signal_batch.intents)

    def finalize(self) -> tuple[TargetIntent, ...]:
        """Finalize the strategy and return finalization intents."""
        self._strategy_ref.tell(StrategyFinalize())
        self._strategy_ref.process_all()
        return self._take_strategy_finalized().intents

    def _history_limit_from_subscriptions(self) -> int | None:
        """Return the maximum requested subscription warmup."""
        if not self._ctx.subscriptions:
            return None
        return max(subscription.warmup for subscription in self._ctx.subscriptions)

    def _take_strategy_bar_result(self) -> StrategyBarResult:
        """Return the single strategy actor result for one bar."""
        if self._strategy_result_mailbox.empty():
            raise RuntimeError("strategy actor did not emit a bar result")
        result = self._strategy_result_mailbox.get()
        if not isinstance(result, StrategyBarResult):
            raise TypeError(f"unexpected strategy actor result: {type(result).__name__}")
        if not self._strategy_result_mailbox.empty():
            raise RuntimeError("strategy actor emitted more than one bar result")
        return result

    def _take_signal_batch(self) -> AggregatedSignalBatch:
        """Return the single signal aggregation result for one bar."""
        if self._signal_result_mailbox.empty():
            raise RuntimeError("signal aggregator actor did not emit a batch")
        result = self._signal_result_mailbox.get()
        if not isinstance(result, AggregatedSignalBatch):
            raise TypeError(f"unexpected signal aggregator result: {type(result).__name__}")
        if not self._signal_result_mailbox.empty():
            raise RuntimeError("signal aggregator actor emitted more than one batch")
        return result

    def _take_strategy_finalized(self) -> StrategyFinalized:
        """Return the single strategy finalization result."""
        if self._strategy_result_mailbox.empty():
            raise RuntimeError("strategy actor did not emit finalization result")
        result = self._strategy_result_mailbox.get()
        if not isinstance(result, StrategyFinalized):
            raise TypeError(f"unexpected strategy actor result: {type(result).__name__}")
        if not self._strategy_result_mailbox.empty():
            raise RuntimeError("strategy actor emitted more than one finalization result")
        return result


__all__ = ["StrategyExecutionPipeline", "StrategyExecutionResult"]
