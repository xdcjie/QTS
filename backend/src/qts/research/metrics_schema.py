"""Field-level research metrics schema validation."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


@dataclass(frozen=True, slots=True)
class ResearchMetricDefinition:
    """One metric field definition in a research metrics schema."""

    path: str
    type: str
    unit: str
    direction: str
    required_for: tuple[str, ...] = ()
    minimum: float | int | None = None
    maximum: float | int | None = None

    def __post_init__(self) -> None:
        path = self.path.strip()
        metric_type = self.type.strip()
        unit = self.unit.strip()
        direction = self.direction.strip()
        if not path or "." not in path:
            raise ValueError("metric path must use group.field form")
        if metric_type not in _SUPPORTED_TYPES:
            raise ValueError(f"unsupported metric type: {metric_type}")
        if not unit:
            raise ValueError(f"{path} unit is required")
        if direction not in _SUPPORTED_DIRECTIONS:
            raise ValueError(f"unsupported metric direction: {direction}")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "type", metric_type)
        object.__setattr__(self, "unit", unit)
        object.__setattr__(self, "direction", direction)
        object.__setattr__(self, "required_for", tuple(str(item) for item in self.required_for))
        for field_name in ("minimum", "maximum"):
            value = getattr(self, field_name)
            if isinstance(value, int | float) and not math.isfinite(value):
                raise ValueError(f"{path} {field_name} must be finite")

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchMetricDefinition:
        """Create a metric definition from a schema mapping."""

        return cls(
            path=str(payload.get("path", "")),
            type=str(payload.get("type", "")),
            unit=str(payload.get("unit", "")),
            direction=str(payload.get("direction", "")),
            required_for=tuple(payload.get("required_for") or ()),
            minimum=_optional_number(payload.get("minimum")),
            maximum=_optional_number(payload.get("maximum")),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready metric definition payload."""

        payload: dict[str, Any] = {
            "direction": self.direction,
            "path": self.path,
            "required_for": list(self.required_for),
            "type": self.type,
            "unit": self.unit,
        }
        if self.minimum is not None:
            payload["minimum"] = self.minimum
        if self.maximum is not None:
            payload["maximum"] = self.maximum
        return payload


@dataclass(frozen=True, slots=True)
class MetricsValidationResult:
    """Validation result for a research metrics payload."""

    accepted: bool
    passed: bool
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-safe validation result payload."""

        return {
            "accepted": self.accepted,
            "passed": self.passed,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class ResearchMetricsSchema:
    """Research metrics schema with field-level validation rules."""

    definitions: tuple[ResearchMetricDefinition, ...]
    schema_id: str
    schema_version: int = 2

    def __post_init__(self) -> None:
        schema_id = self.schema_id.strip()
        if not schema_id:
            raise ValueError("metrics schema_id is required")
        if self.schema_version != 2:
            raise ValueError("metrics schema_version must be 2")
        paths: set[str] = set()
        for definition in self.definitions:
            if definition.path in paths:
                raise ValueError(f"duplicate metric definition: {definition.path}")
            paths.add(definition.path)
        object.__setattr__(self, "schema_id", schema_id)

    @classmethod
    def from_yaml(cls, path: Path) -> ResearchMetricsSchema:
        """Load a v2 research metrics schema YAML file."""

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("metrics schema must be a YAML mapping")
        return cls.from_payload(payload)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchMetricsSchema:
        """Create a research metrics schema from a mapping."""

        schema_version = int(payload.get("schema_version", 0))
        raw_metrics = payload.get("metrics")
        if not isinstance(raw_metrics, Sequence) or isinstance(raw_metrics, str):
            raise ValueError("metrics must be a sequence")
        definitions = tuple(
            ResearchMetricDefinition.from_payload(item)
            for item in raw_metrics
            if isinstance(item, Mapping)
        )
        if len(definitions) != len(raw_metrics):
            raise ValueError("metric definitions must be mappings")
        return cls(
            definitions=definitions,
            schema_id=str(payload.get("schema_id", "")),
            schema_version=schema_version,
        )

    def validate(self, metrics: Mapping[str, Any], *, purpose: str) -> MetricsValidationResult:
        """Validate metrics for a declared purpose."""

        reasons: list[str] = []
        warnings: list[str] = []
        for definition in self.definitions:
            value = self._value_for(metrics, definition.path)
            required = purpose in definition.required_for
            if value is None:
                if required:
                    reasons.append(f"{definition.path} missing for {purpose}")
                continue
            if not self._matches_type(value, definition.type):
                reasons.append(f"{definition.path} expected {definition.type}")
                continue
            if isinstance(value, int | float) and not isinstance(value, bool):
                if not math.isfinite(value):
                    reasons.append(f"{definition.path} must be finite")
                    continue
                if definition.minimum is not None and value < definition.minimum:
                    reasons.append(f"{definition.path} below minimum {definition.minimum}")
                if definition.maximum is not None and value > definition.maximum:
                    reasons.append(f"{definition.path} above maximum {definition.maximum}")
        return MetricsValidationResult(
            accepted=not reasons,
            passed=not reasons,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    def definition_for(self, path: str) -> ResearchMetricDefinition | None:
        """Return the metric definition for a path, if present."""

        for definition in self.definitions:
            if definition.path == path:
                return definition
        return None

    @staticmethod
    def _value_for(metrics: Mapping[str, Any], path: str) -> Any:
        group, field_name = path.split(".", 1)
        group_value = metrics.get(group)
        if not isinstance(group_value, Mapping):
            return None
        return group_value.get(field_name)

    @staticmethod
    def _matches_type(value: Any, expected_type: str) -> bool:
        if expected_type == "bool":
            return isinstance(value, bool)
        if expected_type == "int":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "float":
            return isinstance(value, int | float) and not isinstance(value, bool)
        if expected_type == "str":
            return isinstance(value, str)
        return False


def _optional_number(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("numeric bounds must not be bool")
    if isinstance(value, int | float):
        if not math.isfinite(value):
            raise ValueError("numeric bounds must be finite")
        return value
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("numeric bounds must be finite")
    return result


_SUPPORTED_TYPES = frozenset({"bool", "float", "int", "str"})
_SUPPORTED_DIRECTIONS = frozenset({"higher_is_better", "lower_is_better", "neutral"})


__all__ = [
    "MetricsValidationResult",
    "ResearchMetricDefinition",
    "ResearchMetricsSchema",
]
