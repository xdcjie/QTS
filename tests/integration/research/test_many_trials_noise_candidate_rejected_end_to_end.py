"""End-to-end: a lucky noise candidate is rejected by the full gauntlet under many trials.

This drives the same wiring the autonomous engine uses -- ``CandidateSelector.select``
records each survivor's multiplicity adjustment, the adjustment is attached to the
candidate payload, and a multiplicity-aware ``ValidationGauntlet.validate`` runs every
gate. A high-raw-Sharpe noise candidate that clears every gate with a single trial is
rejected by the ``DeflatedSharpeGate`` once the family's trial count is large: the
expected-maximum-Sharpe haircut deflates its Sharpe below the gate threshold while every
other gate's evidence is held fixed, proving the multiplicity correction is the deciding
factor on the real validation path (not an isolated gate call).
"""

from __future__ import annotations

import math
import random
from typing import Any

from qts.research.selector import (
    CandidateSelector,
    DeflatedSharpeGate,
    PBOGate,
    SelectionPolicy,
    SelectionResult,
    ValidationGauntlet,
)


def test_lucky_noise_candidate_rejected_end_to_end_under_many_trials() -> None:
    rng = random.Random(20260530)
    sample_size = 252
    # A family of noise strategies: positive Sharpe drawn by luck, no real edge.
    family = [
        _noise_candidate(
            f"noise-{index:03d}",
            observed_sharpe=abs(rng.gauss(0.0, 0.06)),
            sample_size=sample_size,
        )
        for index in range(40)
    ]
    # The lucky winner: highest raw Sharpe, and the only candidate carrying the full
    # validation evidence so every non-multiplicity gate passes.
    lucky = _noise_candidate("lucky-winner", observed_sharpe=0.18, sample_size=sample_size)
    lucky["validation"] = _passing_validation()
    candidates = (lucky, *family)

    few = _validate_end_to_end(candidates, trial_count=1)
    many = _validate_end_to_end(candidates, trial_count=2000)

    # With a single trial the winner clears the full gauntlet end to end.
    assert few["selected"], "lucky-winner should survive selection at N=1"
    assert few["accepted"] is True
    assert few["reasons"] == ()

    # With many trials the same candidate -- identical raw Sharpe and identical
    # walk-forward / cost / correlation / capacity / no-lookahead evidence -- is now
    # rejected, and the rejection is attributable to the multiplicity correction.
    assert many["selected"], "lucky-winner should still survive selection at N=2000"
    assert many["accepted"] is False
    assert any("deflated_sharpe" in reason for reason in many["reasons"])

    # The raw objective is unchanged; only the deflated Sharpe collapses with N.
    assert few["raw_score"] == many["raw_score"]
    assert many["deflated_sharpe_ratio"] < few["deflated_sharpe_ratio"]
    assert many["trial_count"] == 2000
    assert few["trial_count"] == 1


def _validate_end_to_end(
    candidates: tuple[dict[str, Any], ...], *, trial_count: int
) -> dict[str, Any]:
    selection: SelectionResult = CandidateSelector(
        SelectionPolicy(min_oos_trade_count=20, max_drawdown=0.30, max_selected=1)
    ).select(candidates, trial_count=trial_count, multiplicity_scope="generation")

    assert selection.trial_count == trial_count
    winner = next(
        (c for c in selection.selected_candidates if c.candidate_id == "lucky-winner"),
        None,
    )
    if winner is None:
        return {"selected": False, "trial_count": selection.trial_count}

    assert winner.multiplicity_adjustment is not None
    # Attach the selector's multiplicity adjustment to the candidate payload exactly
    # as the engine does before running the multiplicity-aware gauntlet.
    candidate_payload = {
        **dict(winner.candidate_payload),
        "multiplicity_adjustment": dict(winner.multiplicity_adjustment),
    }
    result = _gauntlet().validate(candidate_payload)
    return {
        "selected": True,
        "accepted": result.accepted,
        "reasons": result.reasons,
        "raw_score": winner.raw_score,
        "deflated_sharpe_ratio": winner.multiplicity_adjustment["deflated_sharpe_ratio"],
        "trial_count": selection.trial_count,
    }


def _gauntlet() -> ValidationGauntlet:
    # The multiplicity-aware gauntlet the autonomous engine constructs: the deflated
    # Sharpe and PBO gates read the selector's recorded adjustment.
    return ValidationGauntlet(
        deflated_sharpe_gate=DeflatedSharpeGate(min_deflated_sharpe_ratio=0.95),
        pbo_gate=PBOGate(max_pbo=0.50),
    )


def _noise_candidate(
    candidate_id: str, *, observed_sharpe: float, sample_size: int
) -> dict[str, Any]:
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


def _passing_validation() -> dict[str, Any]:
    # Full validation evidence so every gate except the multiplicity gates passes;
    # this isolates the multiplicity correction as the deciding factor.
    return {
        "walk_forward": {
            "consistent": True,
            "test_windows": (
                {"name": "split-001", "accepted": True, "score": 1.10},
                {"name": "split-002", "accepted": True, "score": 0.90},
            ),
            "max_train_test_gap": 0.30,
        },
        "failure_windows": (
            {"name": "crisis", "max_drawdown": 0.12},
            {"name": "rebound", "max_drawdown": 0.08, "report_only": True},
        ),
        "cost_stress": {
            "degradation": 0.12,
            "slippage_sensitivity": 0.05,
            "stressed_score": 0.84,
        },
        "correlation": {
            "active_portfolio_snapshot": {
                "active_candidate_count": 1,
                "active_portfolio_status": "computed",
                "candidate_return_count": 2,
            },
            "max_active_correlation": 0.42,
        },
        "capacity": {
            "estimated_capacity": 1_000_000,
            "required_capital": 500_000,
            "turnover": 1.8,
        },
        "deterministic_replay": {"passed": True, "evidence_id": "replay-001"},
        "no_lookahead": {
            "passed": True,
            "evidence_id": "lookahead-001",
            "string_scan_only": False,
            "violations": [],
            "timing_validation": {
                "passed": True,
                "checked_features": ["momentum_10"],
                "violations": [],
                "window_overlaps": [],
            },
        },
    }
