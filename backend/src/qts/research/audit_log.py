"""Append-only Research OS audit ledger."""

from __future__ import annotations

import json
from collections.abc import Mapping, MutableSequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash

_SUPPORTED_RECORD_TYPES = frozenset(
    {
        "manifest_loaded",
        "research_run_completed",
        "evidence_bundle_created",
        "evidence_validated",
        "metrics_validated",
        "data_quality_validated",
        "reproducibility_validated",
        "promotion_packet_validated",
        "artifact_graph_verified",
        "human_review_decided",
        "artifact_graph_written",
        "report_projected",
        "campaign_loaded",
        "campaign_run_completed",
        "campaign_resumed",
        "campaign_stopped",
        "trial_budget_decision",
        "experiment_trial_completed",
        "experiment_trial_failed",
        "experiment_retry_scheduled",
        "selection_completed",
        "validation_gauntlet_completed",
        "fitness_landscape_updated",
        "next_generation_proposed",
        "generation_approval_decided",
    }
)


@dataclass(frozen=True, slots=True)
class ResearchAuditRecord:
    """One durable Research OS audit ledger row."""

    record_id: str
    record_type: str
    payload_hash: str
    previous_record_hash: str | None
    created_at: datetime
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        self._validate_record_type(self.record_type)
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        object.__setattr__(self, "payload", self._json_safe_payload(self.payload))

    @classmethod
    def create(
        cls,
        record_type: str,
        payload: Mapping[str, Any],
        *,
        previous_record_hash: str | None = None,
        created_at: datetime | None = None,
        record_id: str | None = None,
    ) -> ResearchAuditRecord:
        """Create one audit record with deterministic payload and record hashes."""

        cls._validate_record_type(record_type)
        timestamp = created_at or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        json_payload = cls._json_safe_payload(payload)
        payload_hash = stable_json_hash(json_payload)
        record_hash = cls._record_hash(
            record_type=record_type,
            payload_hash=payload_hash,
            previous_record_hash=previous_record_hash,
            created_at=timestamp,
            payload=json_payload,
        )
        if record_id is not None and record_id != record_hash:
            raise ValueError("record_id must match record_hash")
        return cls(
            record_id=record_id or record_hash,
            record_type=record_type,
            payload_hash=payload_hash,
            previous_record_hash=previous_record_hash,
            created_at=timestamp,
            payload=json_payload,
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchAuditRecord:
        """Rehydrate an audit record from a JSON-safe payload."""

        created_at = datetime.fromisoformat(cls._required_text(payload, "created_at"))
        return cls(
            record_id=cls._required_text(payload, "record_id"),
            record_type=cls._required_text(payload, "record_type"),
            payload_hash=cls._required_text(payload, "payload_hash"),
            previous_record_hash=cls._optional_text(payload, "previous_record_hash"),
            created_at=created_at,
            payload=cls._required_mapping(payload, "payload"),
        )

    @property
    def record_hash(self) -> str:
        """Return the deterministic hash of the record content."""

        return self._record_hash(
            record_type=self.record_type,
            payload_hash=self.payload_hash,
            previous_record_hash=self.previous_record_hash,
            created_at=self.created_at,
            payload=self.payload,
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready audit record payload."""

        return {
            "created_at": self.created_at.isoformat(),
            "payload": dict(self.payload),
            "payload_hash": self.payload_hash,
            "previous_record_hash": self.previous_record_hash,
            "record_id": self.record_id,
            "record_type": self.record_type,
        }

    @classmethod
    def expected_payload_hash(cls, payload: Mapping[str, Any]) -> str:
        """Return the canonical payload hash expected for a record payload."""

        return stable_json_hash(cls._json_safe_payload(payload))

    @classmethod
    def _record_hash(
        cls,
        *,
        record_type: str,
        payload_hash: str,
        previous_record_hash: str | None,
        created_at: datetime,
        payload: Mapping[str, Any],
    ) -> str:
        return stable_json_hash(
            {
                "created_at": created_at.isoformat(),
                "payload": cls._json_safe_payload(payload),
                "payload_hash": payload_hash,
                "previous_record_hash": previous_record_hash,
                "record_type": record_type,
            }
        )

    @staticmethod
    def _validate_record_type(record_type: str) -> None:
        if record_type not in _SUPPORTED_RECORD_TYPES:
            raise ValueError(f"unknown audit record_type: {record_type}")

    @staticmethod
    def _json_safe_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be a JSON object")
        loaded = json.loads(stable_json_dumps(dict(payload)))
        if not isinstance(loaded, dict):
            raise ValueError("payload must be a JSON object")
        return loaded

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} is required")
        return value

    @staticmethod
    def _optional_text(payload: Mapping[str, Any], field_name: str) -> str | None:
        value = payload.get(field_name)
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} must be a non-empty string or null")
        return value

    @staticmethod
    def _required_mapping(payload: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
        value = payload.get(field_name)
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a JSON object")
        return value


class ResearchAuditLog:
    """Owns appending, reading, and verifying a Research OS JSONL audit ledger."""

    def __init__(self, root_or_path: str | Path) -> None:
        path = Path(root_or_path)
        self.path = path if path.suffix == ".jsonl" else path / "audit_log.jsonl"

    def append(
        self,
        record_type: str,
        payload: Mapping[str, Any],
        *,
        created_at: datetime | None = None,
        record_id: str | None = None,
    ) -> ResearchAuditRecord:
        """Append one audit record and return the persisted record."""

        records = self.list()
        previous_record_hash = records[-1].record_hash if records else None
        record = ResearchAuditRecord.create(
            record_type,
            payload,
            previous_record_hash=previous_record_hash,
            created_at=created_at,
            record_id=record_id,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_payload(), sort_keys=True) + "\n")
        return record

    def append_human_review_decision(
        self,
        *,
        reviewer: str,
        decision: str,
        reviewed_at: datetime,
        evidence_bundle_id: str | None = None,
        promotion_candidate_id: str | None = None,
        notes: str | None = None,
    ) -> ResearchAuditRecord:
        """Append a validated human promotion-review decision record."""

        if reviewed_at.tzinfo is None or reviewed_at.tzinfo.utcoffset(reviewed_at) is None:
            raise ValueError("reviewed_at must be timezone-aware")
        payload: dict[str, Any] = {
            "decision": self._required_payload_text(decision, "decision"),
            "reviewed_at": reviewed_at.isoformat(),
            "reviewer": self._required_payload_text(reviewer, "reviewer"),
        }
        resolved_evidence_bundle_id = self._optional_payload_text(
            evidence_bundle_id,
            "evidence_bundle_id",
        )
        resolved_promotion_candidate_id = self._optional_payload_text(
            promotion_candidate_id,
            "promotion_candidate_id",
        )
        if resolved_evidence_bundle_id is None and resolved_promotion_candidate_id is None:
            raise ValueError("evidence_bundle_id or promotion_candidate_id is required")
        if resolved_evidence_bundle_id is not None:
            payload["evidence_bundle_id"] = resolved_evidence_bundle_id
        if resolved_promotion_candidate_id is not None:
            payload["promotion_candidate_id"] = resolved_promotion_candidate_id
        if notes is not None:
            payload["notes"] = str(notes).strip()
        return self.append("human_review_decided", payload)

    def list(self) -> tuple[ResearchAuditRecord, ...]:
        """Read all audit records in ledger file order."""

        if not self.path.exists():
            return ()
        records: list[ResearchAuditRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(ResearchAuditRecord.from_payload(json.loads(line)))
        return tuple(records)

    def verify_hash_chain(self) -> tuple[str, ...]:
        """Verify ledger payload hashes and previous-record links."""

        if not self.path.exists():
            return ()
        reasons: list[str] = []
        previous_record_hash: str | None = None
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = self._parse_record(line, line_number, reasons)
            if record is None:
                previous_record_hash = None
                continue
            expected_payload_hash = ResearchAuditRecord.expected_payload_hash(record.payload)
            if record.payload_hash != expected_payload_hash:
                reasons.append(
                    f"payload_hash mismatch at line {line_number}: "
                    f"expected {expected_payload_hash}, found {record.payload_hash}"
                )
            if record.previous_record_hash != previous_record_hash:
                reasons.append(
                    f"previous_record_hash mismatch at line {line_number}: "
                    f"expected {previous_record_hash}, found {record.previous_record_hash}"
                )
            if record.record_id != record.record_hash:
                reasons.append(
                    f"record_hash mismatch at line {line_number}: "
                    f"expected {record.record_hash}, found {record.record_id}"
                )
            previous_record_hash = record.record_hash
        return tuple(reasons)

    @staticmethod
    def _parse_record(
        line: str,
        line_number: int,
        reasons: MutableSequence[str],
    ) -> ResearchAuditRecord | None:
        try:
            payload = json.loads(line)
            if not isinstance(payload, Mapping):
                reasons.append(f"invalid JSON record at line {line_number}: expected object")
                return None
            return ResearchAuditRecord.from_payload(payload)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            reasons.append(f"invalid audit record at line {line_number}: {exc}")
            return None

    @staticmethod
    def _required_payload_text(value: str, field_name: str) -> str:
        resolved = str(value).strip()
        if not resolved:
            raise ValueError(f"{field_name} is required")
        return resolved

    @staticmethod
    def _optional_payload_text(value: str | None, field_name: str) -> str | None:
        if value is None:
            return None
        resolved = str(value).strip()
        if not resolved:
            return None
        return resolved


__all__ = ["ResearchAuditLog", "ResearchAuditRecord"]
