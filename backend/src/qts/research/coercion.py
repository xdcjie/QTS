"""Generic value-coercion helpers for research payload parsing.

Pure, instance-free type-coercion utilities (optional/required scalar, mapping,
tuple, and ISO date/datetime parsing) extracted from ResearchWorkflowRunner
(QTS-FINAL-011) so the duplicated private copies across research modules can
converge on one shared home.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any


def optional_decimal(value: Any, *, field_name: str = "value") -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal") from exc


def optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def optional_bool(value: Any, *, field_name: str = "value") -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def optional_non_negative_int(value: Any, *, field_name: str = "value") -> int | None:
    parsed = optional_int(value)
    if parsed is not None and parsed < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return parsed


def string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        raise ValueError("value must be a sequence")
    return tuple(str(item) for item in value)


def optional_string_tuple(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    return string_tuple(value)


def optional_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("value must be a mapping")
    return dict(value)


def required_mapping(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    value = payload.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def float_mapping(value: Any, *, field_name: str) -> dict[str, float]:
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"{field_name} must be a non-empty mapping")
    return {str(key): float(item) for key, item in value.items()}


def nested_float_mapping(
    value: Any,
    *,
    field_name: str,
) -> dict[str, dict[str, float]] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return {
        str(key): float_mapping(item, field_name=f"{field_name}.{key}")
        for key, item in value.items()
    }


def iso_date(value: Any, field_name: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO date") from exc


def iso_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=UTC)
    text = str(value)
    if len(text) == len("YYYY-MM-DD"):
        return datetime.combine(date.fromisoformat(text), time.min, tzinfo=UTC)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime or date") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


__all__ = [
    "float_mapping",
    "iso_date",
    "iso_datetime",
    "nested_float_mapping",
    "optional_bool",
    "optional_decimal",
    "optional_float",
    "optional_int",
    "optional_mapping",
    "optional_non_negative_int",
    "optional_string_tuple",
    "required_mapping",
    "string_tuple",
]
