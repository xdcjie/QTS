from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from qts.research.idea_spec import IdeaSpec
from qts.research.meta_research import MetaResearchSummary, MetaResearchSummaryWriter


def _idea(
    idea_id: str,
    *,
    source: str,
    edge_type: str,
    edge_types: tuple[str, ...] = (),
    created_at: datetime = datetime(2026, 5, 5, tzinfo=UTC),
    status: str = "draft",
    trial_count: int = 0,
    rejection_reason: str | None = None,
) -> IdeaSpec:
    return IdeaSpec(
        idea_id=idea_id,
        title=f"{idea_id} title",
        hypothesis=f"{idea_id} hypothesis",
        edge_type=edge_type,
        edge_types=edge_types,
        source=source,
        created_at=created_at,
        status=status,
        trial_count=trial_count,
        rejection_reason=rejection_reason,
    )


def test_meta_research_summary_from_idea_evidence_experiment_registry(
    tmp_path: Path,
) -> None:
    ideas = (
        _idea("idea-momentum", source="openalex", edge_type="momentum", trial_count=4),
        _idea(
            "idea-carry",
            source="semantic_scholar",
            edge_type="carry",
            status="rejected",
            rejection_reason="failed_validation",
        ),
        _idea("idea-value", source="openalex", edge_type="value", status="paper_candidate"),
    )
    evidence = (
        {"idea_id": "idea-momentum", "kind": "factor_candidate", "accepted": True},
        {"idea_id": "idea-carry", "kind": "factor_candidate", "accepted": False},
        {"idea_id": "idea-value", "kind": "strategy_prototype", "accepted": True},
    )
    experiments = (
        {"idea_id": "idea-momentum", "experiment_id": "exp-001", "accepted": True},
        {"idea_id": "idea-carry", "experiment_id": "exp-002", "accepted": False},
    )

    summary = MetaResearchSummary.from_registries(
        ideas=ideas,
        evidence_records=evidence,
        experiment_records=experiments,
        period="monthly",
        period_start=date(2026, 5, 1),
        trial_count_outlier_threshold=3,
    )
    artifacts = MetaResearchSummaryWriter().write(tmp_path, summary)

    assert summary.to_payload() == {
        "edge_type_distribution": {"carry": 1, "momentum": 1, "value": 1},
        "factor_candidates": 2,
        "ideas_created": 3,
        "paper_candidate_count": 1,
        "period": "monthly",
        "period_start": "2026-05-01",
        "rejected_reason_distribution": {"failed_validation": 1},
        "source_success_rate": {
            "openalex": {"accepted": 2, "rate": 1.0, "total": 2},
            "semantic_scholar": {"accepted": 0, "rate": 0.0, "total": 1},
        },
        "strategy_prototypes": 1,
        "trial_count_outliers": [
            {"idea_id": "idea-momentum", "trial_count": 4},
        ],
        "validation_pass_rate": {"accepted": 3, "rate": 0.6, "total": 5},
    }
    assert json.loads(artifacts.json_path.read_text(encoding="utf-8")) == summary.to_payload()
    assert artifacts.markdown_path.read_text(encoding="utf-8").startswith(
        "# Meta-Research Summary\n\n- period: monthly\n- period_start: 2026-05-01\n"
    )


def test_meta_research_groups_by_source_and_edge_type() -> None:
    summary = MetaResearchSummary.from_registries(
        ideas=(
            _idea("idea-1", source="openalex", edge_type="momentum", status="paper_candidate"),
            _idea("idea-2", source="openalex", edge_type="momentum", status="rejected"),
            _idea("idea-3", source="fixture", edge_type="carry", status="paper_candidate"),
        ),
        evidence_records=(),
        experiment_records=(),
        period="quarterly",
        period_start=date(2026, 4, 1),
    )

    assert summary.edge_type_distribution == {"carry": 1, "momentum": 2}
    assert summary.source_success_rate == {
        "fixture": {"accepted": 1, "rate": 1.0, "total": 1},
        "openalex": {"accepted": 1, "rate": 0.5, "total": 2},
    }


