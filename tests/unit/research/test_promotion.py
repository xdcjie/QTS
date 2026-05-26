from __future__ import annotations

import pytest
from qts.research.promotion import (
    PaperReadinessChecklist,
    PromotionCandidateSpec,
    ResearchPromotionPolicy,
)


def test_promotion_candidate_requires_evidence_bundle() -> None:
    with pytest.raises(ValueError, match="evidence_bundle_id is required"):
        PromotionCandidateSpec(
            promotion_candidate_id="pc_001",
            strategy_id="vwap",
            source_module="strategies.research.vwap_factor_research",
            target_module="strategies.production.vwap_production_pullback",
            evidence_bundle_id="",
        )


def test_promotion_candidate_requires_trade_diagnostics() -> None:
    with pytest.raises(ValueError, match="trade_diagnostics_available"):
        PromotionCandidateSpec(
            promotion_candidate_id="pc_001",
            strategy_id="vwap",
            source_module="strategies.research.vwap_factor_research",
            target_module="strategies.production.vwap_production_pullback",
            evidence_bundle_id="evb_001",
            status="paper_candidate",
            paper_readiness=PaperReadinessChecklist(
                evidence_bundle_verified=True,
                trade_diagnostics_available=False,
                validation_scorecard_available=True,
                cost_stress_available=True,
                no_research_import_in_production=True,
                no_examples_direct_promotion=True,
            ),
        )


def test_paper_candidate_requires_validation_scorecard() -> None:
    with pytest.raises(ValueError, match="validation_scorecard_available"):
        PromotionCandidateSpec(
            promotion_candidate_id="pc_001",
            strategy_id="vwap",
            source_module="strategies.research.vwap_factor_research",
            target_module="strategies.production.vwap_production_pullback",
            evidence_bundle_id="evb_001",
            status="paper_candidate",
            paper_readiness=PaperReadinessChecklist(
                evidence_bundle_verified=True,
                trade_diagnostics_available=True,
                validation_scorecard_available=False,
                cost_stress_available=True,
                no_research_import_in_production=True,
                no_examples_direct_promotion=True,
            ),
        )


def test_small_live_candidate_requires_full_readiness() -> None:
    with pytest.raises(ValueError, match="small_live_candidate missing readiness item"):
        PromotionCandidateSpec(
            promotion_candidate_id="pc_001",
            strategy_id="vwap",
            source_module="strategies.research.vwap_factor_research",
            target_module="strategies.production.vwap_production_pullback",
            evidence_bundle_id="evb_001",
            status="small_live_candidate",
        )


def test_promotion_target_module_must_be_production_owned() -> None:
    with pytest.raises(ValueError, match="target_module must be production-owned"):
        PromotionCandidateSpec(
            promotion_candidate_id="pc_001",
            strategy_id="vwap",
            source_module="strategies.research.vwap_factor_research",
            target_module="strategies.research.vwap_factor_research_live",
            evidence_bundle_id="evb_001",
        )


def test_research_source_to_production_target_allowed() -> None:
    candidate = PromotionCandidateSpec(
        promotion_candidate_id="pc_001",
        strategy_id="vwap",
        source_module="strategies.research.vwap_factor_research",
        target_module="strategies.production.vwap_production_pullback",
        evidence_bundle_id="evb_001",
    )

    assert candidate.source_module.startswith("strategies.research.")
    assert candidate.target_module.startswith("strategies.production.")


def test_promotion_spec_reports_missing_items() -> None:
    candidate = PromotionCandidateSpec(
        promotion_candidate_id="pc_001",
        strategy_id="vwap",
        source_module="strategies.research.vwap_factor_research",
        target_module="strategies.production.vwap_production_pullback",
        evidence_bundle_id="evb_001",
    )

    assert candidate.missing_items() == (
        "evidence_bundle_verified",
        "trade_diagnostics_available",
        "validation_scorecard_available",
        "cost_stress_available",
        "no_research_import_in_production",
        "no_examples_direct_promotion",
    )
    assert candidate.to_payload()["missing_items"] == list(candidate.missing_items())


def test_examples_strategy_cannot_be_promotion_candidate_without_migration_review() -> None:
    with pytest.raises(ValueError, match="examples strategy requires migration review"):
        PromotionCandidateSpec(
            promotion_candidate_id="pc_001",
            strategy_id="example",
            source_module="examples.strategies.gc_si_momentum",
            target_module="strategies.production.gc_si_momentum",
            evidence_bundle_id="evb_001",
        )


def test_production_config_rejects_research_only_params() -> None:
    with pytest.raises(ValueError, match="research-only parameter"):
        PromotionCandidateSpec(
            promotion_candidate_id="pc_001",
            strategy_id="vwap",
            source_module="strategies.research.vwap_factor_research",
            target_module="strategies.production.vwap_production_pullback",
            evidence_bundle_id="evb_001",
            production_params={"trial_budget": 10},
        )


def test_research_artifact_cannot_auto_promote() -> None:
    candidate = PromotionCandidateSpec(
        promotion_candidate_id="pc_001",
        strategy_id="vwap",
        source_module="strategies.research.vwap_factor_research",
        target_module="strategies.production.vwap_production_pullback",
        evidence_bundle_id="evb_001",
    )

    assert candidate.status == "review_required"
    assert candidate.to_payload()["promotion_boundary"] == "human_review_required"


def test_promotion_gate_payload_includes_metric_metadata() -> None:
    policy = ResearchPromotionPolicy(
        min_oos_months=6,
        min_oos_trade_count=30,
        min_oos_sharpe=1.0,
        min_profit_factor=1.2,
        max_drawdown=0.25,
        max_cost_impact=0.02,
        max_slippage_sensitivity=0.03,
        min_parameter_stability=0.7,
        min_walk_forward_consistency=0.7,
        max_correlation_to_active=0.5,
    )

    decision = policy.evaluate(
        run_id="run-001",
        strategy_id="vwap",
        metrics={
            "execution": {
                "cost_impact": 0.01,
                "slippage_sensitivity": 0.02,
            },
            "portfolio": {"correlation_to_active": 0.4},
            "quality": {"profit_factor": 1.3, "sharpe": 1.1},
            "research": {
                "deterministic_replay_passed": True,
                "no_lookahead_passed": True,
            },
            "risk": {"max_drawdown": 0.1},
            "stability": {
                "parameter_sensitivity": 0.8,
                "walk_forward_consistency": 0.75,
            },
            "trading": {
                "oos_months": 12,
                "oos_trade_count": 40,
            },
        },
        reproducibility={},
    )

    payloads = {gate["name"]: gate for gate in decision.to_payload()["gates"]}

    assert payloads["max_drawdown"] == {
        "direction": "lower_is_better",
        "metric_path": "risk.max_drawdown",
        "name": "max_drawdown",
        "observed": 0.1,
        "reason": "risk.max_drawdown must be <= 0.25",
        "status": "passed",
        "threshold": 0.25,
        "unit": "ratio",
    }
