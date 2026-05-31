"""Strategy subcontexts that own the state behind ``StrategyContext``.

QTS-FINAL-005 splits the oversized, fully-stateful ``StrategyContext`` facade into
focused subcontexts so no single class owns all SDK state and per-event emissions
are bounded and drainable:

* ``AssetContext`` owns symbol/future/option resolution.
* ``TargetContext`` owns target-intent emission and cancel intents with bounded,
  drainable buffers (``drain_intents`` / ``drain_cancels``).
* ``SubscriptionContext`` owns the market-data subscription registry.
* ``SignalContext`` owns pending forecast signals.
* ``TimerContext`` owns timer subscriptions and freezes them after initialize.
* ``UniverseContext`` owns the strategy-declared universe.
* ``PortfolioContext`` answers portfolio queries over a per-event ``PortfolioView``.

``StrategyContext`` retains only a compatibility surface and delegates to these.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId, OrderId
from qts.domain.instruments import OptionRight
from qts.domain.orders import BracketLeg, BracketSpec, CancelIntent, OrderSide, OrderType
from qts.portfolio.holdings import Holding
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.asset_resolver import (
    ContinuousFutureResolver,
    FutureContractResolver,
    OptionContractResolver,
    StrategyAssetResolver,
    SymbolResolver,
)
from qts.strategy_sdk.events import TimerSubscription
from qts.strategy_sdk.portfolio_view import PortfolioView
from qts.strategy_sdk.signals import Signal
from qts.strategy_sdk.subscription_registry import DataSubscription, StrategySubscriptionRegistry
from qts.strategy_sdk.target import OrderSpec, TargetIntent, TargetIntentType
from qts.strategy_sdk.target_emitter import TargetIntentEmitter
from qts.strategy_sdk.universe import Universe, UniverseMember, UniverseSelector


class AssetContext:
    """Owns user-symbol/future/option resolution for a strategy."""

    def __init__(
        self,
        *,
        instrument_registry: SymbolResolver | None = None,
        future_chain_registry: FutureContractResolver | ContinuousFutureResolver | None = None,
        option_chain_registry: OptionContractResolver | None = None,
    ) -> None:
        """Build the asset resolver from the configured registries."""
        self._resolver = StrategyAssetResolver(
            instrument_registry=instrument_registry,
            future_chain_registry=future_chain_registry,
            option_chain_registry=option_chain_registry,
        )

    def symbol(self, user_symbol: str) -> AssetRef:
        """Resolve a user-facing symbol such as ``AAPL``."""
        return self._resolver.resolve_symbol(user_symbol)

    def future(self, root_symbol: str, *, contract: str = "front") -> AssetRef:
        """Resolve a futures root to a selectable contract reference."""
        return self._resolver.resolve_future(root_symbol, contract=contract)

    def option(
        self,
        *,
        underlying: str | AssetRef | InstrumentId,
        expiry: date,
        strike: Decimal,
        right: OptionRight,
    ) -> AssetRef:
        """Resolve an option by underlying symbol/ref and contract attributes."""
        return self._resolver.resolve_option(
            underlying=underlying, expiry=expiry, strike=strike, right=right
        )


class TargetContext:
    """Owns target-intent emission and cancel intents with bounded, drainable buffers."""

    def __init__(self) -> None:
        """Initialize empty, drainable target-intent and cancel-intent buffers."""
        self._emitter = TargetIntentEmitter()
        self._cancel_intents: list[CancelIntent] = []

    @property
    def pending_intents(self) -> tuple[TargetIntent, ...]:
        """Return target intents emitted since the last drain."""
        return self._emitter.intents

    @property
    def pending_cancels(self) -> tuple[CancelIntent, ...]:
        """Return cancel intents emitted since the last drain."""
        return tuple(self._cancel_intents)

    def drain_intents(self) -> tuple[TargetIntent, ...]:
        """Return and clear the target intents emitted since the last drain."""
        return self._emitter.drain()

    def drain_cancels(self) -> tuple[CancelIntent, ...]:
        """Return and clear the cancel intents emitted since the last drain."""
        drained = tuple(self._cancel_intents)
        self._cancel_intents.clear()
        return drained

    def emit(self, intent: TargetIntent) -> TargetIntent:
        """Record an already-built target intent (used by portfolio construction)."""
        return self._emitter.emit(intent)

    def target_percent(
        self,
        asset: AssetRef,
        weight: Decimal,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a portfolio-weight target for an asset."""
        return self._emitter.emit(
            TargetIntent(
                asset=asset,
                intent_type=TargetIntentType.PERCENT,
                value=weight,
                order_spec=spec or OrderSpec(),
                metadata=metadata or {},
            )
        )

    def target_quantity(
        self,
        asset: AssetRef,
        quantity: Decimal,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a quantity target for an asset."""
        return self._emitter.emit(
            TargetIntent(
                asset=asset,
                intent_type=TargetIntentType.QUANTITY,
                value=quantity,
                order_spec=spec or OrderSpec(),
                metadata=metadata or {},
            )
        )

    def target_value(
        self,
        asset: AssetRef,
        value: Decimal,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a notional value target for an asset."""
        return self._emitter.emit(
            TargetIntent(
                asset=asset,
                intent_type=TargetIntentType.VALUE,
                value=value,
                order_spec=spec or OrderSpec(),
                metadata=metadata or {},
            )
        )

    def close(
        self,
        asset: AssetRef,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a target that closes an asset position."""
        return self._emitter.emit(
            TargetIntent(
                asset=asset,
                intent_type=TargetIntentType.CLOSE,
                value=None,
                order_spec=spec or OrderSpec(),
                metadata=metadata or {},
            )
        )

    def target_bracket(
        self,
        asset: AssetRef,
        take_profit_price: Decimal,
        stop_loss_price: Decimal,
        *,
        quantity: Decimal = Decimal("1"),
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a bracket order target with take-profit and stop-loss legs.

        ``quantity`` is the signed parent target: positive opens (or holds) a long,
        negative a short. The bracket's exit legs face the opposite direction of the
        parent position, so a positive ``quantity`` produces ``sell`` exit legs and a
        negative ``quantity`` produces ``buy`` exit legs (always positive quantity).
        """
        if quantity == Decimal("0"):
            raise ValueError("target_bracket quantity must be non-zero")
        exit_side = OrderSide.SELL if quantity > Decimal("0") else OrderSide.BUY
        leg_quantity = abs(quantity)
        bracket = BracketSpec(
            legs=(
                BracketLeg(
                    order_type=OrderType.LIMIT,
                    side=exit_side,
                    quantity=leg_quantity,
                    limit_price=take_profit_price,
                ),
                BracketLeg(
                    order_type=OrderType.STOP,
                    side=exit_side,
                    quantity=leg_quantity,
                    stop_price=stop_loss_price,
                ),
            )
        )
        spec = OrderSpec(order_type=OrderType.BRACKET, bracket=bracket)
        return self._emitter.emit(
            TargetIntent(
                asset=asset,
                intent_type=TargetIntentType.QUANTITY,
                value=quantity,
                order_spec=spec,
                metadata=metadata or {},
            )
        )

    def rebalance(self, weights: Mapping[AssetRef, Decimal]) -> tuple[TargetIntent, ...]:
        """Emit one percent target per asset in ``weights``."""
        return tuple(self.target_percent(asset, weight) for asset, weight in weights.items())

    def cancel_order(self, order_id: str, *, reason: str | None = None) -> None:
        """Emit a fire-and-forget cancel intent for an order."""
        self._cancel_intents.append(CancelIntent(order_id=OrderId(order_id), reason=reason))


class SubscriptionContext:
    """Owns the strategy's market-data subscription registry."""

    def __init__(self) -> None:
        """Initialize an empty subscription registry."""
        self._registry = StrategySubscriptionRegistry()

    @property
    def subscriptions(self) -> tuple[DataSubscription, ...]:
        """Return market-data subscriptions requested by the strategy."""
        return self._registry.subscriptions

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> DataSubscription:
        """Subscribe to bars for an asset and timeframe."""
        return self._registry.subscribe(
            DataSubscription(asset=asset, timeframe=timeframe, warmup=warmup)
        )

    def subscribe_ticks(self, asset: AssetRef) -> DataSubscription:
        """Subscribe to tick-level market data for an asset."""
        return self._registry.subscribe(DataSubscription(asset=asset, timeframe="tick", warmup=1))


class SignalContext:
    """Owns pending forecast signals awaiting portfolio construction."""

    def __init__(self) -> None:
        """Initialize an empty pending-signal buffer."""
        self._signals: list[Signal] = []

    @property
    def pending(self) -> tuple[Signal, ...]:
        """Return pending signals waiting for portfolio construction."""
        return tuple(self._signals)

    def emit_signal(self, signal: Signal) -> Signal:
        """Record a forecast signal for later portfolio construction."""
        self._signals.append(signal)
        return signal

    def clear(self) -> None:
        """Clear pending signals once they have been consumed."""
        self._signals.clear()


class TimerContext:
    """Owns timer subscriptions; freezes them after ``Strategy.initialize``."""

    def __init__(self) -> None:
        """Initialize an empty, unfrozen timer-subscription buffer."""
        self._timer_subscriptions: list[TimerSubscription] = []
        self._frozen = False

    @property
    def timer_subscriptions(self) -> tuple[TimerSubscription, ...]:
        """Return timer subscriptions requested during initialize."""
        return tuple(self._timer_subscriptions)

    def freeze(self) -> None:
        """Freeze timer subscriptions; later ``schedule_timer`` calls are rejected."""
        self._frozen = True

    def schedule_timer(
        self,
        name: str,
        interval: timedelta,
        *,
        first_fire: datetime | None = None,
    ) -> TimerSubscription:
        """Register an initialization-time timer delivering TimerEvent to ``on_timer``."""
        if self._frozen:
            raise RuntimeError(
                "timer subscriptions are initialization-only and are frozen after "
                "Strategy.initialize; schedule timers in initialize()"
            )
        subscription = TimerSubscription(name=name, interval=interval, first_fire=first_fire)
        self._timer_subscriptions.append(subscription)
        return subscription


class UniverseContext:
    """Owns the strategy-declared universe."""

    def __init__(self) -> None:
        """Initialize an empty universe."""
        self._universe = Universe.empty()

    @property
    def universe(self) -> Universe:
        """Return the current strategy-declared universe."""
        return self._universe

    def set_universe(self, members: Iterable[UniverseMember]) -> Universe:
        """Replace the strategy-declared universe."""
        self._universe = Universe.from_members(members)
        return self._universe

    def set_universe_from_selector(self, selector: UniverseSelector) -> Universe:
        """Replace the strategy-declared universe from a selector result."""
        return self.set_universe(selector.select_universe())

    def add_to_universe(self, members: Iterable[UniverseMember]) -> Universe:
        """Add members to the strategy-declared universe."""
        self._universe = self._universe.add(members)
        return self._universe

    def remove_from_universe(self, members: Iterable[UniverseMember]) -> Universe:
        """Remove members from the strategy-declared universe."""
        self._universe = self._universe.remove(members)
        return self._universe


class PortfolioContext:
    """Answers portfolio queries over a per-event ``PortfolioView`` (owns no state)."""

    def holding(self, view: PortfolioView | None, asset: AssetRef) -> Holding | None:
        """Return the current holding for an asset, or ``None`` without a view."""
        return None if view is None else view.holding(asset)

    def unrealized_pnl(self, view: PortfolioView | None, asset: AssetRef) -> Decimal:
        """Return current unrealized PnL, or zero without a view."""
        return Decimal("0") if view is None else view.unrealized_pnl(asset)

    def realized_pnl(self, view: PortfolioView | None, asset: AssetRef) -> Decimal:
        """Return cumulative realized PnL, or zero without a view."""
        return Decimal("0") if view is None else view.realized_pnl(asset)

    def avg_cost(self, view: PortfolioView | None, asset: AssetRef) -> Decimal | None:
        """Return average cost for an asset, or ``None`` without a view."""
        return None if view is None else view.avg_cost(asset)


__all__ = [
    "AssetContext",
    "PortfolioContext",
    "SignalContext",
    "SubscriptionContext",
    "TargetContext",
    "TimerContext",
    "UniverseContext",
]
