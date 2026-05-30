"""Exponential moving average indicator."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from qts.indicators.rolling import RollingWindow


@dataclass(slots=True)
class EMA:
    """Incremental EMA using SMA as the warmup seed."""

    window: int
    _warmup: RollingWindow[Decimal] = field(init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Allocate the warmup rolling window sized to the EMA period."""
        self._warmup = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return True once the EMA has produced its seeded value."""
        return self.value is not None

    def update(self, price: Decimal) -> Decimal | None:
        """Feed a new price and return the updated EMA, or None while warming up."""
        if self.value is None:
            self._warmup.append(price)
            if not self._warmup.ready:
                return None
            self.value = sum(self._warmup, Decimal("0")) / Decimal(self.window)
            return self.value

        multiplier = Decimal("2") / Decimal(self.window + 1)
        self.value = (price - self.value) * multiplier + self.value
        return self.value


__all__ = ["EMA"]