def test_meta_research_counts_all_idea_edge_types() -> None:
    summary = MetaResearchSummary.from_registries(
        ideas=(
            _idea(
                "idea-1",
                source="openalex",
                edge_type="carry",
                edge_types=("carry", "term_structure"),
            ),
        ),
        evidence_records=(),
        experiment_records=(),
        period="monthly",
        period_start=date(2026, 5, 1),
    )

    assert summary.edge_type_distribution == {"carry": 1, "term_structure": 1}


def test_meta_research_filters_ideas_by_created_at_month() -> None:
    summary = MetaResearchSummary.from_registries(
        ideas=(
            _idea(
                "idea-current",
                source="openalex",
                edge_type="carry",
                created_at=datetime(2026, 5, 15, tzinfo=UTC),
            ),
            _idea(
                "idea-old",
                source="openalex",
                edge_type="carry",
                created_at=datetime(2026, 4, 30, 23, 59, tzinfo=UTC),
            ),
        ),
        evidence_records=(),
        experiment_records=(),
        period="monthly",
        period_start=date(2026, 5, 1),
    )

    assert summary.ideas_created == 1


def test_meta_research_filters_experiment_records_by_recorded_at() -> None:
    summary = MetaResearchSummary.from_registries(
        ideas=(),
        evidence_records=(),
        experiment_records=(
            {"accepted": True, "recorded_at": "2026-05-31T23:59:59+00:00"},
            {"accepted": True, "recorded_at": "2026-06-01T00:00:00+00:00"},
        ),
        period="monthly",
        period_start=date(2026, 5, 1),
    )

    assert summary.validation_pass_rate == {"accepted": 1, "rate": 1.0, "total": 1}


def test_meta_research_filters_evidence_review_decisions_by_time() -> None:
    summary = MetaResearchSummary.from_registries(
        ideas=(),
        evidence_records=(
            {"accepted": True, "reviewed_at": "2026-05-02T00:00:00+00:00"},
            {"accepted": True, "reviewed_at": "2026-06-02T00:00:00+00:00"},
        ),
        experiment_records=(),
        period="monthly",
        period_start=date(2026, 5, 1),
    )

    assert summary.validation_pass_rate == {"accepted": 1, "rate": 1.0, "total": 1}


def test_meta_research_evidence_bundle_record_ignores_legacy_review_decisions() -> None:
    class LegacyBundle:
        evidence_bundle_id = "evb-001"
        idea_id = "idea-001"
        strategy_id = "strategy-001"
        workflow_run_id = "workflow-001"
        review_decisions = (
            {
                "status": "paper_candidate",
                "reason": "strong evidence",
                "reviewed_at": "2026-05-02T00:00:00+00:00",
            },
        )

    records = MetaResearchSummary.evidence_records_from_registry(
        type(
            "Registry",
            (),
            {"list": lambda self: (LegacyBundle(),)},
        )()
    )

    assert records == (
        {
            "evidence_bundle_id": "evb-001",
            "idea_id": "idea-001",
            "kind": "strategy_prototype",
            "strategy_id": "strategy-001",
            "workflow_run_id": "workflow-001",
        },
    )


def test_meta_research_custom_period() -> None:
    summary = MetaResearchSummary.from_registries(
        ideas=(
            _idea(
                "idea-in",
                source="openalex",
                edge_type="carry",
                created_at=datetime(2026, 5, 10, tzinfo=UTC),
            ),
            _idea(
                "idea-out",
                source="openalex",
                edge_type="carry",
                created_at=datetime(2026, 5, 20, tzinfo=UTC),
            ),
        ),
        evidence_records=(),
        experiment_records=(),
        period="custom",
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 15),
    )

    assert summary.ideas_created == 1


def test_meta_research_flags_high_trial_count_candidates() -> None:
    summary = MetaResearchSummary.from_registries(
        ideas=(
            _idea("idea-small", source="openalex", edge_type="momentum", trial_count=2),
            _idea("idea-large", source="openalex", edge_type="momentum", trial_count=5),
        ),
        evidence_records=(),
        experiment_records=(),
        period="monthly",
        period_start=date(2026, 5, 1),
        trial_count_outlier_threshold=4,
    )

    assert summary.trial_count_outliers == ({"idea_id": "idea-large", "trial_count": 5},)
