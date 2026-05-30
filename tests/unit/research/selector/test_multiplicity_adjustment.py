"""Unit tests for the research multiplicity / overfitting correction.

Anchor values are computed from the cited formulas:

* Expected maximum Sharpe (Bailey & Lopez de Prado 2014, eq. 5),
* Probabilistic / Deflated Sharpe Ratio (Bailey & Lopez de Prado 2012, 2014),
* PBO via CSCV (Bailey, Borwein, Lopez de Prado & Zhu 2017),
* Benjamini-Hochberg FDR (Benjamini & Hochberg 1995).
"""

from __future__ import annotations

import math

import pytest
from qts.research.selector import (
    CandidateSelector,
    CandidateStatistics,
    DeflatedSharpeGate,
    MultiplicityAdjustmentResult,
    PBOGate,
    ResearchMultiplicityAdjustment,
    SelectionPolicy,
)
from qts.research.selector.multiplicity_adjustment import (
    benjamini_hochberg_discoveries,
    deflated_sharpe_ratio,
    expected_maximum_sharpe,
    probabilistic_sharpe_ratio,
    probability_of_backtest_overfitting,
)


def test_expected_maximum_sharpe_grows_with_trial_count() -> None:
    # Bailey & Lopez de Prado (2014) eq. (5) with sigma_SR = 0.05.
    # N = 1 carries no multiplicity inflation, so E[max] = 0.
    assert expected_maximum_sharpe(1, 0.05) == 0.0
    e10 = expected_maximum_sharpe(10, 0.05)
    e100 = expected_maximum_sharpe(100, 0.05)
    e1000 = expected_maximum_sharpe(1000, 0.05)
    assert e10 == pytest.approx(0.078730, abs=1e-5)
    assert e100 == pytest.approx(0.126530, abs=1e-5)
    assert e1000 == pytest.approx(0.162756, abs=1e-5)
    assert e10 < e100 < e1000


def test_deflated_sharpe_decreases_monotonically_with_trial_count() -> None:
    # SR_hat = 0.10, n = 252, normal moments, sigma_SR = 0.05.
    # DSR = PSR(E[max_N]); the benchmark grows with N so DSR strictly falls.
    def dsr(trial_count: int) -> float:
        return deflated_sharpe_ratio(
            observed_sharpe=0.10,
            sample_size=252,
            skewness=0.0,
            kurtosis=3.0,
            trial_count=trial_count,
            trial_sharpe_std=0.05,
        )

    d1 = dsr(1)
    d10 = dsr(10)
    d100 = dsr(100)
    d1000 = dsr(1000)
    assert d1 == pytest.approx(0.942987, abs=1e-5)
    assert d10 == pytest.approx(0.631618, abs=1e-5)
    assert d100 == pytest.approx(0.337510, abs=1e-5)
    assert d1000 == pytest.approx(0.160656, abs=1e-5)
    assert d1 > d10 > d100 > d1000


def test_deflated_sharpe_equals_psr_at_single_trial() -> None:
    # With N = 1 the deflation benchmark is 0, so DSR == PSR(SR0 = 0).
    psr = probabilistic_sharpe_ratio(
        observed_sharpe=0.10, sample_size=252, skewness=0.0, kurtosis=3.0
    )
    dsr = deflated_sharpe_ratio(
        observed_sharpe=0.10,
        sample_size=252,
        skewness=0.0,
        kurtosis=3.0,
        trial_count=1,
        trial_sharpe_std=0.05,
    )
    assert dsr == pytest.approx(psr, abs=1e-12)


def test_probabilistic_sharpe_ratio_rises_with_sample_size() -> None:
    # A longer track record makes a positive Sharpe more probably real.
    short = probabilistic_sharpe_ratio(
        observed_sharpe=0.10, sample_size=30, skewness=0.0, kurtosis=3.0
    )
    long = probabilistic_sharpe_ratio(
        observed_sharpe=0.10, sample_size=1000, skewness=0.0, kurtosis=3.0
    )
    assert 0.0 < short < long < 1.0


