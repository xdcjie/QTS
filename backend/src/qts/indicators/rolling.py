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
        """Perform __post_init__."""
        if self.size <= 0:
            raise ValueError("size must be positive")
        self._values = deque(maxlen=self.size)

    @property
    def ready(self) -> bool:
        """Perform ready."""
        return len(self._values) == self.size

    def append(self, value: T) -> None:
        """Perform append."""
        self._values.append(value)

    def snapshot(self) -> tuple[T, ...]:
        """Perform snapshot."""
        return tuple(self._values)

    def restore(self, values: Iterable[T]) -> RollingWindow[T]:
        """Perform restore."""
        restored = RollingWindow[T](self.size)
        for value in values:
            restored.append(value)
        return restored

    def __iter__(self) -> Iterator[T]:
        """Perform __iter__."""
        return iter(self._values)

    def __len__(self) -> int:
        """Perform __len__."""
        return len(self._values)


__all__ = ["RollingWindow"]
