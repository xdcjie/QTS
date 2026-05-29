"""Stable ID value objects for accounts, strategies, instruments, orders, events, and brokers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _StringId:
    """Base class for typed string identifiers."""

    value: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        class_name = self.__class__.__name__
        if not isinstance(self.value, str):
            raise TypeError(f"{class_name} value must be a string")
        if not self.value.strip():
            raise ValueError(f"{class_name} must not be empty")

    def __str__(self) -> str:
        """Perform __str__."""
        return self.value


class AccountId(_StringId):
    """Stable internal account identifier."""


class StrategyId(_StringId):
    """Stable internal strategy identifier."""


class InstrumentId(_StringId):
    """Stable internal instrument identifier."""


class OrderId(_StringId):
    """Stable internal order identifier."""


class BrokerId(_StringId):
    """Stable internal broker identifier."""


class EventId(_StringId):
    """Stable internal event identifier."""


class RuntimeRunId(_StringId):
    """Stable identifier for one runtime run across all modes."""


class RuntimeInstanceId(_StringId):
    """Stable identifier for one runtime process/session instance."""


class CorrelationId(_StringId):
    """Identifier grouping events in one business workflow."""


class CausationId(_StringId):
    """Identifier linking an event to the event that caused it."""


class CalendarId(_StringId):
    """Typed calendar identifier to prevent raw string usage."""


class CurrencyCode(_StringId):
    """Typed currency code (USD, EUR, etc.)."""


__all__ = [
    "AccountId",
    "BrokerId",
    "CausationId",
    "CalendarId",
    "CorrelationId",
    "CurrencyCode",
    "EventId",
    "InstrumentId",
    "OrderId",
    "RuntimeInstanceId",
    "RuntimeRunId",
    "StrategyId",
]