def test_negative_skew_and_fat_tails_lower_psr() -> None:
    # Negative skew and excess kurtosis inflate the Sharpe estimator variance,
    # lowering the probability the Sharpe is real.
    normal = probabilistic_sharpe_ratio(
        observed_sharpe=0.10, sample_size=252, skewness=0.0, kurtosis=3.0
    )
    fat_tailed = probabilistic_sharpe_ratio(
        observed_sharpe=0.10, sample_size=252, skewness=-1.0, kurtosis=8.0
    )
    assert fat_tailed < normal


def test_pbo_high_for_overfit_low_for_genuine() -> None:
    # CSCV (Bailey et al. 2017). Overfit config is high in the first half of the
    # series and low in the second; the in-sample winner flips to the out-of-sample
    # loser across symmetric splits, driving PBO up.
    overfit = [[3.0 if row < 8 else -3.0, 0.1] for row in range(16)]
    genuine = [[1.0, 0.0] for _ in range(16)]
    assert probability_of_backtest_overfitting(overfit, block_count=8) == pytest.approx(
        0.485714, abs=1e-5
    )
    assert probability_of_backtest_overfitting(genuine, block_count=8) == 0.0


def test_pbo_requires_two_configurations() -> None:
    single = [[1.0] for _ in range(16)]
    assert probability_of_backtest_overfitting(single, block_count=8) == 0.0


def test_benjamini_hochberg_controls_false_discovery_rate() -> None:
    # BH step-up at q = 0.10 over four candidates: only the two smallest p-values
    # satisfy p_(k) <= (k/m) * q.
    assert benjamini_hochberg_discoveries([0.001, 0.01, 0.2, 0.5], false_discovery_rate=0.10) == (
        0,
        1,
    )
    assert benjamini_hochberg_discoveries([0.9, 0.95, 0.99], false_discovery_rate=0.10) == ()


def test_adjustment_result_carries_raw_and_adjusted_score() -> None:
    candidates = [
        CandidateStatistics(
            candidate_id=f"c{index}",
            raw_score=1.0,
            observed_sharpe=0.05 + 0.02 * index,
            sample_size=252,
        )
        for index in range(5)
    ]
    results = ResearchMultiplicityAdjustment(trial_count=100).adjust(candidates)
    assert len(results) == 5
    first = results[0]
    assert isinstance(first, MultiplicityAdjustmentResult)
    assert first.raw_score == 1.0
    # The trial-count haircut lowers every adjusted score below the raw score.
    assert first.adjusted_score < first.raw_score
    payload = first.to_payload()
    assert payload["raw_score"] == first.raw_score
    assert payload["adjusted_score"] == first.adjusted_score
    assert "deflated_sharpe_ratio" in payload
    assert "probability_of_backtest_overfitting" in payload


def test_more_trials_lower_every_adjusted_score() -> None:
    candidates = [
        CandidateStatistics(
            candidate_id=f"c{index}",
            raw_score=1.0,
            observed_sharpe=0.05 + 0.02 * index,
            sample_size=252,
        )
        for index in range(5)
    ]
    few = {
        r.candidate_id: r for r in ResearchMultiplicityAdjustment(trial_count=2).adjust(candidates)
    }
    many = {
        r.candidate_id: r
        for r in ResearchMultiplicityAdjustment(trial_count=500).adjust(candidates)
    }
    for candidate_id in few:
        assert many[candidate_id].adjusted_score < few[candidate_id].adjusted_score
        assert many[candidate_id].deflated_sharpe_ratio < few[candidate_id].deflated_sharpe_ratio


