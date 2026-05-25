"""Read-only meta-research summaries for completed research evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from qts.research.idea_spec import IdeaSpec


@dataclass(frozen=True, slots=True)
class MetaResearchArtifacts:
    """Paths written for one meta-research summary."""

    json_path: Path
    markdown_path: Path


@dataclass(frozen=True, slots=True)
class MetaResearchSummary:
    """Monthly or quarterly aggregate over research process evidence."""

    period: str
    period_start: date
    ideas_created: int
    factor_candidates: int
    strategy_prototypes: int
    validation_pass_rate: dict[str, float | int]
    paper_candidate_count: int
    rejected_reason_distribution: dict[str, int]
    source_success_rate: dict[str, dict[str, float | int]]
    edge_type_distribution: dict[str, int]
    trial_count_outliers: tuple[dict[str, int | str], ...]

    @classmethod
    def from_registries(
        cls,
        *,
        ideas: Sequence[IdeaSpec],
        evidence_records: Sequence[Mapping[str, Any]],
        experiment_records: Sequence[Mapping[str, Any]],
        period: str,
        period_start: date,
        trial_count_outlier_threshold: int = 10,
    ) -> MetaResearchSummary:
        """Build a read-only summary from idea, evidence, and experiment records."""

        idea_tuple = tuple(ideas)
        evidence_tuple = tuple(dict(record) for record in evidence_records)
        experiment_tuple = tuple(dict(record) for record in experiment_records)
        validation_records = evidence_tuple + experiment_tuple
        return cls(
            period=period,
            period_start=period_start,
            ideas_created=len(idea_tuple),
            factor_candidates=_count_kind(evidence_tuple, "factor_candidate"),
            strategy_prototypes=_count_kind(evidence_tuple, "strategy_prototype"),
            validation_pass_rate=_pass_rate(validation_records),
            paper_candidate_count=sum(1 for idea in idea_tuple if idea.status == "paper_candidate"),
            rejected_reason_distribution=_rejected_reason_distribution(
                idea_tuple,
                validation_records,
            ),
            source_success_rate=_source_success_rate(idea_tuple, validation_records),
            edge_type_distribution=_edge_type_distribution(idea_tuple),
            trial_count_outliers=_trial_count_outliers(
                idea_tuple,
                threshold=trial_count_outlier_threshold,
            ),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready payload."""

        return {
            "edge_type_distribution": self.edge_type_distribution,
            "factor_candidates": self.factor_candidates,
            "ideas_created": self.ideas_created,
            "paper_candidate_count": self.paper_candidate_count,
            "period": self.period,
            "period_start": self.period_start.isoformat(),
            "rejected_reason_distribution": self.rejected_reason_distribution,
            "source_success_rate": self.source_success_rate,
            "strategy_prototypes": self.strategy_prototypes,
            "trial_count_outliers": list(self.trial_count_outliers),
            "validation_pass_rate": self.validation_pass_rate,
        }


class MetaResearchSummaryWriter:
    """Writes deterministic JSON and Markdown meta-research artifacts."""

    def write(self, output_dir: Path, summary: MetaResearchSummary) -> MetaResearchArtifacts:
        """Write summary artifacts and return their paths."""

        output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"meta-research-{summary.period}-{summary.period_start.isoformat()}"
        json_path = output_dir / f"{stem}.json"
        markdown_path = output_dir / f"{stem}.md"
        payload = summary.to_payload()
        json_path.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(_markdown(payload), encoding="utf-8")
        return MetaResearchArtifacts(json_path=json_path, markdown_path=markdown_path)


def _count_kind(records: Sequence[Mapping[str, Any]], kind: str) -> int:
    return sum(1 for record in records if record.get("kind") == kind)


def _pass_rate(records: Sequence[Mapping[str, Any]]) -> dict[str, float | int]:
    total = sum(1 for record in records if "accepted" in record)
    accepted = sum(1 for record in records if record.get("accepted") is True)
    return {
        "accepted": accepted,
        "rate": 0.0 if total == 0 else accepted / total,
        "total": total,
    }


def _rejected_reason_distribution(
    ideas: Sequence[IdeaSpec],
    records: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    reasons: dict[str, int] = {}
    for idea in ideas:
        if idea.rejection_reason:
            reasons[idea.rejection_reason] = reasons.get(idea.rejection_reason, 0) + 1
    for record in records:
        if record.get("accepted") is False:
            reason = record.get("rejection_reason")
            if isinstance(reason, str) and reason.strip():
                normalized = reason.strip()
                reasons[normalized] = reasons.get(normalized, 0) + 1
    return dict(sorted(reasons.items()))


def _source_success_rate(
    ideas: Sequence[IdeaSpec],
    records: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, float | int]]:
    accepted_by_idea: dict[str, bool] = {}
    for record in records:
        idea_id = record.get("idea_id")
        if isinstance(idea_id, str) and "accepted" in record:
            accepted_by_idea.setdefault(idea_id, False)
            accepted_by_idea[idea_id] = accepted_by_idea[idea_id] or record.get("accepted") is True

    source_counts: dict[str, dict[str, int]] = {}
    for idea in ideas:
        counts = source_counts.setdefault(idea.source, {"accepted": 0, "total": 0})
        counts["total"] += 1
        accepted = accepted_by_idea.get(
            idea.idea_id,
            idea.status in {"accepted", "paper_candidate", "promotion_review"},
        )
        if accepted:
            counts["accepted"] += 1
    return {
        source: {
            "accepted": counts["accepted"],
            "rate": 0.0 if counts["total"] == 0 else counts["accepted"] / counts["total"],
            "total": counts["total"],
        }
        for source, counts in sorted(source_counts.items())
    }


def _edge_type_distribution(ideas: Sequence[IdeaSpec]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for idea in ideas:
        counts[idea.edge_type] = counts.get(idea.edge_type, 0) + 1
    return dict(sorted(counts.items()))


def _trial_count_outliers(
    ideas: Sequence[IdeaSpec],
    *,
    threshold: int,
) -> tuple[dict[str, int | str], ...]:
    return tuple(
        {"idea_id": idea.idea_id, "trial_count": idea.trial_count}
        for idea in sorted(ideas, key=lambda item: (-item.trial_count, item.idea_id))
        if idea.trial_count > threshold
    )


def _markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Meta-Research Summary",
        "",
        f"- period: {payload['period']}",
        f"- period_start: {payload['period_start']}",
        f"- ideas_created: {payload['ideas_created']}",
        f"- factor_candidates: {payload['factor_candidates']}",
        f"- strategy_prototypes: {payload['strategy_prototypes']}",
        f"- paper_candidate_count: {payload['paper_candidate_count']}",
        "",
        "```json",
        json.dumps(payload, sort_keys=True, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


__all__ = ["MetaResearchArtifacts", "MetaResearchSummary", "MetaResearchSummaryWriter"]
