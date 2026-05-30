"""Auditable research factor definition DSL."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Self, cast

from qts.core.hashing import stable_json_hash
from qts.research.artifact_graph import ResearchArtifactNode

SUPPORTED_FACTOR_FAMILIES = frozenset(
    {
        "momentum",
        "mean_reversion",
        "volatility",
        "carry",
        "spread_zscore",
        "breakout",
        "seasonality",
        "regime_filter",
        "liquidity",
        "order_flow",
    }
)

FUTURE_LOOKING_TRANSFORMS = frozenset(
    {
        "future_return",
        "forward_return",
        "future_shift",
        "lead",
        "lookahead",
    }
)

TRANSFORM_ALLOWED_PARAMETERS: Mapping[str, frozenset[str]] = {
    "identity": frozenset(),
    "returns": frozenset({"lookback"}),
    "price_change": frozenset({"lookback"}),
    "difference": frozenset(),
    "ratio": frozenset(),
    "rolling_mean": frozenset({"lookback"}),
    "rolling_std": frozenset({"lookback"}),
    "rolling_zscore": frozenset({"lookback"}),
    "rolling_min": frozenset({"lookback"}),
    "rolling_max": frozenset({"lookback"}),
    "rolling_rank": frozenset({"lookback"}),
    "rolling_breakout": frozenset({"lookback"}),
    "ewm_mean": frozenset({"span"}),
    "lag": frozenset({"lag_bars"}),
    "carry": frozenset({"lookback"}),
    "calendar_seasonality": frozenset({"bucket", "lookback"}),
    "regime_filter": frozenset({"lookback", "threshold"}),
    "liquidity_score": frozenset({"lookback"}),
    "order_flow_imbalance": frozenset({"lookback"}),
    "winsorize": frozenset({"lower_quantile", "upper_quantile"}),
    "clip": frozenset({"lower", "upper"}),
}

POSITIVE_NUMBER_PARAMETERS = frozenset({"horizon", "lag_bars", "lookback", "span"})
FUTURE_PARAMETER_NAMES = frozenset(
    {
        "forward_bars",
        "lead",
        "lead_bars",
        "lookahead",
        "lookahead_bars",
    }
)
VISIBLE_AFTER_VALUES = frozenset({"bar_close", "close", "session_close"})


@dataclass(frozen=True, slots=True)
class FactorDefinitionValidationResult:
    """Validation result for a research factor definition."""

    accepted: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FactorInput:
    """One named input series consumed by a factor definition."""

    root: str
    field: str

    def __post_init__(self) -> None:
        root = self.root.strip().upper()
        field = self.field.strip().lower()
        if not root:
            raise ValueError("root is required")
        if not field:
            raise ValueError("field is required")
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "field", field)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready payload."""

        return {
            "field": self.field,
            "root": self.root,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Self:
        """Rehydrate an input from a JSON/YAML payload."""

        return cls(root=str(payload.get("root", "")), field=str(payload.get("field", "")))


@dataclass(frozen=True, slots=True)
class FactorTransform:
    """One declarative, non-executable factor transform step."""

    transform_type: str
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        transform_type = self.transform_type.strip().lower()
        if not transform_type:
            raise ValueError("transform_type is required")
        normalized_parameters = {
            str(key).strip(): value for key, value in self.parameters.items() if str(key).strip()
        }
        object.__setattr__(self, "transform_type", transform_type)
        object.__setattr__(self, "parameters", normalized_parameters)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready payload."""

        payload: dict[str, Any] = {"type": self.transform_type}
        payload.update(dict(self.parameters))
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Self:
        """Rehydrate a transform from a JSON/YAML payload."""

        transform_type = str(payload.get("type", payload.get("transform_type", "")))
        parameters = {
            key: value for key, value in payload.items() if key not in {"type", "transform_type"}
        }
        return cls(transform_type=transform_type, parameters=parameters)

    def validation_errors(self) -> tuple[str, ...]:
        """Return transform validation errors without executing user code."""

        errors: list[str] = []
        if self.transform_type in FUTURE_LOOKING_TRANSFORMS:
            errors.append(f"transform {self.transform_type} references future data")
        elif self.transform_type not in TRANSFORM_ALLOWED_PARAMETERS:
            errors.append(f"unsupported transform: {self.transform_type}")

        allowed_parameters = TRANSFORM_ALLOWED_PARAMETERS.get(self.transform_type, frozenset())
        for parameter_name in self.parameters:
            if parameter_name in FUTURE_PARAMETER_NAMES:
                errors.append(f"transform {self.transform_type} references future data")
            if parameter_name not in allowed_parameters:
                errors.append(
                    f"transform {self.transform_type} has unexpected parameter: {parameter_name}"
                )

        for parameter_name in allowed_parameters & POSITIVE_NUMBER_PARAMETERS:
            if parameter_name in self.parameters and not self._positive_number(
                self.parameters[parameter_name]
            ):
                errors.append(
                    f"transform {self.transform_type} parameter {parameter_name} must be positive"
                )

        errors.extend(self._quantile_errors())
        return tuple(dict.fromkeys(errors))

    @staticmethod
    def _positive_number(value: Any) -> bool:
        if isinstance(value, bool):
            return False
        return isinstance(value, int | float) and value > 0

    def _quantile_errors(self) -> tuple[str, ...]:
        if self.transform_type != "winsorize":
            return ()
        lower = self.parameters.get("lower_quantile")
        upper = self.parameters.get("upper_quantile")
        errors: list[str] = []
        if not isinstance(lower, int | float) or not 0 <= lower < 1:
            errors.append("transform winsorize parameter lower_quantile must be in [0, 1)")
        if not isinstance(upper, int | float) or not 0 < upper <= 1:
            errors.append("transform winsorize parameter upper_quantile must be in (0, 1]")
        if isinstance(lower, int | float) and isinstance(upper, int | float) and lower >= upper:
            errors.append("transform winsorize lower_quantile must be < upper_quantile")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class FactorLabelPolicy:
    """Forward-label policy metadata for research evaluation."""

    horizon_bars: int
    visible_after: str
    no_lookahead: bool

    def __post_init__(self) -> None:
        visible_after = self.visible_after.strip().lower()
        if not visible_after:
            raise ValueError("visible_after is required")
        object.__setattr__(self, "visible_after", visible_after)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready payload."""

        return {
            "horizon_bars": self.horizon_bars,
            "no_lookahead": self.no_lookahead,
            "visible_after": self.visible_after,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Self:
        """Rehydrate a label policy from a JSON/YAML payload."""

        return cls(
            horizon_bars=int(payload.get("horizon_bars", 0)),
            visible_after=str(payload.get("visible_after", "")),
            no_lookahead=bool(payload.get("no_lookahead", False)),
        )

    def validation_errors(self) -> tuple[str, ...]:
        """Return label policy validation errors."""

        errors: list[str] = []
        if self.horizon_bars <= 0:
            errors.append("label_policy.horizon_bars must be positive")
        if self.visible_after not in VISIBLE_AFTER_VALUES:
            errors.append(f"unsupported label_policy.visible_after: {self.visible_after}")
        if not self.no_lookahead:
            errors.append("label_policy.no_lookahead must be true")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    """Owns validation, normalization, and hashing for one factor DSL object."""

    factor_id: str
    family: str
    inputs: tuple[FactorInput, ...]
    transforms: tuple[FactorTransform, ...]
    label_policy: FactorLabelPolicy | None
    source_idea_id: str | None = None

    def __post_init__(self) -> None:
        factor_id = self.factor_id.strip()
        family = self.family.strip().lower()
        source_idea_id = None if self.source_idea_id is None else self.source_idea_id.strip()
        if not factor_id:
            raise ValueError("factor_id is required")
        if not family:
            raise ValueError("family is required")
        object.__setattr__(self, "factor_id", factor_id)
        object.__setattr__(self, "family", family)
        object.__setattr__(self, "inputs", tuple(self.inputs))
        object.__setattr__(self, "transforms", tuple(self.transforms))
        object.__setattr__(self, "source_idea_id", source_idea_id or None)

    @property
    def factor_hash(self) -> str:
        """Return the deterministic hash of the normalized factor definition."""

        return stable_json_hash(self.to_payload(include_hash=False))

    def validate(
        self,
        *,
        allowed_roots: Sequence[str] | None = None,
    ) -> FactorDefinitionValidationResult:
        """Validate the definition against supported DSL and universe roots."""

        errors: list[str] = []
        if self.family not in SUPPORTED_FACTOR_FAMILIES:
            errors.append(f"unsupported factor family: {self.family}")
        if not self.inputs:
            errors.append("inputs must not be empty")
        if not self.transforms:
            errors.append("transforms must not be empty")

        allowed_root_set = self._allowed_root_set(allowed_roots)
        if allowed_root_set is not None:
            for factor_input in self.inputs:
                if factor_input.root not in allowed_root_set:
                    errors.append(f"unknown input root: {factor_input.root}")

        for transform in self.transforms:
            errors.extend(transform.validation_errors())

        if self.label_policy is None:
            errors.append("label_policy is required")
        else:
            errors.extend(self.label_policy.validation_errors())

        unique_errors = tuple(dict.fromkeys(errors))
        return FactorDefinitionValidationResult(accepted=not unique_errors, errors=unique_errors)

    def to_payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        """Return a deterministic JSON-ready factor definition."""

        payload: dict[str, Any] = {
            "factor_id": self.factor_id,
            "family": self.family,
            "inputs": [factor_input.to_payload() for factor_input in self.inputs],
            "label_policy": (None if self.label_policy is None else self.label_policy.to_payload()),
            "source_idea_id": self.source_idea_id,
            "transforms": [transform.to_payload() for transform in self.transforms],
        }
        if include_hash:
            payload["factor_hash"] = self.factor_hash
        return payload

    def to_artifact_node(self) -> ResearchArtifactNode:
        """Return the ArtifactGraph node for this factor definition."""

        return ResearchArtifactNode(
            node_id=self.factor_id,
            node_type="factor_definition",
            payload_hash=self.factor_hash,
            metadata={
                "family": self.family,
                "source_idea_id": self.source_idea_id,
            },
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Self:
        """Rehydrate a factor definition from a JSON/YAML payload."""

        raw_label_policy = payload.get("label_policy")
        label_policy = (
            None
            if raw_label_policy is None
            else FactorLabelPolicy.from_payload(cast(Mapping[str, Any], raw_label_policy))
        )
        return cls(
            factor_id=str(payload.get("factor_id", "")),
            family=str(payload.get("family", "")),
            inputs=tuple(
                FactorInput.from_payload(item) for item in cls._mapping_sequence(payload, "inputs")
            ),
            transforms=tuple(
                FactorTransform.from_payload(item)
                for item in cls._mapping_sequence(payload, "transforms")
            ),
            label_policy=label_policy,
            source_idea_id=cls._optional_text(payload.get("source_idea_id")),
        )

    @staticmethod
    def _allowed_root_set(allowed_roots: Sequence[str] | None) -> frozenset[str] | None:
        if allowed_roots is None:
            return None
        return frozenset(str(root).strip().upper() for root in allowed_roots if str(root).strip())

    @staticmethod
    def _mapping_sequence(
        payload: Mapping[str, Any],
        field_name: str,
    ) -> tuple[Mapping[str, Any], ...]:
        value = payload.get(field_name)
        if not isinstance(value, Sequence) or isinstance(value, str):
            return ()
        return tuple(item for item in value if isinstance(item, Mapping))

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


__all__ = [
    "SUPPORTED_FACTOR_FAMILIES",
    "FactorDefinition",
    "FactorDefinitionValidationResult",
    "FactorInput",
    "FactorLabelPolicy",
    "FactorTransform",
]
