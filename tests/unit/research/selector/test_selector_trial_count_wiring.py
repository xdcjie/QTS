"""Unit tests: campaign-level multiplicity context is recorded on the selection result.

The multiple-testing correction (``trial_count``, ``multiplicity_scope`` and the
Benjamini-Hochberg control level ``false_discovery_rate``) must be serialized into
``selection_result.json`` so the statistical haircut applied to every candidate is
auditable, not implicit. These tests lock that contract and the documented
behavior that more trials lower the adjusted score under identical metrics.
"""

from __future__ import annotations

import json

import pytest
from qts.research.selector import CandidateSelector, SelectionPolicy


def test_selection_payload_records_campaign_multiplicity_context() -> None:
    result = CandidateSelector(SelectionPolicy(false_discovery_rate=0.05)).select(
        (_candidate("a"), _candidate("b")),
        trial_count=37,
        multiplicity_scope="generation",
    )

    assert result.trial_count == 37
    assert result.multiplicity_scope == "generation"
    assert result.false_discovery_rate == 0.05

    payload = result.to_payload()
    assert payload["trial_count"] == 37
    assert payload["multiplicity_scope"] == "generation"
    assert payload["false_discovery_rate"] == 0.05
    # The campaign-level fields are part of the hashed payload, so they survive a
    # round-trip and any tampering changes the selection hash.
    assert payload["selection_hash"] == result.selection_hash
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload


def test_default_scope_is_generation_and_fdr_defaults_to_policy() -> None:
    result = CandidateSelector(SelectionPolicy()).select((_candidate("a"),))

    assert result.trial_count == 1
    assert result.multiplicity_scope == "generation"
    assert result.false_discovery_rate == SelectionPolicy().false_discovery_rate

    payload = result.to_payload()
    assert payload["multiplicity_scope"] == "generation"
    assert payload["false_discovery_rate"] == SelectionPolicy().false_discovery_rate


def test_unknown_multiplicity_scope_is_rejected() -> None:
    with pytest.raises(ValueError, match="multiplicity_scope must be one of"):
        CandidateSelector(SelectionPolicy()).select(
            (_candidate("a"),),
            multiplicity_scope="strategy",
        )


def test_more_trials_lower_adjusted_score_under_identical_metrics() -> None:
    # Two candidates with cross-trial Sharpe dispersion so the expected-maximum
    # Sharpe haircut is non-zero; the raw metrics are held fixed across runs.
    candidates = (
        _candidate("winner", observed_sharpe=0.18, oos_sharpe=2.85),
        _candidate("runner-up", observed_sharpe=0.06, oos_sharpe=0.95),
    )
    policy = SelectionPolicy()

    single = CandidateSelector(policy).select(candidates, trial_count=1)
    many = CandidateSelector(policy).select(candidates, trial_count=1000)

    single_winner = _by_id(single, "winner")
    many_winner = _by_id(many, "winner")

    # The raw objective is identical; the multiplicity haircut grows with trials so
    # the adjusted score strictly drops and the deflated Sharpe collapses.
    assert single_winner.raw_score == many_winner.raw_score
    assert single_winner.adjusted_score == single_winner.raw_score  # no inflation at N=1
    assert many_winner.adjusted_score is not None
    assert single_winner.adjusted_score is not None
    assert many_winner.adjusted_score < single_winner.adjusted_score

    assert single_winner.multiplicity_adjustment is not None
    assert many_winner.multiplicity_adjustment is not None
    assert single_winner.multiplicity_adjustment["trial_count"] == 1
    assert many_winner.multiplicity_adjustment["trial_count"] == 1000
    assert (
        many_winner.multiplicity_adjustment["deflated_sharpe_ratio"]
        < single_winner.multiplicity_adjustment["deflated_sharpe_ratio"]
    )


def _by_id(result: object, candidate_id: str) -> object:
    selected = next(  # type: ignore[attr-defined]
        candidate
        for candidate in result.selected_candidates  # type: ignore[attr-defined]
        if candidate.candidate_id == candidate_id
    )
    return selected


def _candidate(
    candidate_id: str,
    *,
    observed_sharpe: float = 0.12,
    oos_sharpe: float = 1.6,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "metrics": {
            "performance": {
                "max_drawdown": 0.07,
                "observed_sharpe": observed_sharpe,
                "oos_sharpe": oos_sharpe,
                "return_observation_count": 252,
                "total_return": 0.16,
            },
            "quality": {"profit_factor": 1.5},
            "trading": {"oos_trade_count": 50},
            "costs": {"cost_sensitivity": 0.01},
        },
        "data_quality": {"accepted": True},
        "reproducibility": {"git_dirty": False},
    }
