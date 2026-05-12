"""Reconnect policy for live feed adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ReconnectPolicy:
    """Deterministic reconnect backoff policy."""

    initial_delay: timedelta
    multiplier: Decimal
    max_delay: timedelta
    max_attempts: int

    def __post_init__(self) -> None:
        if self.initial_delay <= timedelta(0):
            raise ValueError("initial_delay must be positive")
        if self.multiplier < Decimal("1"):
            raise ValueError("multiplier must be at least 1")
        if self.max_delay < self.initial_delay:
            raise ValueError("max_delay must be >= initial_delay")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")

    def delay_for_attempt(self, attempt: int) -> timedelta | None:
        """Return delay for given reconnect attempt, or None after max attempts."""
        if attempt <= 0:
            raise ValueError("attempt must be positive")
        if attempt > self.max_attempts:
            return None
        seconds = self.initial_delay.total_seconds() * float(self.multiplier ** (attempt - 1))
        return min(timedelta(seconds=seconds), self.max_delay)


__all__ = ["ReconnectPolicy"]
