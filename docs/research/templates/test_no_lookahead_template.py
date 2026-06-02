"""Template for a no-lookahead regression test for reviewed factors."""

from __future__ import annotations


def test_reviewed_factor_does_not_change_past_values_when_future_data_changes() -> None:
    """Past factor values must be invariant to future observation changes."""
    raise NotImplementedError("build fixture data and assert no-lookahead behavior")
