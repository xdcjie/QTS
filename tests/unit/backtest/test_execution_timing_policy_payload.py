"""QTS-FINAL-003: fill-timing policy lives in the domain layer and serializes
its honesty facts for the backtest manifest.

The model now owns the shared rule independently of the backtest package; these
gates lock the manifest payload contract that promotion gating reads.
"""

from __future__ import annotations

import pytest
from qts.domain.execution_timing import ExecutionTimingModel, FillPolicy


def test_policy_owner_is_domain_layer() -> None:
    assert ExecutionTimingModel.__module__ == "qts.domain.execution_timing"
    assert FillPolicy.__module__ == "qts.domain.execution_timing"


def test_next_bar_open_payload_is_next_obtainable_and_promotion_grade() -> None:
    payload = ExecutionTimingModel.promotion_grade().to_manifest_payload()

    assert payload == {
        "fill_policy": "next_bar_open",
        "fill_timing_basis": "next_bar_open",
        "optimistic": False,
        "optimistic_waiver": False,
        "promotion_grade": True,
    }


def test_same_bar_close_payload_is_optimistic_and_never_promotion_grade() -> None:
    payload = ExecutionTimingModel.research_only().to_manifest_payload()

    assert payload == {
        "fill_policy": "same_bar_close",
        "fill_timing_basis": "same_bar_close",
        "optimistic": True,
        "optimistic_waiver": True,
        "promotion_grade": False,
    }


def test_from_value_round_trips_policy_and_waiver() -> None:
    model = ExecutionTimingModel.from_value("same_bar_close", optimistic_waiver=True)
    assert model.fill_policy is FillPolicy.SAME_BAR_CLOSE
    assert model.optimistic_waiver is True

    with pytest.raises(ValueError, match="optimistic_waiver"):
        ExecutionTimingModel.from_value("same_bar_close")