def test_deflated_sharpe_gate_rejects_high_raw_low_deflated() -> None:
    # A candidate with a high raw Sharpe but a poor deflated Sharpe under many
    # trials must fail the gate.
    high_raw_low_deflated = {
        "candidate_id": "lucky",
        "multiplicity_adjustment": {
            "observed_sharpe": 0.10,
            "deflated_sharpe_ratio": 0.16,
            "expected_maximum_sharpe": 0.16,
            "trial_count": 1000,
        },
    }
    genuine = {
        "candidate_id": "genuine",
        "multiplicity_adjustment": {
            "observed_sharpe": 0.10,
            "deflated_sharpe_ratio": 0.96,
            "expected_maximum_sharpe": 0.0,
            "trial_count": 1,
        },
    }
    gate = DeflatedSharpeGate(min_deflated_sharpe_ratio=0.95)
    rejected = gate.evaluate(high_raw_low_deflated)
    accepted = gate.evaluate(genuine)
    assert rejected.accepted is False
    assert any("deflated_sharpe_ratio" in reason for reason in rejected.reasons)
    assert accepted.accepted is True


def test_deflated_sharpe_gate_requires_evidence() -> None:
    decision = DeflatedSharpeGate().evaluate({"candidate_id": "no-evidence"})
    assert decision.accepted is False
    assert decision.reasons == ("deflated_sharpe: multiplicity adjustment evidence missing",)


def test_pbo_gate_rejects_overfit_candidate() -> None:
    overfit = {
        "candidate_id": "overfit",
        "multiplicity_adjustment": {"probability_of_backtest_overfitting": 0.85},
    }
    robust = {
        "candidate_id": "robust",
        "multiplicity_adjustment": {"probability_of_backtest_overfitting": 0.05},
    }
    gate = PBOGate(max_pbo=0.50)
    assert gate.evaluate(overfit).accepted is False
    assert gate.evaluate(robust).accepted is True


def test_selector_ranks_on_adjusted_score_and_records_both() -> None:
    # Two survivors with identical raw composites but different Sharpes: under a
    # large trial count the higher-Sharpe candidate keeps a higher adjusted score.
    policy = SelectionPolicy(min_oos_trade_count=20, max_drawdown=0.30)
    result = CandidateSelector(policy).select(
        (
            _candidate("steady", oos_sharpe=1.8, oos_trade_count=200),
            _candidate("volatile", oos_sharpe=1.2, oos_trade_count=200),
        ),
        trial_count=50,
    )
    selected = {c.candidate_id: c for c in result.selected_candidates}
    assert set(selected) == {"steady", "volatile"}
    for candidate in result.selected_candidates:
        assert candidate.raw_score is not None
        assert candidate.adjusted_score is not None
        # The trial-count haircut is identical for the family, so adjusted < raw.
        assert candidate.adjusted_score < candidate.raw_score
        assert candidate.multiplicity_adjustment is not None
        assert candidate.multiplicity_adjustment["trial_count"] == 50
        payload = candidate.to_payload()
        assert payload["raw_score"] == candidate.raw_score
        assert payload["adjusted_score"] == candidate.adjusted_score
    # Ranking follows the adjusted score (higher Sharpe ranks first).
    ranked = sorted(result.selected_candidates, key=lambda c: c.selected_rank)
    assert ranked[0].candidate_id == "steady"


def test_selector_default_trial_count_leaves_score_unadjusted() -> None:
    # With the default trial_count = 1 there is no multiplicity inflation, so the
    # adjusted score equals the raw composite (backward-compatible ranking).
    policy = SelectionPolicy(min_oos_trade_count=20, max_drawdown=0.30)
    result = CandidateSelector(policy).select(
        (_candidate("only", oos_sharpe=1.5, oos_trade_count=200),),
    )
    candidate = result.selected_candidates[0]
    assert candidate.adjusted_score == pytest.approx(candidate.raw_score)
    assert candidate.adjusted_score == pytest.approx(candidate.composite_score)


def _candidate(
    candidate_id: str,
    *,
    oos_sharpe: float,
    oos_trade_count: int,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "metrics": {
            "performance": {
                "max_drawdown": 0.08,
                "observed_sharpe": oos_sharpe / math.sqrt(252.0),
                "oos_sharpe": oos_sharpe,
                "return_observation_count": oos_trade_count,
                "total_return": 0.20,
            },
            "trading": {"oos_trade_count": oos_trade_count},
            "costs": {"cost_sensitivity": 0.01},
        },
        "data_quality": {"accepted": True},
        "reproducibility": {"git_dirty": False},
    }
