"""Deterministic JSON hashing utilities."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from qts.core.ids import (
    AccountId,
    BrokerId,
    CausationId,
    CorrelationId,
    EventId,
    InstrumentId,
    OrderId,
    RuntimeInstanceId,
    RuntimeRunId,
    StrategyId,
)

_STRING_ID_TYPES = (
    AccountId,
    BrokerId,
    CausationId,
    CorrelationId,
    EventId,
    InstrumentId,
    OrderId,
    RuntimeInstanceId,
    RuntimeRunId,
    StrategyId,
)


def stable_json_default(value: object) -> object:
    """Adapter used by :func:`stable_json_dumps` for non-native JSON types."""

    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum) and isinstance(value.value, str):
        return value.value
    if isinstance(value, _STRING_ID_TYPES):
        return value.value
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def stable_json_dumps(payload: Any) -> str:
    """Serialize `payload` deterministically for stable hashing."""

    return json.dumps(
        payload,
        default=stable_json_default,
        sort_keys=True,
        separators=(",", ":"),
    )


def stable_json_hash(payload: Any) -> str:
    """Return a stable SHA-256 digest for a payload."""

    return f"sha256:{hashlib.sha256(stable_json_dumps(payload).encode()).hexdigest()}"


__all__ = ["stable_json_default", "stable_json_dumps", "stable_json_hash"]
