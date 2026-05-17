"""Order execution specification value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from qts.core.time import require_aware_datetime


class BrokerOrderType(StrEnum):
    """Order types modeled before broker submission."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    MARKET_ON_OPEN = "market_on_open"
    MARKET_ON_CLOSE = "market_on_close"
    BRACKET = "bracket"
    ICEBERG = "iceberg"


class TimeInForce(StrEnum):
    """Time-in-force values modeled at the execution boundary."""

    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"
    GTD = "gtd"
    OPG = "opg"
    ATC = "atc"


@dataclass(frozen=True, slots=True)
class BracketLeg:
    """One child leg of a bracket order."""

    order_type: BrokerOrderType
    side: str
    quantity: Decimal
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None

    def __post_init__(self) -> None:
        if self.quantity <= Decimal("0"):
            raise ValueError("bracket leg quantity must be positive")
        if not self.side.strip():
            raise ValueError("bracket leg side must not be empty")
        _validate_optional_price(self.limit_price, "limit_price")
        _validate_optional_price(self.stop_price, "stop_price")


@dataclass(frozen=True, slots=True)
class BracketSpec:
    """Parent order bracket with child OCO legs."""

    legs: tuple[BracketLeg, ...]

    def __post_init__(self) -> None:
        if len(self.legs) < 2:
            raise ValueError("bracket orders require at least two legs")


@dataclass(frozen=True, slots=True)
class OrderSpec:
    """Typed execution shape carried from strategy intent to broker request."""

    order_type: BrokerOrderType = BrokerOrderType.MARKET
    time_in_force: TimeInForce = TimeInForce.DAY
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    trail_amount: Decimal | None = None
    trail_percent: Decimal | None = None
    good_til_date: datetime | None = None
    bracket: BracketSpec | None = None

    def __post_init__(self) -> None:
        _validate_optional_price(self.limit_price, "limit_price")
        _validate_optional_price(self.stop_price, "stop_price")
        _validate_optional_price(self.trail_amount, "trail_amount")
        if self.trail_percent is not None and (
            self.trail_percent <= Decimal("0") or self.trail_percent > Decimal("100")
        ):
            raise ValueError("trail_percent must be in (0, 100]")
        if self.good_til_date is not None:
            require_aware_datetime(self.good_til_date, name="good_til_date")
        self._validate_shape()

    def to_payload(self) -> dict[str, object]:
        """Serialize the execution spec for events and manifests."""
        payload: dict[str, object] = {
            "order_type": self.order_type.value,
            "time_in_force": self.time_in_force.value,
            "limit_price": None if self.limit_price is None else str(self.limit_price),
            "stop_price": None if self.stop_price is None else str(self.stop_price),
            "trail_amount": None if self.trail_amount is None else str(self.trail_amount),
            "trail_percent": None if self.trail_percent is None else str(self.trail_percent),
            "good_til_date": None if self.good_til_date is None else self.good_til_date.isoformat(),
        }
        if self.bracket is not None:
            payload["bracket_legs"] = [
                {
                    "order_type": leg.order_type.value,
                    "side": leg.side,
                    "quantity": str(leg.quantity),
                    "limit_price": None if leg.limit_price is None else str(leg.limit_price),
                    "stop_price": None if leg.stop_price is None else str(leg.stop_price),
                }
                for leg in self.bracket.legs
            ]
        return payload

    def _validate_shape(self) -> None:
        if self.order_type is BrokerOrderType.MARKET and any(
            value is not None
            for value in (
                self.limit_price,
                self.stop_price,
                self.trail_amount,
                self.trail_percent,
                self.bracket,
            )
        ):
            raise ValueError("market orders cannot carry price, trailing, or bracket fields")
        if self.order_type is BrokerOrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if self.order_type is BrokerOrderType.STOP and self.stop_price is None:
            raise ValueError("stop_price is required for stop orders")
        if self.order_type is BrokerOrderType.STOP_LIMIT and (
            self.stop_price is None or self.limit_price is None
        ):
            raise ValueError("stop_limit orders require stop_price and limit_price")
        if self.order_type is BrokerOrderType.TRAILING_STOP and (
            self.trail_amount is None and self.trail_percent is None
        ):
            raise ValueError("trailing_stop orders require trail_amount or trail_percent")
        if self.order_type is BrokerOrderType.BRACKET and self.bracket is None:
            raise ValueError("bracket orders require bracket legs")


def _validate_optional_price(value: Decimal | None, name: str) -> None:
    if value is not None and value < Decimal("0"):
        raise ValueError(f"{name} must be non-negative")


__all__ = [
    "BracketLeg",
    "BracketSpec",
    "BrokerOrderType",
    "OrderSpec",
    "TimeInForce",
]
