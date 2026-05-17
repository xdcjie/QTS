"""Parameter space + cartesian product grid for optimizer sweeps."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import product
from typing import Any


@dataclass(frozen=True, slots=True)
class ParameterSpace:
    """One dimension of an optimization sweep — a parameter name and its values."""

    name: str
    values: tuple[Any, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("parameter space name must not be empty")
        if not self.values:
            raise ValueError("parameter space must contain at least one value")


class ParameterGrid:
    """Cartesian product of multiple ``ParameterSpace`` dimensions.

    Iteration yields dictionaries of ``{parameter_name: value}`` in stable
    order (lexicographic on parameter declaration order, leftmost varies
    slowest).
    """

    def __init__(self, *spaces: ParameterSpace) -> None:
        if not spaces:
            raise ValueError("ParameterGrid requires at least one ParameterSpace")
        names = [space.name for space in spaces]
        if len(set(names)) != len(names):
            raise ValueError("duplicate parameter names in grid")
        self._spaces = tuple(spaces)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        names = [space.name for space in self._spaces]
        value_lists = [list(space.values) for space in self._spaces]
        for combination in product(*value_lists):
            yield dict(zip(names, combination, strict=True))

    def size(self) -> int:
        """Return the total number of combinations the grid will yield."""
        total = 1
        for space in self._spaces:
            total *= len(space.values)
        return total


__all__ = ["ParameterGrid", "ParameterSpace"]
