"""Deterministic governance registry for research ideas."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.core.time import require_aware_datetime
from qts.research.idea_spec import IdeaSpec


@dataclass(frozen=True, slots=True)
class TrialBudgetWarning:
    """Process warning emitted when an idea exceeds its trial budget."""

    idea_id: str
    trial_count: int
    budget: int

    @property
    def message(self) -> str:
        """Return a stable human-readable warning message."""

        return f"{self.idea_id} trial_count {self.trial_count} exceeds budget {self.budget}"


class IdeaRegistry:
    """Owns YAML idea specs plus JSONL trial/review evidence."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    @property
    def ideas_path(self) -> Path:
        """Return the deterministic YAML registry path."""

        return self._root_dir / "ideas.yaml"

    @property
    def trial_events_path(self) -> Path:
        """Return the deterministic JSONL trial evidence path."""

        return self._root_dir / "idea-trials.jsonl"

    @property
    def review_events_path(self) -> Path:
        """Return the deterministic JSONL review evidence path."""

        return self._root_dir / "idea-reviews.jsonl"

    def save_idea(self, idea: IdeaSpec) -> Path:
        """Upsert one idea spec and persist the sorted YAML registry."""

        ideas_by_id = {item.idea_id: item for item in self.list_ideas()}
        ideas_by_id[idea.idea_id] = idea
        self._write_ideas(tuple(ideas_by_id.values()))
        return self.ideas_path

    def get(self, idea_id: str) -> IdeaSpec:
        """Return one idea by id."""

        normalized_id = idea_id.strip()
        for idea in self.list_ideas():
            if idea.idea_id == normalized_id:
                return idea
        raise KeyError(f"unknown idea_id: {normalized_id}")

    def list_ideas(self) -> tuple[IdeaSpec, ...]:
        """Return all idea specs sorted by id."""

        if not self.ideas_path.exists():
            return ()
        payload = yaml.safe_load(self.ideas_path.read_text(encoding="utf-8"))
        if payload is None:
            return ()
        if not isinstance(payload, dict):
            raise ValueError("idea registry YAML must contain a mapping")
        raw_ideas = payload.get("ideas", [])
        if not isinstance(raw_ideas, list):
            raise ValueError("idea registry YAML ideas must be a list")
        return tuple(
            sorted(
                (IdeaSpec.from_payload(item) for item in raw_ideas if isinstance(item, Mapping)),
                key=lambda idea: idea.idea_id,
            )
        )

    def record_trial(
        self,
        idea_id: str,
        *,
        experiment_id: str,
        recorded_at: datetime | None = None,
    ) -> IdeaSpec:
        """Record one unique experiment trial and deterministically update trial_count."""

        idea = self.get(idea_id)
        experiment_id = experiment_id.strip()
        if not experiment_id:
            raise ValueError("experiment_id is required")
        timestamp = datetime.now(UTC) if recorded_at is None else recorded_at
        require_aware_datetime(timestamp, name="recorded_at")

        events = list(self._load_trial_events())
        key = (idea.idea_id, experiment_id)
        if key not in {(str(event["idea_id"]), str(event["experiment_id"])) for event in events}:
            events.append(
                {
                    "experiment_id": experiment_id,
                    "idea_id": idea.idea_id,
                    "recorded_at": timestamp.isoformat(),
                }
            )
            self._write_trial_events(tuple(events))
        self._sync_trial_counts()
        return self.get(idea.idea_id)

    def record_review_decision(
        self,
        idea_id: str,
        *,
        decision: str,
        reviewer: str,
        hypothesis: str | None = None,
        rejection_reason: str | None = None,
        reviewed_at: datetime | None = None,
    ) -> IdeaSpec:
        """Persist a process review decision and update the idea status."""

        idea = self.get(idea_id)
        decision = decision.strip()
        reviewer = reviewer.strip()
        reviewed_at = datetime.now(UTC) if reviewed_at is None else reviewed_at
        require_aware_datetime(reviewed_at, name="reviewed_at")
        if not reviewer:
            raise ValueError("reviewer is required")

        next_hypothesis = idea.hypothesis if hypothesis is None else hypothesis.strip()
        if decision == "promotion_review" and not next_hypothesis:
            raise ValueError("hypothesis is required for promotion_review")
        updated = replace(
            idea,
            hypothesis=next_hypothesis,
            status=decision,
            rejection_reason=rejection_reason,
        )
        self.save_idea(updated)
        self._append_review_event(
            {
                "decision": decision,
                "idea_id": updated.idea_id,
                "rejection_reason": updated.rejection_reason,
                "reviewed_at": reviewed_at.isoformat(),
                "reviewer": reviewer,
            }
        )
        return updated

    def _write_ideas(self, ideas: tuple[IdeaSpec, ...]) -> None:
        self._root_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "ideas": [idea.to_payload() for idea in sorted(ideas, key=lambda item: item.idea_id)]
        }
        content = yaml.safe_dump(payload, sort_keys=True)
        self.ideas_path.write_text(content, encoding="utf-8")

    def _load_trial_events(self) -> tuple[dict[str, Any], ...]:
        if not self.trial_events_path.exists():
            return ()
        events: list[dict[str, Any]] = []
        for line in self.trial_events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("trial event row must be a JSON object")
            events.append(dict(payload))
        return tuple(events)

    def _write_trial_events(self, events: tuple[dict[str, Any], ...]) -> None:
        self.trial_events_path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(
            events,
            key=lambda event: (
                str(event["recorded_at"]),
                str(event["idea_id"]),
                str(event["experiment_id"]),
            ),
        )
        lines = [json.dumps(event, sort_keys=True) for event in ordered]
        self.trial_events_path.write_text(
            "\n".join(lines) + ("\n" if lines else ""),
            encoding="utf-8",
        )

    def _sync_trial_counts(self) -> None:
        events = self._load_trial_events()
        experiments_by_idea: dict[str, set[str]] = {}
        for event in events:
            experiments_by_idea.setdefault(str(event["idea_id"]), set()).add(
                str(event["experiment_id"])
            )
        synced = tuple(
            replace(
                idea,
                trial_count=len(experiments_by_idea.get(idea.idea_id, set())),
            )
            for idea in self.list_ideas()
        )
        self._write_ideas(synced)

    def _append_review_event(self, event: dict[str, Any]) -> None:
        self.review_events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.review_events_path.open("a", encoding="utf-8") as review_file:
            review_file.write(json.dumps(event, sort_keys=True) + "\n")


def trial_budget_warning(
    idea: IdeaSpec,
    *,
    budget: int | None = None,
    budget_key: str = "max_strategy_trials",
) -> TrialBudgetWarning | None:
    """Return a warning when an idea's trial count exceeds its configured budget."""

    resolved_budget = budget if budget is not None else (idea.trial_budget or {}).get(budget_key)
    if resolved_budget is None:
        return None
    if resolved_budget < 0:
        raise ValueError("budget must be non-negative")
    if idea.trial_count <= resolved_budget:
        return None
    return TrialBudgetWarning(
        idea_id=idea.idea_id,
        trial_count=idea.trial_count,
        budget=resolved_budget,
    )


def validate_promotion_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Return a normalized promotion candidate payload with required idea linkage."""

    payload = dict(candidate)
    idea_id = payload.get("idea_id")
    if not isinstance(idea_id, str) or not idea_id.strip():
        raise ValueError("idea_id is required")
    payload["idea_id"] = idea_id.strip()
    return payload


__all__ = [
    "IdeaRegistry",
    "TrialBudgetWarning",
    "trial_budget_warning",
    "validate_promotion_candidate",
]
