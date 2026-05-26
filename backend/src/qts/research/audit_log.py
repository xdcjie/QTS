"""Function-level research audit log helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash


def audit_log_path(root_dir: Path) -> Path:
    """Return the audit JSONL index path."""

    return root_dir / "audit-log.jsonl"


def create_audit_record(
    *,
    record_type: str,
    payload: Mapping[str, Any],
    previous_payload_hash: str | None = None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Create one deterministic audit record payload."""

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
    return {
        "created_at": timestamp.isoformat(),
        "payload": dict(payload),
        "payload_hash": payload_hash,
        "previous_payload_hash": previous_payload_hash,
        "record_id": record_id,
        "record_type": record_type,
    }


def append_audit_record(
    root_dir: Path,
    *,
    record_type: str,
    payload: Mapping[str, Any],
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Append one audit record and return it."""

    records = list_audit_records(root_dir)
    previous_hash = None if not records else str(records[-1]["payload_hash"])
    record = create_audit_record(
        record_type=record_type,
        payload=payload,
        previous_payload_hash=previous_hash,
        created_at=created_at,
    )
    root_dir.mkdir(parents=True, exist_ok=True)
    with audit_log_path(root_dir).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def list_audit_records(root_dir: Path) -> tuple[dict[str, Any], ...]:
    """Return audit records in append order."""

    path = audit_log_path(root_dir)
    if not path.exists():
        return ()
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError("audit record row must be a JSON object")
        records.append(record)
    return tuple(records)


def verify_audit_log(root_dir: Path) -> tuple[str, ...]:
    """Return audit validation failures, or an empty tuple when valid."""

    reasons: list[str] = []
    previous_hash: str | None = None
    for index, record in enumerate(list_audit_records(root_dir)):
        payload = record.get("payload")
        if not isinstance(payload, Mapping):
            reasons.append(f"record {index} payload must be a mapping")
            continue
        actual_hash = stable_json_hash(payload)
        payload_hash = str(record.get("payload_hash"))
        if actual_hash != payload_hash:
            reasons.append(f"record {index} payload hash mismatch")
        if record.get("previous_payload_hash") != previous_hash:
            reasons.append(f"record {index} previous hash mismatch")
        created_at = datetime.fromisoformat(_required_text(record, "created_at"))
        expected_id = _record_id(
            record_type=_required_text(record, "record_type"),
            payload_hash=payload_hash,
            previous_payload_hash=(
                None if record.get("previous_payload_hash") is None else str(record.get("previous_payload_hash"))
            ),
            created_at=created_at,
        )
        if record.get("record_id") != expected_id:
            reasons.append(f"record {index} id mismatch")
        previous_hash = payload_hash
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


__all__ = [
    "append_audit_record",
    "audit_log_path",
    "create_audit_record",
    "list_audit_records",
    "verify_audit_log",
]
