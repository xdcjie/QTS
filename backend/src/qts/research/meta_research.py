"""Read-only meta-research summaries for completed research evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

from qts.research.evidence_registry import EvidenceRegistry, ResearchEvidenceBundle
from qts.research.experiment_store import ExperimentStore, ExperimentStoreRecord
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
        period_end: date | None = None,
        all_history: bool = False,
        trial_count_outlier_threshold: int = 10,
    ) -> MetaResearchSummary:
        """Build a read-only summary from idea, evidence, and experiment records."""

        resolved_period_end = _period_end(period, period_start, period_end)
        idea_tuple = tuple(
            ideas
            if all_history
            else (
                idea
                for idea in ideas
                if _datetime_in_period(
                    idea.created_at,
                    period_start=period_start,
                    period_end=resolved_period_end,
                )
            )
        )
        evidence_tuple = tuple(
            record
            for record in (dict(record) for record in evidence_records)
            if all_history
            or _record_in_period(record, period_start=period_start, period_end=resolved_period_end)
        )
        experiment_tuple = tuple(
            record
            for record in (dict(record) for record in experiment_records)
            if all_history
            or _record_in_period(record, period_start=period_start, period_end=resolved_period_end)
        )
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

    @staticmethod
    def evidence_records_from_registry(
        registry: EvidenceRegistry,
    ) -> tuple[dict[str, Any], ...]:
        """Return meta-research records derived from persisted evidence bundles."""

        return tuple(_evidence_bundle_record(bundle) for bundle in registry.list())

    @staticmethod
    def experiment_records_from_store(
        store: ExperimentStore,
    ) -> tuple[dict[str, Any], ...]:
        """Return meta-research records derived from persisted experiment records."""

        return tuple(_experiment_store_record(record) for record in store.list_runs())

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


def _evidence_bundle_record(bundle: ResearchEvidenceBundle) -> dict[str, Any]:
    record: dict[str, Any] = {
        "evidence_bundle_id": bundle.evidence_bundle_id,
        "idea_id": bundle.idea_id,
        "kind": "strategy_prototype" if bundle.strategy_id else "evidence_bundle",
        "strategy_id": bundle.strategy_id,
        "workflow_run_id": bundle.workflow_run_id,
    }
    decision = bundle.review_decisions[-1] if bundle.review_decisions else {}
    if decision:
        status = str(decision.get("status", "")).strip()
        reviewed_at = decision.get("reviewed_at")
        if isinstance(reviewed_at, str) and reviewed_at.strip():
            record["reviewed_at"] = reviewed_at.strip()
        if status in {"paper_candidate", "small_live_candidate"}:
            record["accepted"] = True
        elif status in {"reject", "rejected", "retire", "retired"}:
            record["accepted"] = False
            record["rejection_reason"] = _decision_reason(decision) or status
    return record


def _experiment_store_record(record: ExperimentStoreRecord) -> dict[str, Any]:
    payload = record.to_payload()
    accepted = record.metrics.get("accepted")
    if isinstance(accepted, bool):
        payload["accepted"] = accepted
    return payload


def _decision_reason(decision: Mapping[str, Any]) -> str | None:
    reason = decision.get("reason")
    if isinstance(reason, str) and reason.strip():
        return reason.strip()
    if isinstance(reason, Sequence) and not isinstance(reason, str):
        for item in reason:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return None


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
        edge_types = getattr(idea, "edge_types", ()) or (idea.edge_type,)
        for edge_type in edge_types:
            counts[str(edge_type)] = counts.get(str(edge_type), 0) + 1
    return dict(sorted(counts.items()))


def _period_end(period: str, period_start: date, period_end: date | None) -> date:
    if period == "monthly":
        year = period_start.year + (1 if period_start.month == 12 else 0)
        month = 1 if period_start.month == 12 else period_start.month + 1
        return date(year, month, 1)
    if period == "quarterly":
        next_month = ((period_start.month - 1) // 3 + 1) * 3 + 1
        year = period_start.year + (1 if next_month > 12 else 0)
        month = next_month - 12 if next_month > 12 else next_month
        return date(year, month, 1)
    if period == "custom":
        if period_end is None:
            raise ValueError("custom meta-research period requires period_end")
        if period_start >= period_end:
            raise ValueError("period_start must be before period_end")
        return period_end
    raise ValueError("period must be monthly, quarterly, or custom")


def _record_in_period(
    record: Mapping[str, Any],
    *,
    period_start: date,
    period_end: date,
) -> bool:
    record_time = _record_time(record)
    if record_time is None:
        return True
    return _datetime_in_period(record_time, period_start=period_start, period_end=period_end)


def _record_time(record: Mapping[str, Any]) -> datetime | None:
    for key in ("recorded_at", "created_at", "reviewed_at"):
        value = record.get(key)
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value.strip():
            return _parse_datetime(value)
    decision = record.get("decision")
    if isinstance(decision, Mapping):
        reviewed_at = decision.get("reviewed_at")
        if isinstance(reviewed_at, str) and reviewed_at.strip():
            return _parse_datetime(reviewed_at)
    return None


def _parse_datetime(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if isinstance(parsed, datetime):
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return datetime.combine(parsed, time.min, tzinfo=UTC)


def _datetime_in_period(value: datetime, *, period_start: date, period_end: date) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    start = datetime.combine(period_start, time.min, tzinfo=UTC)
    end = datetime.combine(period_end, time.min, tzinfo=UTC)
    return start <= value.astimezone(UTC) < end


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
