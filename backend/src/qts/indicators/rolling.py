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
        if self.size <= 0:
            raise ValueError("size must be positive")
        self._values = deque(maxlen=self.size)

    @property
    def ready(self) -> bool:
        return len(self._values) == self.size

    def append(self, value: T) -> None:
        self._values.append(value)

    def snapshot(self) -> tuple[T, ...]:
        return tuple(self._values)

    def restore(self, values: Iterable[T]) -> RollingWindow[T]:
        restored = RollingWindow[T](self.size)
        for value in values:
            restored.append(value)
        return restored

    def __iter__(self) -> Iterator[T]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)


__all__ = ["RollingWindow"]
