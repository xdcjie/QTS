from __future__ import annotations

from pathlib import Path

from qts.research.factor_candidate import FactorCandidateBatch, FactorCandidateWorkflow
from qts.research.factor_discovery import (
    FactorDiscovery,
    FactorDiscoveryQuery,
    FactorIdea,
    FactorIdeaStore,
)
from qts.research.factor_spec_store import FactorSpecStore


class _FixtureSource:
    name = "fixture"

    def __init__(self, ideas: tuple[FactorIdea, ...]) -> None:
        self.calls: list[FactorDiscoveryQuery] = []
        self._ideas = ideas

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        self.calls.append(query)
        return self._ideas


def _idea(
    *,
    idea_id: str,
    title: str,
    candidate_tags: tuple[str, ...],
    year: int | None = 2026,
) -> FactorIdea:
    return FactorIdea(
        idea_id=idea_id,
        source="fixture",
        external_id=idea_id,
        title=title,
        abstract="Research evidence for a non-executable factor candidate.",
        url=f"https://example.test/{idea_id}",
        year=year,
        authors=("A. Researcher",),
        citation_count=12,
        candidate_tags=candidate_tags,
    )


def test_factor_candidate_workflow_discovers_drafts_and_saves_specs_in_order(
    tmp_path: Path,
) -> None:
    ideas = (
        _idea(
            idea_id="fixture:momentum",
            title="Momentum and volatility effects",
            candidate_tags=("momentum", "volatility"),
        ),
        _idea(
            idea_id="fixture:carry",
            title="Carry signals in futures",
            candidate_tags=("carry",),
            year=2025,
        ),
    )
    source = _FixtureSource(ideas)
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={"fixture": source},
    )
    spec_store = FactorSpecStore(tmp_path / "research-store")
    workflow = FactorCandidateWorkflow(discovery=discovery, spec_store=spec_store)

    batch = workflow.find(
        "commodity factors",
        sources=("fixture",),
        max_results=2,
        from_year=2020,
        to_year=2026,
        refresh=True,
    )

    assert isinstance(batch, FactorCandidateBatch)
    assert [candidate.idea for candidate in batch.candidates] == list(ideas)
    assert [candidate.spec.name for candidate in batch.candidates] == [
        "momentum-volatility-effects",
        "carry-signals-in-futures",
    ]
    assert batch.specs == tuple(candidate.spec for candidate in batch.candidates)
    assert [candidate.spec_path for candidate in batch.candidates] == [
        spec_store.path_for("momentum-volatility-effects"),
        spec_store.path_for("carry-signals-in-futures"),
    ]
    assert spec_store.load("momentum-volatility-effects").review_status == "draft"
    assert spec_store.load("carry-signals-in-futures").promotion_gate == "human_review_required"
    assert source.calls == [
        FactorDiscoveryQuery(
            text="commodity factors",
            sources=("fixture",),
            max_results=2,
            from_year=2020,
            to_year=2026,
        )
    ]


def test_factor_candidate_batch_rows_include_discovery_and_spec_review_fields(
    tmp_path: Path,
) -> None:
    idea = _idea(
        idea_id="fixture:momentum",
        title="Momentum and volatility effects",
        candidate_tags=("momentum", "volatility"),
    )
    workflow = FactorCandidateWorkflow(
        discovery=FactorDiscovery(
            store=FactorIdeaStore(tmp_path / "research-store"),
            sources={"fixture": _FixtureSource((idea,))},
        ),
        spec_store=FactorSpecStore(tmp_path / "research-store"),
    )

    batch = workflow.find("commodity factors", sources=("fixture",), max_results=1)

    assert batch.rows() == (
        {
            "query_id": batch.result.query.query_id,
            "query_text": "commodity factors",
            "idea_id": "fixture:momentum",
            "source": "fixture",
            "external_id": "fixture:momentum",
            "title": "Momentum and volatility effects",
            "url": "https://example.test/fixture:momentum",
            "year": 2026,
            "candidate_tags": "momentum, volatility",
            "spec_name": "momentum-volatility-effects",
            "spec_path": str(batch.candidates[0].spec_path),
            "review_status": "draft",
        },
    )


def test_factor_candidate_batch_to_pandas_imports_pandas_lazily(
    tmp_path: Path,
) -> None:
    idea = _idea(
        idea_id="fixture:carry",
        title="Carry signals in futures",
        candidate_tags=("carry",),
    )
    workflow = FactorCandidateWorkflow(
        discovery=FactorDiscovery(
            store=FactorIdeaStore(tmp_path / "research-store"),
            sources={"fixture": _FixtureSource((idea,))},
        ),
        spec_store=FactorSpecStore(tmp_path / "research-store"),
    )
    batch = workflow.find("carry factors", sources=("fixture",), max_results=1)

    frame = batch.to_pandas()

    assert list(frame["spec_name"]) == ["carry-signals-in-futures"]
    assert list(frame["candidate_tags"]) == ["carry"]
