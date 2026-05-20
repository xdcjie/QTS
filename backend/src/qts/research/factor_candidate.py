"""Research-only factor candidate workflow artifacts."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.research.factor_discovery import (
    DEFAULT_FACTOR_DISCOVERY_SOURCES,
    FactorDiscovery,
    FactorDiscoveryResult,
    FactorIdea,
)
from qts.research.factor_spec import FactorSpec, FactorSpecDrafter
from qts.research.factor_spec_store import FactorSpecStore


@dataclass(frozen=True, slots=True)
class FactorCandidate:
    """One discovered idea with its human-reviewable spec draft."""

    idea: FactorIdea
    spec: FactorSpec
    spec_path: Path


@dataclass(frozen=True, slots=True)
class FactorCandidateBatch:
    """Review batch produced from one factor discovery search."""

    result: FactorDiscoveryResult
    candidates: tuple[FactorCandidate, ...]

    @property
    def specs(self) -> tuple[FactorSpec, ...]:
        """Return spec drafts in candidate order."""

        return tuple(candidate.spec for candidate in self.candidates)

    def rows(self) -> tuple[dict[str, object], ...]:
        """Return notebook-friendly rows for candidate review."""

        return tuple(
            {
                "query_id": self.result.query.query_id,
                "query_text": self.result.query.text,
                "idea_id": candidate.idea.idea_id,
                "source": candidate.idea.source,
                "external_id": candidate.idea.external_id,
                "title": candidate.idea.title,
                "url": candidate.idea.url,
                "year": candidate.idea.year,
                "candidate_tags": ", ".join(candidate.idea.candidate_tags),
                "spec_name": candidate.spec.name,
                "spec_path": str(candidate.spec_path),
                "review_status": candidate.spec.review_status,
            }
            for candidate in self.candidates
        )

    def to_pandas(self) -> Any:
        """Return candidate rows as a pandas DataFrame."""

        pandas_module: Any = importlib.import_module("pandas")
        return pandas_module.DataFrame(self.rows())


class FactorCandidateWorkflow:
    """Coordinates discovery ideas into persisted reviewable spec drafts."""

    def __init__(self, *, discovery: FactorDiscovery, spec_store: FactorSpecStore) -> None:
        self._discovery = discovery
        self._spec_store = spec_store

    def find(
        self,
        query: str,
        *,
        sources: Sequence[str] = DEFAULT_FACTOR_DISCOVERY_SOURCES,
        max_results: int = 10,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> FactorCandidateBatch:
        """Find source-backed ideas and persist non-executable spec drafts."""

        result = self._discovery.search(
            query,
            sources=sources,
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        )
        drafter = FactorSpecDrafter()
        candidates = tuple(self._draft_candidate(idea, drafter=drafter) for idea in result.ideas)
        return FactorCandidateBatch(result=result, candidates=candidates)

    def _draft_candidate(
        self,
        idea: FactorIdea,
        *,
        drafter: FactorSpecDrafter,
    ) -> FactorCandidate:
        spec = drafter.draft(idea)
        spec_path = self._spec_store.save(spec)
        return FactorCandidate(idea=idea, spec=spec, spec_path=spec_path)


__all__ = ["FactorCandidate", "FactorCandidateBatch", "FactorCandidateWorkflow"]
