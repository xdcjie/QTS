"""Unit tests for autonomous research candidate selection."""

from __future__ import annotations

import json

import pytest
from qts.research.metrics_schema import ResearchMetricDefinition, ResearchMetricsSchema
from qts.research.selector import CandidateSelector, SelectionPolicy


def test_candidate_selector_rejects_failed_evidence_and_ranks_survivors() -> None:
    policy = SelectionPolicy(
        max_drawdown=0.20,
        min_oos_trade_count=20,
        max_selected=2,
    )
    result = CandidateSelector(policy).select(
        (
            _candidate(
                "high-return-high-drawdown",
                total_return=0.90,
                oos_sharpe=2.4,
                max_drawdown=0.42,
                oos_trade_count=110,
            ),
            _candidate(
                "high-sharpe-low-trades",
                total_return=0.20,
                oos_sharpe=3.1,
                max_drawdown=0.05,
                oos_trade_count=3,
            ),
            _candidate(
                "failed-data-quality",
                total_return=0.18,
                oos_sharpe=1.6,
                max_drawdown=0.06,
                oos_trade_count=45,
                data_quality_accepted=False,
            ),
            _candidate(
                "dirty-reproducibility",
                total_return=0.16,
                oos_sharpe=1.5,
                max_drawdown=0.07,
                oos_trade_count=40,
                git_dirty=True,
            ),
            _candidate(
                "steady",
                total_return=0.16,
                oos_sharpe=1.7,
                max_drawdown=0.07,
                oos_trade_count=50,
            ),
            _candidate(
                "second",
                total_return=0.14,
                oos_sharpe=1.3,
                max_drawdown=0.05,
                oos_trade_count=60,
            ),
        )
    )

    assert [candidate.candidate_id for candidate in result.selected_candidates] == [
        "steady",
        "second",
    ]
    assert (
        result.selected_candidates[0].composite_score
        > result.selected_candidates[1].composite_score
    )

    rejected = {
        candidate.candidate_id: candidate.reasons for candidate in result.rejected_candidates
    }
    assert rejected["high-return-high-drawdown"] == ("max_drawdown: 0.42 exceeds 0.2",)
    assert rejected["high-sharpe-low-trades"] == ("oos_trade_count: 3 below 20",)
    assert rejected["failed-data-quality"] == ("data_quality: artifact rejected",)
    assert rejected["dirty-reproducibility"] == ("reproducibility: git working tree is dirty",)
    assert all(candidate.reasons for candidate in result.rejected_candidates)

    payload = result.to_payload()
    assert payload["selection_hash"] == result.selection_hash
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload


def test_candidate_selector_rejects_metrics_schema_failures() -> None:
    schema = ResearchMetricsSchema(
        schema_id="selection-metrics-v2",
        definitions=(
            ResearchMetricDefinition(
                path="performance.oos_sharpe",
                type="float",
                unit="ratio",
                direction="higher_is_better",
                required_for=("candidate_selection",),
            ),
        ),
    )

    result = CandidateSelector(SelectionPolicy()).select(
        (
            {
                "candidate_id": "missing-oos-sharpe",
                "metrics": {
                    "performance": {"total_return": 0.10, "max_drawdown": 0.04},
                    "trading": {"oos_trade_count": 50},
                    "costs": {"cost_sensitivity": 0.01},
                },
                "data_quality": {"accepted": True},
                "reproducibility": {"git_dirty": False},
            },
        ),
        metrics_schema=schema,
    )

    assert result.selected_candidates == ()
    assert result.rejected_candidates[0].candidate_id == "missing-oos-sharpe"
    assert result.rejected_candidates[0].reasons == (
        "metrics_schema: performance.oos_sharpe missing for candidate_selection",
    )


def test_candidate_selector_rejects_candidates_below_min_profit_factor() -> None:
    result = CandidateSelector(SelectionPolicy(min_profit_factor=1.15)).select(
        (
            _candidate(
                "low-profit-factor",
                total_return=-0.01,
                oos_sharpe=-1.2,
                max_drawdown=0.04,
                oos_trade_count=50,
                profit_factor=0.36,
            ),
        )
    )

    assert result.selected_candidates == ()
    assert result.rejected_candidates[0].candidate_id == "low-profit-factor"
    assert result.rejected_candidates[0].reasons == ("profit_factor: 0.36 below 1.15",)


def test_candidate_selector_requires_every_candidate_to_have_an_id() -> None:
    with pytest.raises(ValueError, match="candidate_id is required"):
        CandidateSelector(SelectionPolicy()).select(({"metrics": {}},))


def test_policy_reads_per_observation_statistics_over_fallbacks() -> None:
    # When the backtest publishes per-observation statistics (C2), the policy
    # consumes them directly instead of the annualized oos_sharpe / trade-count
    # fallbacks and the normal-moment defaults.
    policy = SelectionPolicy()
    metrics = {
        "performance": {
            "oos_sharpe": 9.9,
            "observed_sharpe": 0.21,
            "return_observation_count": 480,
            "return_skewness": -0.4,
            "return_kurtosis": 5.0,
            "oos_returns": [0.01, -0.02, 0.015, 0.0],
        },
        "trading": {"oos_trade_count": 7},
    }
    stats = policy.candidate_statistics("cand-1", metrics)
    assert stats.observed_sharpe == 0.21  # not the annualized oos_sharpe fallback
    assert stats.sample_size == 480  # not the oos_trade_count fallback
    assert stats.skewness == -0.4  # not the normal default of 0
    assert stats.kurtosis == 5.0  # not the normal default of 3
    assert stats.oos_returns == (0.01, -0.02, 0.015, 0.0)


def test_policy_falls_back_when_per_observation_statistics_absent() -> None:
    policy = SelectionPolicy()
    metrics = {
        "performance": {"oos_sharpe": 1.3},
        "trading": {"oos_trade_count": 42},
    }
    stats = policy.candidate_statistics("cand-1", metrics)
    assert stats.observed_sharpe == 1.3  # annualized fallback
    assert stats.sample_size == 42  # trade-count fallback
    assert stats.skewness == 0.0  # normal default
    assert stats.kurtosis == 3.0  # normal default
    assert stats.oos_returns == ()


def _candidate(
    candidate_id: str,
    *,
    total_return: float,
    oos_sharpe: float,
    max_drawdown: float,
    oos_trade_count: int,
    data_quality_accepted: bool = True,
    git_dirty: bool = False,
    profit_factor: float = 1.50,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "metrics": {
            "performance": {
                "max_drawdown": max_drawdown,
                "oos_sharpe": oos_sharpe,
                "total_return": total_return,
            },
            "quality": {"profit_factor": profit_factor},
            "trading": {"oos_trade_count": oos_trade_count},
            "costs": {"cost_sensitivity": 0.01},
        },
        "data_quality": {"accepted": data_quality_accepted},
        "reproducibility": {"git_dirty": git_dirty},
    }
