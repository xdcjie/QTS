"""Factor research-workbench service.

Owns the factor discovery, hypothesis drafting/persistence, and candidate-review
workflow extracted from ``ResearchSession`` (QTS-FINAL-011), so the facade keeps
no candidate/review/spec-persistence logic directly. Discovery and spec-store
dependencies are supplied as factories so the session's lazy, shared instances
are preserved (filesystem-backed stores are not built until first use).
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from qts.research.factor_candidate import FactorCandidateBatch, FactorCandidateWorkflow
from qts.research.factor_discovery import FactorDiscovery, FactorDiscoveryResult, FactorIdea
from qts.research.factor_spec import FactorSpec, FactorSpecDrafter
from qts.research.factor_spec_store import FactorSpecReview, FactorSpecStore


class FactorWorkbenchService:
    """Owns factor discovery, hypothesis drafting/persistence, and candidate review."""

    def __init__(
        self,
        *,
        discovery_factory: Callable[[], FactorDiscovery],
        spec_store_factory: Callable[[], FactorSpecStore],
        discovery_sources: Sequence[str],
        discovery_max_results: int,
    ) -> None:
        """Create the workbench bound to lazy discovery + spec-store factories."""
        self._discovery_factory = discovery_factory
        self._spec_store_factory = spec_store_factory
        self._discovery_sources = tuple(discovery_sources)
        self._discovery_max_results = discovery_max_results

    def discover_factors(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        max_results: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> FactorDiscoveryResult:
        """Discover source-backed factor ideas without creating executable behavior."""

        return self._discovery_factory().search(
            query,
            sources=self._discovery_sources if sources is None else sources,
            max_results=(self._discovery_max_results if max_results is None else max_results),
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        )

    def discover_factors_frame(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        max_results: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> Any:
        """Return discovered factor ideas as a pandas DataFrame."""

        return self.discover_factors(
            query,
            sources=sources,
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        ).to_pandas()

    def draft_factor_spec(self, idea: FactorIdea) -> FactorSpec:
        """Draft a non-executable factor hypothesis from one discovered idea."""

        return FactorSpecDrafter().draft(idea)

    def draft_factor_specs(
        self,
        ideas: FactorDiscoveryResult | Sequence[FactorIdea],
    ) -> tuple[FactorSpec, ...]:
        """Draft non-executable factor hypotheses from discovered ideas."""

        source_ideas = ideas.ideas if isinstance(ideas, FactorDiscoveryResult) else ideas
        drafter = FactorSpecDrafter()
        return tuple(drafter.draft(idea) for idea in source_ideas)

    def save_factor_spec(self, spec: FactorSpec) -> Path:
        """Persist one non-executable factor hypothesis draft."""

        return self._spec_store_factory().save(spec)

    def save_factor_specs(self, specs: Sequence[FactorSpec]) -> tuple[Path, ...]:
        """Persist multiple non-executable factor hypothesis drafts."""

        spec_store = self._spec_store_factory()
        return tuple(spec_store.save(spec) for spec in specs)

    def list_factor_specs(self) -> tuple[FactorSpec, ...]:
        """Return persisted factor hypothesis drafts sorted by name."""

        return self._spec_store_factory().list_specs()

    def load_factor_spec(self, name: str) -> FactorSpec:
        """Load one persisted factor hypothesis draft by name."""

        return self._spec_store_factory().load(name)

    def find_factor_candidates(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        max_results: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> FactorCandidateBatch:
        """Discover, draft, and persist non-executable factor candidates."""

        return FactorCandidateWorkflow(
            discovery=self._discovery_factory(),
            spec_store=self._spec_store_factory(),
        ).find(
            query,
            sources=self._discovery_sources if sources is None else sources,
            max_results=(self._discovery_max_results if max_results is None else max_results),
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        )

    def find_factor_candidates_frame(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        max_results: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> Any:
        """Return discovered factor candidates as a pandas DataFrame."""

        return self.find_factor_candidates(
            query,
            sources=sources,
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        ).to_pandas()

    def review_factor_spec(
        self,
        name: str,
        *,
        decision: str,
        reviewer: str,
        notes: Sequence[str] = (),
        reviewed_at: datetime | None = None,
    ) -> FactorSpecReview:
        """Record a research review decision for a persisted factor spec."""

        return self._spec_store_factory().record_review(
            name,
            decision=decision,
            reviewer=reviewer,
            notes=notes,
            reviewed_at=reviewed_at,
        )

    def list_factor_reviews(
        self,
        *,
        decision: str | None = None,
    ) -> tuple[FactorSpecReview, ...]:
        """Return persisted factor spec review decisions."""

        return self._spec_store_factory().list_reviews(decision=decision)

    def list_factor_specs_by_status(self, status: str) -> tuple[FactorSpec, ...]:
        """Return persisted factor specs filtered by review status."""

        return self._spec_store_factory().list_specs_by_status(status)

    def review_queue_frame(self, *, status: str = "draft") -> Any:
        """Return factor specs awaiting review as a pandas DataFrame."""

        pandas_module: Any = importlib.import_module("pandas")
        return pandas_module.DataFrame(
            [
                {
                    "candidate_tags": ", ".join(spec.candidate_tags),
                    "hypothesis": spec.hypothesis,
                    "promotion_gate": spec.promotion_gate,
                    "review_status": spec.review_status,
                    "source_refs": ", ".join(
                        f"{source_ref.source}:{source_ref.external_id}"
                        for source_ref in spec.source_refs
                    ),
                    "spec_name": spec.name,
                }
                for spec in self.list_factor_specs_by_status(status)
            ]
        )


__all__ = ["FactorWorkbenchService"]
