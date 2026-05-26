"""Leakage-safe research split definitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any


@dataclass(frozen=True, slots=True)
class ResearchSplit:
    """One immutable split window."""

    name: str
    role: str
    start: date
    end: date

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("split name is required")
        if self.role not in {"in_sample", "validation", "out_of_sample", "report_only"}:
            raise ValueError(f"unsupported split role: {self.role}")
        if self.start >= self.end:
            raise ValueError("split start must be before end")

    def to_payload(self) -> dict[str, str]:
        """Return deterministic split metadata."""

        return {
            "end": self.end.isoformat(),
            "name": self.name,
            "role": self.role,
            "start": self.start.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ResearchSplitPlan:
    """Ordered, leakage-safe split manifest."""

    splits: tuple[ResearchSplit, ...]

    @classmethod
    def from_config(cls, payload: Mapping[str, Any]) -> ResearchSplitPlan:
        """Build deterministic splits from manifest config."""

        raw_splits = payload.get("windows", ())
        if not isinstance(raw_splits, list) or not raw_splits:
            raise ValueError("splits.windows must not be empty")
        splits: list[ResearchSplit] = []
        for item in raw_splits:
            if not isinstance(item, dict):
                raise ValueError("split window must be a mapping")
            splits.append(
                ResearchSplit(
                    name=cls._required_text(item, "name"),
                    role=cls._required_text(item, "role"),
                    start=date.fromisoformat(cls._required_text(item, "start")),
                    end=date.fromisoformat(cls._required_text(item, "end")),
                )
            )
        return cls(tuple(splits))

    def __post_init__(self) -> None:
        if not self.splits:
            raise ValueError("split plan requires at least one split")
        seen: set[str] = set()
        previous_end: date | None = None
        for split in self.splits:
            if split.name in seen:
                raise ValueError(f"duplicate split name: {split.name}")
            seen.add(split.name)
            if previous_end is not None and split.start < previous_end:
                raise ValueError("split windows must be ordered and non-overlapping")
            previous_end = split.end
        oos_positions = [
            index for index, split in enumerate(self.splits) if split.role == "out_of_sample"
        ]
        if not oos_positions:
            raise ValueError("split plan requires an out_of_sample window")
        for index in oos_positions:
            for later in self.splits[index + 1 :]:
                if later.role != "report_only":
                    raise ValueError(
                        "out_of_sample windows must be locked after earlier tuning windows"
                    )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready split manifest."""

        return {
            "interval_semantics": "[start, end)",
            "leakage_rule": "later windows must not tune earlier choices",
            "windows": [split.to_payload() for split in self.splits],
        }

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()


def walk_forward_split_plans(
    *,
    start: date,
    train_days: int,
    validation_days: int,
    oos_days: int,
    cycles: int,
    step_days: int | None = None,
) -> tuple[ResearchSplitPlan, ...]:
    """Return deterministic leakage-safe walk-forward split plans."""

    for field_name, value in (
        ("train_days", train_days),
        ("validation_days", validation_days),
        ("oos_days", oos_days),
        ("cycles", cycles),
    ):
        if value < 1:
            raise ValueError(f"{field_name} must be positive")
    step = train_days + validation_days + oos_days if step_days is None else step_days
    if step < 1:
        raise ValueError("step_days must be positive")
    plans: list[ResearchSplitPlan] = []
    for index in range(cycles):
        cycle_start = start + timedelta(days=index * step)
        train_end = cycle_start + timedelta(days=train_days)
        validation_end = train_end + timedelta(days=validation_days)
        oos_end = validation_end + timedelta(days=oos_days)
        cycle_id = f"{index + 1:03d}"
        plans.append(
            ResearchSplitPlan(
                (
                    ResearchSplit(
                        f"wf-{cycle_id}-train",
                        "in_sample",
                        cycle_start,
                        train_end,
                    ),
                    ResearchSplit(
                        f"wf-{cycle_id}-validation",
                        "validation",
                        train_end,
                        validation_end,
                    ),
                    ResearchSplit(
                        f"wf-{cycle_id}-oos",
                        "out_of_sample",
                        validation_end,
                        oos_end,
                    ),
                )
            )
        )
    return tuple(plans)


__all__ = ["ResearchSplit", "ResearchSplitPlan", "walk_forward_split_plans"]
