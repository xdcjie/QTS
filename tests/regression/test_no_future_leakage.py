from __future__ import annotations

from datetime import date

import pytest
from qts.research.splits import ResearchSplit, ResearchSplitPlan, walk_forward_split_plans


def test_out_of_sample_window_is_locked_after_tuning_windows() -> None:
    plan = ResearchSplitPlan(
        (
            ResearchSplit("train", "in_sample", date(2026, 1, 1), date(2026, 3, 1)),
            ResearchSplit("validation", "validation", date(2026, 3, 1), date(2026, 4, 1)),
            ResearchSplit("oos", "out_of_sample", date(2026, 4, 1), date(2026, 5, 1)),
        )
    )

    assert plan.to_payload()["windows"][-1]["role"] == "out_of_sample"
    assert plan.to_payload()["leakage_rule"] == "later windows must not tune earlier choices"


def test_split_plan_rejects_future_tuning_after_oos() -> None:
    with pytest.raises(ValueError, match="out_of_sample windows must be locked"):
        ResearchSplitPlan(
            (
                ResearchSplit("train", "in_sample", date(2026, 1, 1), date(2026, 3, 1)),
                ResearchSplit("oos", "out_of_sample", date(2026, 4, 1), date(2026, 5, 1)),
                ResearchSplit("late-validation", "validation", date(2026, 5, 1), date(2026, 6, 1)),
            )
        )


def test_split_plan_rejects_overlapping_windows() -> None:
    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        ResearchSplitPlan(
            (
                ResearchSplit("train", "in_sample", date(2026, 1, 1), date(2026, 3, 1)),
                ResearchSplit("validation", "validation", date(2026, 2, 1), date(2026, 4, 1)),
                ResearchSplit("oos", "out_of_sample", date(2026, 4, 1), date(2026, 5, 1)),
            )
        )


def test_walk_forward_helper_predeclares_locked_oos_windows() -> None:
    plans = walk_forward_split_plans(
        start=date(2026, 1, 1),
        train_days=20,
        validation_days=5,
        oos_days=5,
        cycles=2,
    )

    assert [plan.to_payload()["windows"][-1]["role"] for plan in plans] == [
        "out_of_sample",
        "out_of_sample",
    ]
    assert plans[0].to_payload()["windows"] == [
        {
            "name": "wf-001-train",
            "role": "in_sample",
            "start": "2026-01-01",
            "end": "2026-01-21",
        },
        {
            "name": "wf-001-validation",
            "role": "validation",
            "start": "2026-01-21",
            "end": "2026-01-26",
        },
        {
            "name": "wf-001-oos",
            "role": "out_of_sample",
            "start": "2026-01-26",
            "end": "2026-01-31",
        },
    ]
    assert plans[1].to_payload()["windows"][0]["start"] == "2026-01-31"
