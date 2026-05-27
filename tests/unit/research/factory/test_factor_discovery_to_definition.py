from __future__ import annotations

from datetime import UTC, datetime

from qts.research.factor_discovery import FactorIdea
from qts.research.factory import (
    FactorDefinitionDraftConstraints,
    FactorDiscoveryDraftMapper,
)
from qts.research.idea_spec import IdeaSpec


def _idea(
    *,
    idea_id: str,
    title: str,
    abstract: str,
    candidate_tags: tuple[str, ...] = (),
) -> FactorIdea:
    return FactorIdea(
        idea_id=idea_id,
        source="fixture",
        external_id=idea_id,
        title=title,
        abstract=abstract,
        url="https://example.test/paper",
        year=2026,
        authors=("A. Researcher",),
        citation_count=7,
        candidate_tags=candidate_tags,
    )


def _mapper() -> FactorDiscoveryDraftMapper:
    return FactorDiscoveryDraftMapper(
        constraints=FactorDefinitionDraftConstraints(
            roots=("GC", "SI"),
            label_horizon_bars=60,
            family_lookbacks={
                "momentum": 120,
                "carry": 20,
                "spread_zscore": 240,
            },
        )
    )


def test_momentum_idea_maps_to_factor_definition_draft() -> None:
    draft = _mapper().draft_from_idea(
        _idea(
            idea_id="paper:momentum",
            title="Trend following momentum in commodity futures",
            abstract="Time-series momentum predicts next-session returns.",
            candidate_tags=("momentum",),
        )
    )

    assert draft.idea_id == "paper:momentum"
    assert draft.needs_human_spec is False
    assert draft.factor_definition is not None
    assert draft.factor_definition.family == "momentum"
    assert draft.factor_definition.source_idea_id == "paper:momentum"
    assert draft.factor_definition.validate(allowed_roots=("GC", "SI")).accepted is True


def test_carry_idea_maps_to_factor_definition_draft() -> None:
    draft = _mapper().draft_from_idea(
        _idea(
            idea_id="paper:carry",
            title="Term structure carry in futures markets",
            abstract="Roll yield and basis contain carry premia.",
            candidate_tags=("carry",),
        )
    )

    assert draft.idea_id == "paper:carry"
    assert draft.needs_human_spec is False
    assert draft.factor_definition is not None
    assert draft.factor_definition.family == "carry"
    assert draft.factor_definition.inputs[0].field == "roll_yield"


def test_spread_idea_maps_to_spread_zscore_factor_definition_draft() -> None:
    draft = _mapper().draft_from_idea(
        _idea(
            idea_id="paper:spread",
            title="Gold silver spread z-score mean reversion",
            abstract="A pair spread z-score identifies relative value dislocations.",
        )
    )

    assert draft.idea_id == "paper:spread"
    assert draft.needs_human_spec is False
    assert draft.factor_definition is not None
    assert draft.factor_definition.family == "spread_zscore"
    assert [transform.transform_type for transform in draft.factor_definition.transforms] == [
        "ratio",
        "rolling_zscore",
    ]


def test_unmappable_idea_is_marked_needs_human_spec_with_idea_reference() -> None:
    draft = _mapper().draft_from_idea(
        _idea(
            idea_id="paper:sentiment",
            title="News sentiment in commodity markets",
            abstract="Text embeddings may predict return dispersion.",
            candidate_tags=("sentiment",),
        )
    )

    assert draft.idea_id == "paper:sentiment"
    assert draft.needs_human_spec is True
    assert draft.factor_definition is None
    assert draft.reason == "no supported factory mapping for idea"


def test_idea_spec_maps_by_edge_type_and_preserves_idea_id_reference() -> None:
    idea_spec = IdeaSpec(
        idea_id="idea:carry",
        title="Carry edge",
        hypothesis="Term structure carry from roll yield",
        edge_type="carry",
        edge_types=("carry",),
        source="manual",
        created_at=datetime(2026, 5, 27, tzinfo=UTC),
    )

    draft = _mapper().draft_from_idea_spec(idea_spec)

    assert draft.idea_id == "idea:carry"
    assert draft.needs_human_spec is False
    assert draft.factor_definition is not None
    assert draft.factor_definition.source_idea_id == "idea:carry"
