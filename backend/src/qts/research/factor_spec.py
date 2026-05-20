"""Human-reviewable factor hypothesis drafts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from qts.research.factor_discovery import FactorIdea

_INPUTS_BY_TAG: dict[str, tuple[str, ...]] = {
    "carry": ("contract_chain", "roll_yield"),
    "liquidity": ("volume", "bid_ask_spread"),
    "macro": ("macro_series",),
    "momentum": ("close",),
    "quality": ("fundamental_data",),
    "reversal": ("close",),
    "seasonality": ("calendar", "session"),
    "sentiment": ("news_sentiment",),
    "value": ("fundamental_data",),
    "volatility": ("high", "low", "close"),
}

_DATA_REQUIREMENTS_BY_TAG: dict[str, tuple[str, ...]] = {
    "carry": ("continuous futures chain metadata", "roll-adjusted futures history"),
    "liquidity": ("volume history", "quote or spread history"),
    "macro": ("aligned macro time series",),
    "momentum": ("historical bars",),
    "quality": ("point-in-time fundamentals",),
    "reversal": ("historical bars",),
    "seasonality": ("exchange calendar and session labels",),
    "sentiment": ("timestamped news or sentiment scores",),
    "value": ("point-in-time fundamentals",),
    "volatility": ("historical OHLC bars",),
}


@dataclass(frozen=True, slots=True)
class FactorSpecSourceRef:
    """One source reference supporting a factor hypothesis draft."""

    source: str
    external_id: str
    title: str
    url: str
    year: int | None

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source is required")
        if not self.external_id.strip():
            raise ValueError("external_id is required")
        if not self.title.strip():
            raise ValueError("title is required")
        object.__setattr__(self, "source", self.source.strip().lower())
        object.__setattr__(self, "external_id", self.external_id.strip())
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "url", self.url.strip())

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready source reference."""

        return {
            "external_id": self.external_id,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "year": self.year,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FactorSpecSourceRef:
        """Rehydrate a source reference from JSON."""

        return cls(
            source=str(payload.get("source", "")),
            external_id=str(payload.get("external_id", "")),
            title=str(payload.get("title", "")),
            url=str(payload.get("url", "")),
            year=_optional_int(payload.get("year")),
        )


@dataclass(frozen=True, slots=True)
class FactorSpec:
    """Owns a non-executable factor hypothesis draft."""

    name: str
    hypothesis: str
    inputs: tuple[str, ...]
    lookback: str
    universe: str
    rebalance: str
    expected_direction: str
    data_requirements: tuple[str, ...]
    source_refs: tuple[FactorSpecSourceRef, ...]
    candidate_tags: tuple[str, ...]
    notes: tuple[str, ...]
    review_status: str = "draft"
    promotion_gate: str = "human_review_required"

    def __post_init__(self) -> None:
        name = self.name.strip()
        hypothesis = self.hypothesis.strip()
        inputs = tuple(dict.fromkeys(item.strip() for item in self.inputs if item.strip()))
        lookback = self.lookback.strip()
        universe = self.universe.strip()
        rebalance = self.rebalance.strip()
        expected_direction = self.expected_direction.strip()
        data_requirements = tuple(
            dict.fromkeys(item.strip() for item in self.data_requirements if item.strip())
        )
        source_refs = tuple(self.source_refs)
        candidate_tags = tuple(
            dict.fromkeys(item.strip() for item in self.candidate_tags if item.strip())
        )
        notes = tuple(dict.fromkeys(item.strip() for item in self.notes if item.strip()))
        review_status = self.review_status.strip()
        promotion_gate = self.promotion_gate.strip()

        if not name:
            raise ValueError("name is required")
        if not hypothesis:
            raise ValueError("hypothesis is required")
        if not inputs:
            raise ValueError("inputs must not be empty")
        if not lookback:
            raise ValueError("lookback is required")
        if not universe:
            raise ValueError("universe is required")
        if not rebalance:
            raise ValueError("rebalance is required")
        if not expected_direction:
            raise ValueError("expected_direction is required")
        if not data_requirements:
            raise ValueError("data_requirements must not be empty")
        if not source_refs:
            raise ValueError("source_refs must not be empty")
        if not review_status:
            raise ValueError("review_status is required")
        if not promotion_gate:
            raise ValueError("promotion_gate is required")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "hypothesis", hypothesis)
        object.__setattr__(self, "inputs", inputs)
        object.__setattr__(self, "lookback", lookback)
        object.__setattr__(self, "universe", universe)
        object.__setattr__(self, "rebalance", rebalance)
        object.__setattr__(self, "expected_direction", expected_direction)
        object.__setattr__(self, "data_requirements", data_requirements)
        object.__setattr__(self, "source_refs", source_refs)
        object.__setattr__(self, "candidate_tags", candidate_tags)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "review_status", review_status)
        object.__setattr__(self, "promotion_gate", promotion_gate)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready factor spec."""

        return {
            "candidate_tags": list(self.candidate_tags),
            "data_requirements": list(self.data_requirements),
            "expected_direction": self.expected_direction,
            "hypothesis": self.hypothesis,
            "inputs": list(self.inputs),
            "lookback": self.lookback,
            "name": self.name,
            "notes": list(self.notes),
            "promotion_gate": self.promotion_gate,
            "rebalance": self.rebalance,
            "review_status": self.review_status,
            "source_refs": [source_ref.to_payload() for source_ref in self.source_refs],
            "universe": self.universe,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FactorSpec:
        """Rehydrate a factor spec from JSON."""

        return cls(
            name=str(payload.get("name", "")),
            hypothesis=str(payload.get("hypothesis", "")),
            inputs=_string_tuple(payload.get("inputs")),
            lookback=str(payload.get("lookback", "")),
            universe=str(payload.get("universe", "")),
            rebalance=str(payload.get("rebalance", "")),
            expected_direction=str(payload.get("expected_direction", "")),
            data_requirements=_string_tuple(payload.get("data_requirements")),
            source_refs=tuple(
                FactorSpecSourceRef.from_payload(item)
                for item in cls._mapping_sequence(payload.get("source_refs"))
            ),
            candidate_tags=_string_tuple(payload.get("candidate_tags")),
            notes=_string_tuple(payload.get("notes")),
            review_status=str(payload.get("review_status", "draft")),
            promotion_gate=str(payload.get("promotion_gate", "human_review_required")),
        )

    @staticmethod
    def _mapping_sequence(value: Any) -> tuple[Mapping[str, Any], ...]:
        if not isinstance(value, list):
            return ()
        return tuple(item for item in value if isinstance(item, dict))


class FactorSpecDrafter:
    """Owns deterministic FactorIdea to FactorSpec draft heuristics."""

    def draft(self, idea: FactorIdea) -> FactorSpec:
        """Return a human-reviewable spec draft for one discovered idea."""

        tags = idea.candidate_tags
        return FactorSpec(
            name=_slug(idea.title),
            hypothesis=(
                f"Research whether '{idea.title}' defines a reusable factor signal. "
                "Scores should be validated with out-of-sample forward returns before "
                "any strategy or live use."
            ),
            inputs=_inputs_for_tags(tags),
            lookback="researcher_defined",
            universe="research_session_universe",
            rebalance="researcher_defined",
            expected_direction="higher_score_higher_expected_return",
            data_requirements=_data_requirements_for_tags(tags),
            source_refs=(
                FactorSpecSourceRef(
                    source=idea.source,
                    external_id=idea.external_id,
                    title=idea.title,
                    url=idea.url,
                    year=idea.year,
                ),
            ),
            candidate_tags=tags,
            notes=(
                "human review required",
                "not executable factor code",
                "must be promoted through qts.factors and FactorEvaluation",
            ),
        )


def _inputs_for_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
    inputs: list[str] = []
    for tag in tags:
        inputs.extend(_INPUTS_BY_TAG.get(tag, ()))
    if not inputs:
        inputs.append("researcher_defined_input")
    return tuple(dict.fromkeys(inputs))


def _data_requirements_for_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
    requirements: list[str] = []
    for tag in tags:
        requirements.extend(_DATA_REQUIREMENTS_BY_TAG.get(tag, ()))
    if not requirements:
        requirements.append("researcher-defined source data")
    return tuple(dict.fromkeys(requirements))


def _slug(value: str) -> str:
    lowered = value.strip().lower()
    words = [
        word
        for word in re.split(r"[^a-z0-9]+", lowered)
        if word and word not in {"a", "an", "and", "of", "the"}
    ]
    normalized = "-".join(words)
    return normalized or "factor-spec"


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


__all__ = ["FactorSpec", "FactorSpecDrafter", "FactorSpecSourceRef"]
