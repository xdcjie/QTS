"""Fixed-size rolling window."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class RollingWindow(Generic[T]):
    """Bounded FIFO buffer with warmup state."""

    size: int
    _values: deque[T] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate the positive window size and allocate the bounded deque."""
        if self.size <= 0:
            raise ValueError("size must be positive")
        self._values = deque(maxlen=self.size)

    @property
    def ready(self) -> bool:
        """Return True once the window holds its full capacity of values."""
        return len(self._values) == self.size

    def append(self, value: T) -> None:
        """Add a value, evicting the oldest once at capacity."""
        self._values.append(value)

    def snapshot(self) -> tuple[T, ...]:
        """Return the current window contents as an immutable tuple."""
        return tuple(self._values)

    def restore(self, values: Iterable[T]) -> RollingWindow[T]:
        """Return a new same-sized window populated from the given values."""
        restored = RollingWindow[T](self.size)
        for value in values:
            restored.append(value)
        return restored

    def __iter__(self) -> Iterator[T]:
        """Iterate over the window values from oldest to newest."""
        return iter(self._values)

    def __len__(self) -> int:
        """Return the number of values currently buffered."""
        return len(self._values)


__all__ = ["RollingWindow"]
