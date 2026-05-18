"""Unit tests for deterministic optimizer walk-forward split definitions."""

from __future__ import annotations

from datetime import date

import pytest
from qts.research.optimizer import WalkForwardPlan, WalkForwardSplit


def test_walk_forward_plan_records_ordered_train_test_windows() -> None:
    split = WalkForwardSplit(
        name="split-001",
        train_start=date(2026, 1, 1),
        train_end=date(2026, 3, 31),
        test_start=date(2026, 4, 1),
        test_end=date(2026, 4, 30),
    )

    plan = WalkForwardPlan((split,))

    assert plan.splits == (split,)
    assert plan.to_metadata() == (
        {
            "name": "split-001",
            "train_start": "2026-01-01",
            "train_end": "2026-03-31",
            "test_start": "2026-04-01",
            "test_end": "2026-04-30",
        },
    )


def test_walk_forward_split_rejects_overlapping_train_and_test_windows() -> None:
    with pytest.raises(ValueError, match="non-overlapping"):
        WalkForwardSplit(
            name="split-001",
            train_start=date(2026, 1, 1),
            train_end=date(2026, 4, 15),
            test_start=date(2026, 4, 1),
            test_end=date(2026, 4, 30),
        )


def test_walk_forward_split_rejects_empty_train_window() -> None:
    with pytest.raises(ValueError, match="train_start must be before train_end"):
        WalkForwardSplit(
            name="split-001",
            train_start=date(2026, 1, 1),
            train_end=date(2026, 1, 1),
            test_start=date(2026, 2, 1),
            test_end=date(2026, 2, 28),
        )


def test_walk_forward_plan_requires_at_least_one_split() -> None:
    with pytest.raises(ValueError, match="requires at least one split"):
        WalkForwardPlan(())
