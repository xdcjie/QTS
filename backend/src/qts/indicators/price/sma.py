"""Simple moving average indicator."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from qts.indicators.rolling import RollingWindow


@dataclass(slots=True)
class SMA:
    """Incremental simple moving average."""

    window: int
    _values: RollingWindow[Decimal] = field(init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        self._values = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Perform ready."""
        return self._values.ready

    def update(self, price: Decimal) -> Decimal | None:
        """Perform update."""
        self._values.append(price)
        if not self.ready:
            self.value = None
            return None
        self.value = sum(self._values, Decimal("0")) / Decimal(self.window)
        return self.value


__all__ = ["SMA"]
