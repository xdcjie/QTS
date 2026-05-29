"""User-facing Strategy SDK callback event types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.core.time import require_aware_datetime
from qts.domain.orders import OrderSide, OrderState


@dataclass(frozen=True, slots=True)
class TimerEvent:
    """Scheduled strategy timer event."""

    name: str
    time: datetime

    def __post_init__(self) -> None:
        """Validate timer event fields."""
        if not self.name.strip():
            raise ValueError("name must not be empty")
        require_aware_datetime(self.time, name="time")


@dataclass(frozen=True, slots=True)
class TimerSubscription:
    """Strategy-declared timer schedule request."""

    name: str
    interval: timedelta
    first_fire: datetime | None = None

    def __post_init__(self) -> None:
        """Validate timer subscription fields."""
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if self.interval <= timedelta(0):
            raise ValueError("interval must be positive")
        if self.first_fire is not None:
            require_aware_datetime(self.first_fire, name="first_fire")


class TimerScheduler:
    """Deterministic next-fire bookkeeping for strategy timer subscriptions.

    Owns the per-subscription next-fire clock so the runtime can ask, for a
    given domain time, which timers are due. Firing uses ``now >= next_fire``
    and advances ``next_fire`` by whole intervals so a single time jump never
    fires the same timer more than once per elapsed interval.
    """

    def __init__(self) -> None:
        """Create an empty timer scheduler."""
        self._next_fire: dict[str, datetime] = {}
        self._intervals: dict[str, timedelta] = {}

    def register(self, subscription: TimerSubscription) -> None:
        """Register a timer subscription, replacing any prior one with its name."""
        first_fire = subscription.first_fire
        self._intervals[subscription.name] = subscription.interval
        if first_fire is not None:
            self._next_fire[subscription.name] = first_fire
        else:
            # Defer the first fire until the scheduler observes its first time.
            self._next_fire.pop(subscription.name, None)

    def due(self, now: datetime) -> tuple[TimerEvent, ...]:
        """Return timer events due at ``now`` and advance their next-fire times."""
        require_aware_datetime(now, name="now")
        events: list[TimerEvent] = []
        for name in self._intervals:
            interval = self._intervals[name]
            next_fire = self._next_fire.get(name)
            if next_fire is None:
                # First observation establishes the first fire one interval out.
                self._next_fire[name] = now + interval
                continue
            while now >= next_fire:
                events.append(TimerEvent(name=name, time=next_fire))
                next_fire = next_fire + interval
            self._next_fire[name] = next_fire
        return tuple(events)


@dataclass(frozen=True, slots=True)
class OrderUpdate:
    """Strategy-facing order status update."""

    order_id: OrderId
    state: OrderState
    filled_quantity: Decimal = Decimal("0")
    remaining_quantity: Decimal | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        """Validate order update quantities."""
        if self.filled_quantity < Decimal("0"):
            raise ValueError("filled_quantity must be non-negative")
        if self.remaining_quantity is not None and self.remaining_quantity < Decimal("0"):
            raise ValueError("remaining_quantity must be non-negative")


@dataclass(frozen=True, slots=True)
class Fill:
    """Strategy-facing fill event."""

    fill_id: str
    order_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")
    account_id: AccountId | None = None
    intent_id: str | None = None

    def __post_init__(self) -> None:
        """Validate fill economics."""
        if not self.fill_id.strip():
            raise ValueError("fill_id must not be empty")
        if self.intent_id is not None and not self.intent_id.strip():
            raise ValueError("intent_id must not be empty if provided")
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if self.price <= Decimal("0"):
            raise ValueError("price must be positive")
        if self.commission < Decimal("0"):
            raise ValueError("commission must be non-negative")
        if self.slippage < Decimal("0"):
            raise ValueError("slippage must be non-negative")


__all__ = ["Fill", "OrderUpdate", "TimerEvent", "TimerScheduler", "TimerSubscription"]
