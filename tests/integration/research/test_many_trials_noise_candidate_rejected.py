"""Integration: many trials reject a noise candidate via the adjusted score.

When a large family of noise strategies is tried, the best raw Sharpe inflates by
chance. This test drives a noise candidate (high raw Sharpe, no genuine edge)
through ``CandidateSelector`` and a multiplicity-aware ``ValidationGauntlet``:

* with few trials the candidate's Deflated Sharpe clears the gate,
* with many trials the same candidate is rejected by the ``DeflatedSharpeGate``
  acting on the selector's adjusted score.

This exercises the wiring required by the plan: trial count threaded into
selection, ``adjusted_score`` recorded on the selection result, and promotion
gated on the adjusted statistic.
"""

from __future__ import annotations

import math
import random

from qts.research.selector import (
    CandidateSelector,
    DeflatedSharpeGate,
    PBOGate,
    SelectionPolicy,
    ValidationGauntlet,
)


def _noise_candidate(candidate_id: str, observed_sharpe: float, sample_size: int) -> dict:
    # A noise candidate: a positive observed Sharpe drawn by luck, no validation
    # edge. Annualized oos_sharpe is reported alongside the per-observation Sharpe.
    return {
        "candidate_id": candidate_id,
        "metrics": {
            "performance": {
                "max_drawdown": 0.10,
                "observed_sharpe": observed_sharpe,
                "oos_sharpe": observed_sharpe * math.sqrt(252.0),
                "return_observation_count": sample_size,
                "return_skewness": 0.0,
                "return_kurtosis": 3.0,
                "total_return": 0.15,
            },
            "trading": {"oos_trade_count": sample_size},
            "costs": {"cost_sensitivity": 0.01},
        },
        "data_quality": {"accepted": True},
        "reproducibility": {"git_dirty": False},
    }


def _gauntlet() -> ValidationGauntlet:
    # Multiplicity-aware gauntlet: DeflatedSharpeGate enforces the adjusted score.
    return ValidationGauntlet(
        deflated_sharpe_gate=DeflatedSharpeGate(min_deflated_sharpe_ratio=0.95),
        pbo_gate=PBOGate(max_pbo=0.50),
    )


def _select_and_gate(candidates: tuple[dict, ...], *, trial_count: int):
    policy = SelectionPolicy(min_oos_trade_count=20, max_drawdown=0.30)
    selection = CandidateSelector(policy).select(candidates, trial_count=trial_count)
    gauntlet = _gauntlet()
    decisions = {}
    for selected in selection.selected_candidates:
        decision = gauntlet.deflated_sharpe_gate.evaluate(
            {
                "candidate_id": selected.candidate_id,
                "multiplicity_adjustment": dict(selected.multiplicity_adjustment or {}),
            }
        )
        decisions[selected.candidate_id] = (selected, decision)
    return selection, decisions


def test_many_trials_reject_noise_candidate_via_adjusted_score() -> None:
    # Build a family of noise candidates; the "winner" has the highest raw Sharpe
    # purely by chance. The cross-trial Sharpe dispersion drives the deflation.
    rng = random.Random(20260530)
    sample_size = 252
    family = tuple(
        _noise_candidate(
            f"noise-{index:03d}",
            observed_sharpe=abs(rng.gauss(0.0, 0.06)),
            sample_size=sample_size,
        )
        for index in range(40)
    )
    # Inject one lucky high-raw-Sharpe candidate.
    lucky = _noise_candidate("lucky-winner", observed_sharpe=0.18, sample_size=sample_size)
    candidates = (lucky, *family)

    # Few trials: the lucky candidate's deflated Sharpe still clears the gate.
    few_selection, few_decisions = _select_and_gate(candidates, trial_count=1)
    lucky_few, lucky_few_decision = few_decisions["lucky-winner"]
    assert lucky_few_decision.accepted is True

    # Many trials: the same candidate is now rejected by the adjusted-score gate.
    many_selection, many_decisions = _select_and_gate(candidates, trial_count=2000)
    lucky_many, lucky_many_decision = many_decisions["lucky-winner"]
    assert lucky_many_decision.accepted is False
    assert any("deflated_sharpe_ratio" in reason for reason in lucky_many_decision.reasons)

    # Acceptance criteria: raw Sharpe identical, deflated Sharpe collapses with N,
    # and both raw and adjusted scores are recorded on the selection result.
    assert lucky_few.raw_score == lucky_many.raw_score
    assert lucky_many.adjusted_score < lucky_few.adjusted_score
    assert lucky_few.multiplicity_adjustment is not None
    assert lucky_many.multiplicity_adjustment is not None
    assert (
        lucky_many.multiplicity_adjustment["deflated_sharpe_ratio"]
        < lucky_few.multiplicity_adjustment["deflated_sharpe_ratio"]
    )
    assert lucky_few.multiplicity_adjustment["trial_count"] == 1
    assert lucky_many.multiplicity_adjustment["trial_count"] == 2000


def test_increasing_trials_raises_acceptance_threshold() -> None:
    # Holding the candidate fixed, raising the trial count lowers its deflated
    # Sharpe monotonically: more trials => harder to pass.
    candidates = (
        _noise_candidate("a", observed_sharpe=0.12, sample_size=252),
        _noise_candidate("b", observed_sharpe=0.08, sample_size=252),
        _noise_candidate("c", observed_sharpe=0.04, sample_size=252),
    )
    deflated_by_trials = []
    for trial_count in (1, 10, 100, 1000):
        selection = CandidateSelector(
            SelectionPolicy(min_oos_trade_count=20, max_drawdown=0.30)
        ).select(candidates, trial_count=trial_count)
        winner = next(c for c in selection.selected_candidates if c.candidate_id == "a")
        assert winner.multiplicity_adjustment is not None
        deflated_by_trials.append(winner.multiplicity_adjustment["deflated_sharpe_ratio"])
    assert deflated_by_trials == sorted(deflated_by_trials, reverse=True)
    assert deflated_by_trials[0] > deflated_by_trials[-1]
