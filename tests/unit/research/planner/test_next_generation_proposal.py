"""Unit tests for autonomous research next-generation proposals."""

from __future__ import annotations

import pytest
from qts.research.landscape import FitnessAnalytics, FitnessLandscape, FitnessLandscapePoint
from qts.research.planner import (
    FamilyBudgetMutation,
    NextGenerationProposal,
    SearchSpaceMutation,
    StrategyVariantMutation,
)


def test_next_generation_proposal_is_deterministic_and_evidence_backed() -> None:
    analytics = _analytics()

    first = NextGenerationProposal.from_analytics(
        campaign_id="campaign-001",
        previous_generation_id="generation-000",
        next_generation_id="generation-001",
        analytics=analytics,
        previous_campaign_config=_previous_config(),
        trial_budget_state={"remaining_trials": 8, "requested_trials": 6},
        human_constraints={"max_trials_per_generation": 6},
    )
    second = NextGenerationProposal.from_analytics(
        campaign_id="campaign-001",
        previous_generation_id="generation-000",
        next_generation_id="generation-001",
        analytics=analytics,
        previous_campaign_config=_previous_config(),
        trial_budget_state={"remaining_trials": 8, "requested_trials": 6},
        human_constraints={"max_trials_per_generation": 6},
    )

    assert first.to_payload() == second.to_payload()
    assert first.proposal_hash == second.proposal_hash
    assert first.trial_budget == 6
    assert {type(mutation) for mutation in first.mutations} >= {
        SearchSpaceMutation,
        FamilyBudgetMutation,
        StrategyVariantMutation,
    }
    assert all(mutation.reason for mutation in first.mutations)
    assert all(mutation.evidence_refs for mutation in first.mutations)


def test_next_generation_proposal_rejects_budget_overrun() -> None:
    analytics = _analytics()

    with pytest.raises(ValueError, match="proposal trial budget exceeds"):
        NextGenerationProposal.from_analytics(
            campaign_id="campaign-001",
            previous_generation_id="generation-000",
            next_generation_id="generation-001",
            analytics=analytics,
            previous_campaign_config=_previous_config(),
            trial_budget_state={"remaining_trials": 12, "requested_trials": 10},
            human_constraints={"max_trials_per_generation": 6},
        )


def test_next_generation_proposal_rejects_silent_data_window_changes() -> None:
    mutation = SearchSpaceMutation(
        mutation_id="search-space-001",
        target="momentum.alpha",
        action="narrow_range",
        payload={"min": 0.2, "max": 0.5},
        reason="stable accepted parameter region",
        evidence_refs=("sha256:analytics",),
    )

    with pytest.raises(ValueError, match="data window change requires explicit mutation"):
        NextGenerationProposal(
            proposal_id="proposal-001",
            campaign_id="campaign-001",
            previous_generation_id="generation-000",
            next_generation_id="generation-001",
            previous_data_window={"start": "2025-01-01", "end": "2025-12-31"},
            proposed_data_window={"start": "2024-01-01", "end": "2025-12-31"},
            trial_budget=4,
            max_trial_budget=6,
            mutations=(mutation,),
        )


def _analytics() -> FitnessAnalytics:
    return FitnessAnalytics.from_landscape(
        FitnessLandscape(
            (
                _point(
                    "trial-001",
                    strategy_family="momentum",
                    accepted=True,
                    train_sharpe=1.1,
                    oos_sharpe=1.0,
                    max_drawdown=0.06,
                    cost_sensitivity=0.02,
                ),
                _point(
                    "trial-002",
                    strategy_family="breakout",
                    accepted=False,
                    train_sharpe=2.2,
                    oos_sharpe=0.1,
                    max_drawdown=0.31,
                    rejected_reasons=("max_drawdown",),
                ),
                _point(
                    "trial-003",
                    strategy_family="mean_reversion",
                    accepted=False,
                    train_sharpe=1.4,
                    oos_sharpe=0.2,
                    max_drawdown=0.12,
                    cost_sensitivity=0.35,
                    rejected_reasons=("cost_stress",),
                ),
            )
        )
    )


def _previous_config() -> dict[str, object]:
    return {
        "data_window": {"start": "2025-01-01", "end": "2025-12-31"},
        "trial_budget": 20,
    }


def _point(
    trial_id: str,
    *,
    strategy_family: str,
    accepted: bool,
    train_sharpe: float,
    oos_sharpe: float,
    max_drawdown: float,
    cost_sensitivity: float = 0.03,
    rejected_reasons: tuple[str, ...] = (),
) -> FitnessLandscapePoint:
    return FitnessLandscapePoint(
        trial_id=trial_id,
        retry_id=None,
        campaign_id="campaign-001",
        generation_id="generation-000",
        strategy_family=strategy_family,
        factor_family="carry",
        universe=("metals",),
        root="GC",
        timeframe="1h",
        regime="trend",
        session="rth",
        parameter_hash=f"sha256:{trial_id}",
        metrics={
            "performance": {
                "max_drawdown": max_drawdown,
                "oos_sharpe": oos_sharpe,
                "train_sharpe": train_sharpe,
            },
            "costs": {"cost_sensitivity": cost_sensitivity},
        },
        constraints={"max_drawdown": 0.2},
        accepted=accepted,
        rejected_reasons=rejected_reasons,
        evidence_bundle_id=f"evidence-{trial_id}",
        promotion_packet_id=f"packet-{trial_id}" if accepted else None,
        artifact_graph_hash=f"sha256:artifact-{trial_id}",
    )
