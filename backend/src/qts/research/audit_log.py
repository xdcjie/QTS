"""Research audit log records for evidence and promotion decisions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash


@dataclass(frozen=True, slots=True)
class ResearchAuditRecord:
    """Owns one immutable research audit row."""

    record_id: str
    record_type: str
    payload_hash: str
    previous_payload_hash: str | None
    created_at: datetime
    payload: Mapping[str, Any]

    @classmethod
    def create(
        cls,
        *,
        record_type: str,
        payload: Mapping[str, Any],
        previous_payload_hash: str | None = None,
        created_at: datetime | None = None,
    ) -> ResearchAuditRecord:
        """Create one deterministic audit record."""

        record_type = record_type.strip()
        if not record_type:
            raise ValueError("record_type is required")
        timestamp = datetime.now(UTC) if created_at is None else created_at
        if timestamp.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        payload_hash = stable_json_hash(payload)
        record_id = _record_id(
            record_type=record_type,
            payload_hash=payload_hash,
            previous_payload_hash=previous_payload_hash,
            created_at=timestamp,
        )
        return cls(
            record_id=record_id,
            record_type=record_type,
            payload_hash=payload_hash,
            previous_payload_hash=previous_payload_hash,
            created_at=timestamp,
            payload=dict(payload),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchAuditRecord:
        """Rehydrate an audit record from JSON payload."""

        created_at = datetime.fromisoformat(_required_text(payload, "created_at"))
        if created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        raw_payload = payload.get("payload")
        if not isinstance(raw_payload, Mapping):
            raise ValueError("payload must be a mapping")
        previous = payload.get("previous_payload_hash")
        return cls(
            record_id=_required_text(payload, "record_id"),
            record_type=_required_text(payload, "record_type"),
            payload_hash=_required_text(payload, "payload_hash"),
            previous_payload_hash=None if previous is None else str(previous),
            created_at=created_at,
            payload=dict(raw_payload),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready audit row."""

        return {
            "created_at": self.created_at.isoformat(),
            "payload": dict(self.payload),
            "payload_hash": self.payload_hash,
            "previous_payload_hash": self.previous_payload_hash,
            "record_id": self.record_id,
            "record_type": self.record_type,
        }


class ResearchAuditLog:
    """Owns append-only JSONL research audit records."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    @property
    def index_path(self) -> Path:
        """Return the audit JSONL index path."""

        return self.root_dir / "audit-log.jsonl"

    def append(
        self,
        *,
        record_type: str,
        payload: Mapping[str, Any],
        created_at: datetime | None = None,
    ) -> ResearchAuditRecord:
        """Append one audit record."""

        records = self.list()
        previous_hash = None if not records else records[-1].payload_hash
        record = ResearchAuditRecord.create(
            record_type=record_type,
            payload=payload,
            previous_payload_hash=previous_hash,
            created_at=created_at,
        )
        self.root_dir.mkdir(parents=True, exist_ok=True)
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_payload(), sort_keys=True) + "\n")
        return record

    def list(self) -> tuple[ResearchAuditRecord, ...]:
        """Return audit records in append order."""

        if not self.index_path.exists():
            return ()
        records: list[ResearchAuditRecord] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(ResearchAuditRecord.from_payload(json.loads(line)))
        return tuple(records)

    def verify(self) -> tuple[str, ...]:
        """Return audit validation failures, or an empty tuple when valid."""

        reasons: list[str] = []
        previous_hash: str | None = None
        for index, record in enumerate(self.list()):
            actual_hash = stable_json_hash(record.payload)
            if actual_hash != record.payload_hash:
                reasons.append(f"record {index} payload hash mismatch")
            if record.previous_payload_hash != previous_hash:
                reasons.append(f"record {index} previous hash mismatch")
            expected_id = _record_id(
                record_type=record.record_type,
                payload_hash=record.payload_hash,
                previous_payload_hash=record.previous_payload_hash,
                created_at=record.created_at,
            )
            if record.record_id != expected_id:
                reasons.append(f"record {index} id mismatch")
            previous_hash = record.payload_hash
        return tuple(reasons)


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _record_id(
    *,
    record_type: str,
    payload_hash: str,
    previous_payload_hash: str | None,
    created_at: datetime,
) -> str:
    seed = {
        "created_at": created_at.isoformat(),
        "payload_hash": payload_hash,
        "previous_payload_hash": previous_payload_hash,
        "record_type": record_type,
    }
    return f"rec_{stable_json_hash(seed).split(':', maxsplit=1)[1][:16]}"


__all__ = ["ResearchAuditLog", "ResearchAuditRecord"]
