from __future__ import annotations

import pytest
from qts.research.promotion import PaperReadinessChecklist, PromotionCandidateSpec


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
