"""Versioned research metrics schema validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ResearchMetricDefinition:
    """Owns the validation contract for one research metric."""

    path: str
    value_type: str
    unit: str
    direction: str
    required: bool = False
    minimum: float | None = None
    maximum: float | None = None

    @classmethod
    def from_payload(cls, path: str, payload: Mapping[str, Any]) -> ResearchMetricDefinition:
        """Create a metric definition from a schema mapping."""

        return cls(
            path=path,
            value_type=_required_text(payload, "type"),
            unit=_required_text(payload, "unit"),
            direction=_required_text(payload, "direction"),
            required=bool(payload.get("required", False)),
            minimum=_optional_float(payload.get("minimum")),
            maximum=_optional_float(payload.get("maximum")),
        )

    def validate(self, metrics: Mapping[str, Any]) -> tuple[str, ...]:
        """Return validation failures for this metric path."""

        value = _nested_value(metrics, self.path)
        if value is None:
            return (f"{self.path} is required",) if self.required else ()
        if self.value_type == "float":
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                return (f"{self.path} must be a float",)
            reasons: list[str] = []
            if self.minimum is not None and parsed < self.minimum:
                reasons.append(f"{self.path} must be >= {self.minimum}")
            if self.maximum is not None and parsed > self.maximum:
                reasons.append(f"{self.path} must be <= {self.maximum}")
            return tuple(reasons)
        if self.value_type == "bool":
            return () if isinstance(value, bool) else (f"{self.path} must be a bool",)
        if self.value_type == "int":
            if isinstance(value, bool):
                return (f"{self.path} must be an int",)
            try:
                int(value)
            except (TypeError, ValueError):
                return (f"{self.path} must be an int",)
            return ()
        return (f"{self.path} has unsupported type {self.value_type}",)

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready schema metadata."""

        return {
            "direction": self.direction,
            "maximum": self.maximum,
            "minimum": self.minimum,
            "path": self.path,
            "required": self.required,
            "type": self.value_type,
            "unit": self.unit,
        }


@dataclass(frozen=True, slots=True)
class ResearchMetricsSchema:
    """Owns a versioned research metrics schema."""

    schema_version: int
    definitions: tuple[ResearchMetricDefinition, ...]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchMetricsSchema:
        """Create a schema from YAML/JSON-compatible payload."""

        version = int(payload.get("schema_version", 0))
        if version < 1:
            raise ValueError("schema_version must be positive")
        raw_metrics = payload.get("metrics")
        if not isinstance(raw_metrics, Mapping) or not raw_metrics:
            raise ValueError("metrics schema requires metric definitions")
        definitions = []
        for path in sorted(raw_metrics):
            item = raw_metrics[path]
            if not isinstance(item, Mapping):
                raise ValueError(f"metrics.{path} must be a mapping")
            definitions.append(ResearchMetricDefinition.from_payload(str(path), item))
        return cls(schema_version=version, definitions=tuple(definitions))

    @classmethod
    def default_v2(cls) -> ResearchMetricsSchema:
        """Return the default promotion-oriented metrics schema."""

        return cls.from_payload(DEFAULT_METRICS_SCHEMA_V2)

    def validate(self, metrics: Mapping[str, Any]) -> tuple[str, ...]:
        """Return schema validation failures."""

        reasons: list[str] = []
        for definition in self.definitions:
            reasons.extend(definition.validate(metrics))
        return tuple(reasons)

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready schema payload."""

        return {
            "definitions": [definition.to_payload() for definition in self.definitions],
            "schema_version": self.schema_version,
        }


DEFAULT_METRICS_SCHEMA_V2: dict[str, Any] = {
    "schema_version": 2,
    "metrics": {
        "execution.cost_impact": {
            "direction": "lower_is_better",
            "maximum": 1.0,
            "minimum": 0.0,
            "required": True,
            "type": "float",
            "unit": "return_fraction",
        },
        "execution.slippage_sensitivity": {
            "direction": "lower_is_better",
            "minimum": 0.0,
            "required": True,
            "type": "float",
            "unit": "return_fraction",
        },
        "portfolio.correlation_to_active": {
            "direction": "lower_abs_is_better",
            "maximum": 1.0,
            "minimum": -1.0,
            "required": True,
            "type": "float",
            "unit": "correlation",
        },
        "quality.profit_factor": {
            "direction": "higher_is_better",
            "minimum": 0.0,
            "required": True,
            "type": "float",
            "unit": "ratio",
        },
        "quality.sharpe": {
            "direction": "higher_is_better",
            "required": True,
            "type": "float",
            "unit": "ratio",
        },
        "research.deterministic_replay_passed": {
            "direction": "must_be_true",
            "required": True,
            "type": "bool",
            "unit": "boolean",
        },
        "research.no_lookahead_passed": {
            "direction": "must_be_true",
            "required": True,
            "type": "bool",
            "unit": "boolean",
        },
        "risk.max_drawdown": {
            "direction": "lower_is_better",
            "maximum": 1.0,
            "minimum": 0.0,
            "required": True,
            "type": "float",
            "unit": "absolute_fraction",
        },
        "stability.parameter_sensitivity": {
            "direction": "higher_is_better",
            "minimum": 0.0,
            "required": True,
            "type": "float",
            "unit": "stability_score",
        },
        "stability.walk_forward_consistency": {
            "direction": "higher_is_better",
            "minimum": 0.0,
            "required": True,
            "type": "float",
            "unit": "consistency_score",
        },
        "trading.oos_months": {
            "direction": "higher_is_better",
            "minimum": 0.0,
            "required": True,
            "type": "float",
            "unit": "months",
        },
        "trading.oos_trade_count": {
            "direction": "higher_is_better",
            "minimum": 0.0,
            "required": True,
            "type": "float",
            "unit": "trades",
        },
    },
}


def _nested_value(payload: Mapping[str, Any], path: str) -> Any:
    group, _, field_name = path.partition(".")
    group_value = payload.get(group)
    if not isinstance(group_value, Mapping):
        return None
    return group_value.get(field_name)


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


__all__ = [
    "DEFAULT_METRICS_SCHEMA_V2",
    "ResearchMetricDefinition",
    "ResearchMetricsSchema",
]
