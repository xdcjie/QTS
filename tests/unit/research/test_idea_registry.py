from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.research.idea_registry import (
    IdeaRegistry,
    trial_budget_warning,
    validate_promotion_candidate,
)
from qts.research.idea_spec import IdeaSpec


def _idea(
    idea_id: str = "idea-momentum",
    *,
    hypothesis: str = "Momentum edge persists after session-aware transaction costs.",
    edge_type: str = "momentum",
    source: str = "openalex",
    trial_count: int = 0,
) -> IdeaSpec:
    return IdeaSpec(
        idea_id=idea_id,
        title=f"{idea_id} title",
        hypothesis=hypothesis,
        edge_type=edge_type,
        source=source,
        created_at=datetime(2026, 5, 20, 12, 30, tzinfo=UTC),
        data_required=("GC 15m OHLCV", "session VWAP"),
        kill_criteria=("oos_net_sharpe_below_0_8",),
        trial_budget={"max_strategy_trials": 3, "max_validation_variants": 2},
        trial_count=trial_count,
    )


def test_idea_registry_requires_hypothesis(tmp_path: Path) -> None:
    registry = IdeaRegistry(tmp_path)
    registry.save_idea(_idea(hypothesis="paper abstract only"))

    with pytest.raises(ValueError, match="hypothesis is required"):
        registry.save_idea(_idea("idea-no-hypothesis", hypothesis=" "))

    registry.save_idea(_idea("idea-draft", hypothesis="draft hypothesis"))
    with pytest.raises(ValueError, match="hypothesis is required"):
        registry.record_review_decision(
            "idea-draft",
            decision="promotion_review",
            hypothesis=" ",
            reviewer="researcher@example.com",
            reviewed_at=datetime(2026, 5, 21, tzinfo=UTC),
        )


def test_idea_registry_rejects_unknown_edge_type() -> None:
    with pytest.raises(ValueError, match="edge_type"):
        _idea(edge_type="moon-phase")


def test_idea_spec_accepts_multiple_edge_types() -> None:
    idea = IdeaSpec(
        idea_id="idea-multi",
        title="multi edge",
        hypothesis="Term structure and carry effects can persist after costs.",
        edge_type="carry",
        edge_types=("carry", "term_structure"),
        source="openalex",
        created_at=datetime(2026, 5, 20, 12, 30, tzinfo=UTC),
    )

    assert idea.edge_type == "carry"
    assert idea.edge_types == ("carry", "term_structure")
    assert idea.to_payload()["edge_types"] == ["carry", "term_structure"]


def test_idea_status_lifecycle_values() -> None:
    for status in (
        "idea",
        "factor_candidate",
        "strategy_prototype",
        "validated_research",
        "frozen_forward",
        "paper_candidate",
        "rejected",
        "retired",
    ):
        idea = IdeaSpec(
            idea_id=f"idea-{status}",
            title=f"{status} title",
            hypothesis="Lifecycle state is accepted by the governance schema.",
            edge_type="carry",
            source="openalex",
            created_at=datetime(2026, 5, 20, 12, 30, tzinfo=UTC),
            status=status,
        )
        assert idea.status == status


def test_experiment_increments_idea_trial_count(tmp_path: Path) -> None:
    registry = IdeaRegistry(tmp_path)
    registry.save_idea(_idea())

    registry.record_trial(
        "idea-momentum",
        experiment_id="exp-001",
        recorded_at=datetime(2026, 5, 21, 9, 0, tzinfo=UTC),
    )
    registry.record_trial(
        "idea-momentum",
        experiment_id="exp-001",
        recorded_at=datetime(2026, 5, 21, 10, 0, tzinfo=UTC),
    )
    registry.record_trial(
        "idea-momentum",
        experiment_id="exp-002",
        recorded_at=datetime(2026, 5, 22, 9, 0, tzinfo=UTC),
    )

    assert registry.get("idea-momentum").trial_count == 2
    assert [
        json.loads(line)
        for line in registry.trial_events_path.read_text(encoding="utf-8").splitlines()
    ] == [
        {
            "experiment_id": "exp-001",
            "idea_id": "idea-momentum",
            "recorded_at": "2026-05-21T09:00:00+00:00",
        },
        {
            "experiment_id": "exp-002",
            "idea_id": "idea-momentum",
            "recorded_at": "2026-05-22T09:00:00+00:00",
        },
    ]


def test_trial_budget_warning_when_exceeded() -> None:
    warning = trial_budget_warning(_idea(trial_count=4), budget=3)

    assert warning is not None
    assert warning.idea_id == "idea-momentum"
    assert warning.trial_count == 4
    assert warning.budget == 3
    assert warning.message == "idea-momentum trial_count 4 exceeds budget 3"
    assert trial_budget_warning(_idea(trial_count=3), budget=3) is None
    configured_warning = trial_budget_warning(_idea(trial_count=4))
    assert configured_warning is not None
    assert configured_warning.budget == 3


def test_idea_spec_persists_data_requirements_kill_criteria_and_trial_budget() -> None:
    idea = _idea()
    payload = idea.to_payload()

    assert payload["data_required"] == ["GC 15m OHLCV", "session VWAP"]
    assert payload["kill_criteria"] == ["oos_net_sharpe_below_0_8"]
    assert payload["trial_budget"] == {
        "max_strategy_trials": 3,
        "max_validation_variants": 2,
    }
    assert IdeaSpec.from_payload(payload).to_payload() == payload


def test_workflow_report_emits_trial_budget_warning_for_idea_metadata() -> None:
    from qts.research.report import ResearchWorkflowReport
    from qts.research.workflow import ResearchWorkflowResult

    idea = _idea(trial_count=4)
    report = ResearchWorkflowReport.from_result(
        ResearchWorkflowResult(
            workflow_id="idea-flow",
            status="completed",
            steps=(),
            idea_metadata=idea.to_payload(),
        )
    )

    body = report.to_markdown()

    assert "## Idea Metadata" in body
    assert "- idea_id: idea-momentum" in body
    assert "- edge_types: ['momentum']" in body
    assert "- trial_budget_warning: idea-momentum trial_count 4 exceeds budget 3" in body


def test_promotion_candidate_requires_idea_id_helper_validation() -> None:
    with pytest.raises(ValueError, match="idea_id is required"):
        validate_promotion_candidate({"candidate_id": "candidate-001"})

    candidate = validate_promotion_candidate(
        {
            "candidate_id": "candidate-001",
            "idea_id": " idea-momentum ",
            "score": "0.42",
        }
    )

    assert candidate == {
        "candidate_id": "candidate-001",
        "idea_id": "idea-momentum",
        "score": "0.42",
    }


def test_idea_registry_public_exports_are_available() -> None:
    from qts.research import IdeaRegistry as ExportedIdeaRegistry
    from qts.research import IdeaSpec as ExportedIdeaSpec

    assert ExportedIdeaRegistry is IdeaRegistry
    assert ExportedIdeaSpec is IdeaSpec
