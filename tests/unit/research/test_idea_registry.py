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
