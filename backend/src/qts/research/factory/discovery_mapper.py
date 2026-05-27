"""Map discovered research ideas into controlled factor definition drafts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from qts.research.factor_discovery import FactorIdea
from qts.research.factory.factor_definition import (
    FactorDefinition,
    FactorInput,
    FactorLabelPolicy,
    FactorTransform,
)
from qts.research.idea_spec import IdeaSpec


@dataclass(frozen=True, slots=True)
class FactorDefinitionDraftConstraints:
    """Manual seed constraints used by deterministic discovery-to-DSL mapping."""

    roots: tuple[str, ...]
    label_horizon_bars: int = 60
    default_field: str = "close"
    family_lookbacks: Mapping[str, int] = field(
        default_factory=lambda: {
            "carry": 20,
            "momentum": 120,
            "spread_zscore": 240,
        }
    )

    def __post_init__(self) -> None:
        roots = tuple(dict.fromkeys(root.strip().upper() for root in self.roots if root.strip()))
        default_field = self.default_field.strip().lower()
        family_lookbacks = {
            str(family).strip().lower(): int(lookback)
            for family, lookback in self.family_lookbacks.items()
        }
        if not roots:
            raise ValueError("roots must not be empty")
        if self.label_horizon_bars <= 0:
            raise ValueError("label_horizon_bars must be positive")
        if not default_field:
            raise ValueError("default_field is required")
        if any(lookback <= 0 for lookback in family_lookbacks.values()):
            raise ValueError("family lookbacks must be positive")
        object.__setattr__(self, "roots", roots)
        object.__setattr__(self, "default_field", default_field)
        object.__setattr__(self, "family_lookbacks", family_lookbacks)

    def lookback_for(self, family: str) -> int:
        """Return the seeded lookback for a mapped family."""

        return int(self.family_lookbacks.get(family, 60))


@dataclass(frozen=True, slots=True)
class FactorDefinitionDraft:
    """Draft result that always preserves its originating idea ID."""

    idea_id: str
    needs_human_spec: bool
    factor_definition: FactorDefinition | None
    reason: str

    def __post_init__(self) -> None:
        idea_id = self.idea_id.strip()
        reason = self.reason.strip()
        if not idea_id:
            raise ValueError("idea_id is required")
        if not reason:
            raise ValueError("reason is required")
        if self.needs_human_spec and self.factor_definition is not None:
            raise ValueError("needs_human_spec drafts must not include factor_definition")
        if not self.needs_human_spec and self.factor_definition is None:
            raise ValueError("mapped drafts require factor_definition")
        object.__setattr__(self, "idea_id", idea_id)
        object.__setattr__(self, "reason", reason)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready draft payload."""

        return {
            "factor_definition": (
                None if self.factor_definition is None else self.factor_definition.to_payload()
            ),
            "idea_id": self.idea_id,
            "needs_human_spec": self.needs_human_spec,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class FactorDiscoveryDraftMapper:
    """Owns deterministic FactorDiscovery/IdeaSpec to FactorDefinition drafts."""

    constraints: FactorDefinitionDraftConstraints

    def draft_from_idea(self, idea: FactorIdea) -> FactorDefinitionDraft:
        """Map a source-backed discovery idea to a factor definition draft."""

        text = f"{idea.title}\n{idea.abstract}"
        return self._draft(
            idea_id=idea.idea_id,
            terms=tuple(idea.candidate_tags),
            text=text,
        )

    def draft_from_idea_spec(self, idea_spec: IdeaSpec) -> FactorDefinitionDraft:
        """Map a governed IdeaSpec to a factor definition draft."""

        text = f"{idea_spec.title}\n{idea_spec.hypothesis}"
        return self._draft(
            idea_id=idea_spec.idea_id,
            terms=idea_spec.edge_types,
            text=text,
        )

    def _draft(
        self,
        *,
        idea_id: str,
        terms: tuple[str, ...],
        text: str,
    ) -> FactorDefinitionDraft:
        family = self._family_for(terms=terms, text=text)
        if family is None:
            return FactorDefinitionDraft(
                idea_id=idea_id,
                needs_human_spec=True,
                factor_definition=None,
                reason="no supported factory mapping for idea",
            )
        if family == "spread_zscore" and len(self.constraints.roots) < 2:
            return FactorDefinitionDraft(
                idea_id=idea_id,
                needs_human_spec=True,
                factor_definition=None,
                reason="spread_zscore mapping requires at least two roots",
            )
        definition = self._definition_for(family=family, idea_id=idea_id)
        return FactorDefinitionDraft(
            idea_id=idea_id,
            needs_human_spec=False,
            factor_definition=definition,
            reason=f"mapped {family} idea to factor definition draft",
        )

    def _family_for(self, *, terms: tuple[str, ...], text: str) -> str | None:
        normalized_terms = frozenset(term.strip().lower() for term in terms if term.strip())
        normalized_text = text.lower()
        if self._is_spread_text(normalized_text) or "relative_value" in normalized_terms:
            return "spread_zscore"
        if normalized_terms & {"carry", "term_structure"} or self._contains_any(
            normalized_text,
            ("carry", "roll yield", "term structure", "basis"),
        ):
            return "carry"
        if normalized_terms & {"cross_sectional_momentum", "momentum", "time_series_momentum"}:
            return "momentum"
        if self._contains_any(normalized_text, ("momentum", "trend", "trend-following")):
            return "momentum"
        return None

    def _definition_for(self, *, family: str, idea_id: str) -> FactorDefinition:
        if family == "momentum":
            return self._momentum_definition(idea_id)
        if family == "carry":
            return self._carry_definition(idea_id)
        return self._spread_definition(idea_id)

    def _momentum_definition(self, idea_id: str) -> FactorDefinition:
        return FactorDefinition(
            factor_id=self._factor_id("momentum", idea_id),
            family="momentum",
            inputs=(
                FactorInput(root=self.constraints.roots[0], field=self.constraints.default_field),
            ),
            transforms=(
                FactorTransform(
                    transform_type="returns",
                    parameters={"lookback": self.constraints.lookback_for("momentum")},
                ),
            ),
            label_policy=self._label_policy(),
            source_idea_id=idea_id,
        )

    def _carry_definition(self, idea_id: str) -> FactorDefinition:
        return FactorDefinition(
            factor_id=self._factor_id("carry", idea_id),
            family="carry",
            inputs=(FactorInput(root=self.constraints.roots[0], field="roll_yield"),),
            transforms=(
                FactorTransform(
                    transform_type="carry",
                    parameters={"lookback": self.constraints.lookback_for("carry")},
                ),
            ),
            label_policy=self._label_policy(),
            source_idea_id=idea_id,
        )

    def _spread_definition(self, idea_id: str) -> FactorDefinition:
        return FactorDefinition(
            factor_id=self._factor_id("spread_zscore", idea_id),
            family="spread_zscore",
            inputs=(
                FactorInput(root=self.constraints.roots[0], field=self.constraints.default_field),
                FactorInput(root=self.constraints.roots[1], field=self.constraints.default_field),
            ),
            transforms=(
                FactorTransform(transform_type="ratio"),
                FactorTransform(
                    transform_type="rolling_zscore",
                    parameters={"lookback": self.constraints.lookback_for("spread_zscore")},
                ),
            ),
            label_policy=self._label_policy(),
            source_idea_id=idea_id,
        )

    def _label_policy(self) -> FactorLabelPolicy:
        return FactorLabelPolicy(
            horizon_bars=self.constraints.label_horizon_bars,
            visible_after="close",
            no_lookahead=True,
        )

    @staticmethod
    def _factor_id(family: str, idea_id: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", idea_id.strip().lower()).strip("_")
        return f"{family}_{normalized or 'idea'}_draft"

    @staticmethod
    def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
        return any(needle in value for needle in needles)

    @staticmethod
    def _is_spread_text(value: str) -> bool:
        return "spread" in value and any(
            term in value
            for term in (
                "pair",
                "pairs",
                "relative value",
                "z-score",
                "zscore",
            )
        )


__all__ = [
    "FactorDefinitionDraft",
    "FactorDefinitionDraftConstraints",
    "FactorDiscoveryDraftMapper",
]
