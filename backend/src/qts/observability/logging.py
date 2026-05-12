"""Structured logging helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from qts.domain.events import EventMetadata

SECRET_FIELD_MARKERS = ("password", "secret", "token", "credential", "api_key")
REDACTED = "[REDACTED]"


def build_log_record(
    *,
    level: str,
    message: str,
    metadata: EventMetadata | None = None,
    fields: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build a structured log record without exposing secret values."""

    if not level.strip():
        raise ValueError("level must not be empty")
    if not message.strip():
        raise ValueError("message must not be empty")

    record: dict[str, object] = {
        "level": level,
        "message": message,
    }
    if metadata is not None:
        record.update(_metadata_fields(metadata))
    if fields is not None:
        for key, value in fields.items():
            if not key.strip():
                raise ValueError("log field key must not be empty")
            record[key] = REDACTED if _is_secret_key(key) else value
    return record


def _metadata_fields(metadata: EventMetadata) -> dict[str, object]:
    """Perform _metadata_fields."""
    fields: dict[str, object] = {
        "event_id": str(metadata.event_id),
        "event_type": metadata.event_type,
        "event_time": metadata.event_time.isoformat(),
    }
    optional: dict[str, Any] = {
        "source_actor": metadata.source_actor,
        "target_actor": metadata.target_actor,
        "account_id": metadata.account_id,
        "strategy_id": metadata.strategy_id,
        "instrument_id": metadata.instrument_id,
        "order_id": metadata.order_id,
        "bar_time": metadata.bar_time.isoformat() if metadata.bar_time is not None else None,
        "seq": metadata.seq,
        "partition_key": metadata.partition_key,
        "correlation_id": metadata.correlation_id,
        "causation_id": metadata.causation_id,
    }
    for key, value in optional.items():
        if value is not None:
            fields[key] = str(value)
    return fields


def _is_secret_key(key: str) -> bool:
    """Perform _is_secret_key."""
    normalized = key.lower()
    return any(marker in normalized for marker in SECRET_FIELD_MARKERS)


__all__ = ["REDACTED", "build_log_record"]
