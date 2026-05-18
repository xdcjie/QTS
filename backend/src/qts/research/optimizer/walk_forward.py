"""Walk-forward split definitions for optimizer validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class WalkForwardSplit:
    """One deterministic train/test window definition."""

    name: str
    train_start: date
    train_end: date
    test_start: date
    test_end: date

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("walk-forward split name must not be empty")
        if self.train_start >= self.train_end:
            raise ValueError("train_start must be before train_end")
        if self.test_start >= self.test_end:
            raise ValueError("test_start must be before test_end")
        if self.train_end > self.test_start:
            raise ValueError("train/test windows must be ordered and non-overlapping")

    def to_metadata(self) -> dict[str, str]:
        """Return a deterministic JSON-ready representation."""
        return {
            "name": self.name,
            "train_start": self.train_start.isoformat(),
            "train_end": self.train_end.isoformat(),
            "test_start": self.test_start.isoformat(),
            "test_end": self.test_end.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class WalkForwardPlan:
    """Collection of walk-forward split definitions."""

    splits: tuple[WalkForwardSplit, ...]

    def __post_init__(self) -> None:
        if not self.splits:
            raise ValueError("WalkForwardPlan requires at least one split")
        names = [split.name for split in self.splits]
        if len(set(names)) != len(names):
            raise ValueError("WalkForwardPlan split names must be unique")
        for previous, current in zip(self.splits, self.splits[1:], strict=False):
            if previous.test_end > current.train_start:
                raise ValueError("WalkForwardPlan splits must be ordered and non-overlapping")

    def to_metadata(self) -> tuple[dict[str, str], ...]:
        """Return deterministic JSON-ready split metadata."""
        return tuple(split.to_metadata() for split in self.splits)


__all__ = ["WalkForwardPlan", "WalkForwardSplit"]
