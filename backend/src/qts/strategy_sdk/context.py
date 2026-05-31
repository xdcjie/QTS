"""User-facing StrategyContext compatibility facade.

QTS-FINAL-005: StrategyContext no longer owns SDK state directly. It holds focused
subcontexts (asset, target, subscription, signal, timer, universe, portfolio) plus
the indicator/factor factories, and delegates every operation to them. Per-event
emissions live in ``TargetContext`` / ``SignalContext`` with bounded, drainable
buffers; ``StrategyActor`` drains them event-locally rather than slicing an
ever-growing global buffer.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId, OrderId
from qts.domain.instruments import OptionRight
from qts.domain.orders import BracketLeg, BracketSpec, CancelIntent, OrderType
from qts.portfolio.holdings import Holding
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.asset_resolver import (
    ContinuousFutureResolver,
    FutureContractResolver,
    OptionContractRef,
    OptionContractResolver,
    StrategyAssetResolver,
    SymbolResolver,
)
from qts.strategy_sdk.data_view import DataView
from qts.strategy_sdk.events import TimerSubscription
from qts.strategy_sdk.factors import FactorFactory
from qts.strategy_sdk.indicators import IndicatorFactory
from qts.strategy_sdk.portfolio_construction import PortfolioConstructionModel
from qts.strategy_sdk.portfolio_view import PortfolioView
from qts.strategy_sdk.signals import Signal
from qts.strategy_sdk.subcontexts import (
    AssetContext,
    PortfolioContext,
    SignalContext,
    SubscriptionContext,
    TargetContext,
    TimerContext,
    UniverseContext,
)
from qts.strategy_sdk.subscription_registry import DataSubscription
from qts.strategy_sdk.target import OrderSpec, TargetIntent
from qts.strategy_sdk.universe import Universe, UniverseMember, UniverseSelector


@dataclass(slots=True)
class StrategyContext:
    """User-facing strategy facade delegating to focused subcontexts."""

    instrument_registry: SymbolResolver | None = None
    future_chain_registry: FutureContractResolver | ContinuousFutureResolver | None = None
    option_chain_registry: OptionContractResolver | None = None
    data: DataView | None = None
    portfolio: PortfolioView | None = None
    indicator: IndicatorFactory = field(default_factory=IndicatorFactory)
    factor: FactorFactory = field(default_factory=FactorFactory)
    asset: AssetContext = field(init=False)
    target: TargetContext = field(default_factory=TargetContext, init=False)
    subscription: SubscriptionContext = field(default_factory=SubscriptionContext, init=False)
    signal: SignalContext = field(default_factory=SignalContext, init=False)
    timer: TimerContext = field(default_factory=TimerContext, init=False)
    universe_context: UniverseContext = field(default_factory=UniverseContext, init=False)
    portfolio_context: PortfolioContext = field(default_factory=PortfolioContext, init=False)

    def __post_init__(self) -> None:
        """Build the asset subcontext from the configured registries."""
        self.asset = AssetContext(
            instrument_registry=self.instrument_registry,
            future_chain_registry=self.future_chain_registry,
            option_chain_registry=self.option_chain_registry,
        )

    # -- emission views (compatibility; return current undrained buffers) --

    @property
    def intents(self) -> tuple[TargetIntent, ...]:
        """Return target intents emitted since the last drain."""
        return self.target.pending_intents

    @property
    def cancel_intents(self) -> tuple[CancelIntent, ...]:
        """Return cancel intents emitted since the last drain."""
        return self.target.pending_cancels

    @property
    def signals(self) -> tuple[Signal, ...]:
        """Return pending signals waiting for portfolio construction."""
        return self.signal.pending

    @property
    def timer_subscriptions(self) -> tuple[TimerSubscription, ...]:
        """Return timer subscriptions requested during initialize."""
        return self.timer.timer_subscriptions

    @property
    def subscriptions(self) -> tuple[DataSubscription, ...]:
        """Return market-data subscriptions requested by the strategy."""
        return self.subscription.subscriptions

    @property
    def universe(self) -> Universe:
        """Return the current strategy-declared universe."""
        return self.universe_context.universe

    # -- event-local drain + timer freeze (used by StrategyActor) --

    def drain_intents(self) -> tuple[TargetIntent, ...]:
        """Return and clear target intents emitted since the last drain."""
        return self.target.drain_intents()

    def drain_cancels(self) -> tuple[CancelIntent, ...]:
        """Return and clear cancel intents emitted since the last drain."""
        return self.target.drain_cancels()

    def freeze_timers(self) -> None:
        """Freeze timer subscriptions after ``Strategy.initialize``."""
        self.timer.freeze()

    # -- asset resolution --

    def symbol(self, user_symbol: str) -> AssetRef:
        """Resolve a user-facing symbol such as ``AAPL``."""
        return self.asset.symbol(user_symbol)

    def future(self, root_symbol: str, *, contract: str = "front") -> AssetRef:
        """Resolve a futures root to a selectable contract reference."""
        return self.asset.future(root_symbol, contract=contract)

    def option(
        self,
        *,
        underlying: str | AssetRef | InstrumentId,
        expiry: date,
        strike: Decimal,
        right: OptionRight,
    ) -> AssetRef:
        """Resolve an option by underlying symbol/ref and contract attributes."""
        return self.asset.option(underlying=underlying, expiry=expiry, strike=strike, right=right)

    # -- target / cancel emission --

    def target_percent(
        self,
        asset: AssetRef,
        weight: Decimal,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a portfolio-weight target for an asset."""
        return self.target.target_percent(asset, weight, spec=spec, metadata=metadata)

    def target_quantity(
        self,
        asset: AssetRef,
        quantity: Decimal,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a quantity target for an asset."""
        return self.target.target_quantity(asset, quantity, spec=spec, metadata=metadata)

    def target_value(
        self,
        asset: AssetRef,
        value: Decimal,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a notional value target for an asset."""
        return self.target.target_value(asset, value, spec=spec, metadata=metadata)

    def close(
        self,
        asset: AssetRef,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a target that closes an asset position."""
        return self.target.close(asset, spec=spec, metadata=metadata)

    def target_bracket(
        self,
        asset: AssetRef,
        take_profit_price: Decimal,
        stop_loss_price: Decimal,
        *,
        quantity: Decimal = Decimal("1"),
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a bracket order target with take-profit and stop-loss legs."""
        return self.target.target_bracket(
            asset, take_profit_price, stop_loss_price, quantity=quantity, metadata=metadata
        )

    def cancel_order(self, order_id: str, *, reason: str | None = None) -> None:
        """Emit a fire-and-forget cancel intent for an order."""
        self.target.cancel_order(order_id, reason=reason)

    def rebalance(self, weights: dict[AssetRef, Decimal]) -> tuple[TargetIntent, ...]:
        """Emit one percent target per asset in ``weights``."""
        return self.target.rebalance(weights)

    # -- signals / portfolio construction --

    def emit_signal(self, signal: Signal) -> Signal:
        """Record a forecast signal for later portfolio construction."""
        return self.signal.emit_signal(signal)

    def construct_targets(
        self,
        model: PortfolioConstructionModel,
    ) -> tuple[TargetIntent, ...]:
        """Construct and emit target intents from pending signals."""
        targets = model.construct(self.signal.pending)
        for target in targets:
            self.target.emit(target)
        self.signal.clear()
        return targets

    # -- timers --

    def schedule_timer(
        self,
        name: str,
        interval: timedelta,
        *,
        first_fire: datetime | None = None,
    ) -> TimerSubscription:
        """Register a timer that delivers TimerEvent to ``Strategy.on_timer``."""
        return self.timer.schedule_timer(name, interval, first_fire=first_fire)

    # -- subscriptions --

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> DataSubscription:
        """Subscribe to bars for an asset and timeframe."""
        return self.subscription.subscribe(asset, timeframe=timeframe, warmup=warmup)

    def subscribe_ticks(self, asset: AssetRef) -> DataSubscription:
        """Subscribe to tick-level market data for an asset."""
        return self.subscription.subscribe_ticks(asset)

    # -- portfolio queries --

    def holding(self, asset: AssetRef) -> Holding | None:
        """Return the current holding for an asset."""
        return self.portfolio_context.holding(self.portfolio, asset)

    def unrealized_pnl(self, asset: AssetRef) -> Decimal:
        """Return current unrealized PnL if a portfolio mark is available."""
        return self.portfolio_context.unrealized_pnl(self.portfolio, asset)

    def realized_pnl(self, asset: AssetRef) -> Decimal:
        """Return cumulative realized PnL for an asset."""
        return self.portfolio_context.realized_pnl(self.portfolio, asset)

    def avg_cost(self, asset: AssetRef) -> Decimal | None:
        """Return average cost for an asset."""
        return self.portfolio_context.avg_cost(self.portfolio, asset)

    # -- universe --

    def set_universe(self, members: Iterable[UniverseMember]) -> Universe:
        """Replace the strategy-declared universe."""
        return self.universe_context.set_universe(members)

    def set_universe_from_selector(self, selector: UniverseSelector) -> Universe:
        """Replace the strategy-declared universe from a selector result."""
        return self.universe_context.set_universe_from_selector(selector)

    def add_to_universe(self, members: Iterable[UniverseMember]) -> Universe:
        """Add members to the strategy-declared universe."""
        return self.universe_context.add_to_universe(members)

    def remove_from_universe(self, members: Iterable[UniverseMember]) -> Universe:
        """Remove members from the strategy-declared universe."""
        return self.universe_context.remove_from_universe(members)


__all__ = [
    "BracketLeg",
    "BracketSpec",
    "CancelIntent",
    "ContinuousFutureResolver",
    "DataSubscription",
    "FutureContractResolver",
    "OptionContractRef",
    "OptionContractResolver",
    "OrderId",
    "OrderType",
    "Signal",
    "StrategyAssetResolver",
    "StrategyContext",
    "SymbolResolver",
    "TimerSubscription",
]
