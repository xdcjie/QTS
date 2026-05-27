"""Controlled strategy template and variant construction."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_hash
from qts.research.artifact_graph import ResearchArtifactNode
from qts.research.factory.factor_definition import FactorDefinition

FORBIDDEN_IMPORT_PREFIXES = (
    "ib_async",
    "ibapi",
    "importlib",
    "os",
    "qts.data.adapters",
    "qts.execution",
    "qts.portfolio",
    "qts.registry",
    "qts.risk",
    "qts.runtime",
    "subprocess",
    "sys",
)


@dataclass(frozen=True, slots=True)
class StrategyVariantValidationResult:
    """Validation result for a strategy template or variant request."""

    accepted: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StrategyTemplate:
    """Research-only template contract for strategy variant generation."""

    template_id: str
    family: str
    factor_definition: FactorDefinition
    strategy_entrypoint: str
    allowed_imports: tuple[str, ...]
    parameter_space: Mapping[str, Any]
    risk_assumptions: Mapping[str, Any]
    execution_assumptions: Mapping[str, Any]
    template_kind: str = "static"
    trial_budget: int | None = None
    manifest_template: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        template_id = self.template_id.strip()
        family = self.family.strip().lower()
        strategy_entrypoint = self.strategy_entrypoint.strip()
        allowed_imports = tuple(
            import_name.strip() for import_name in self.allowed_imports if import_name.strip()
        )
        template_kind = self.template_kind.strip().lower()
        if not template_id:
            raise ValueError("template_id is required")
        if not family:
            raise ValueError("family is required")
        if not strategy_entrypoint:
            raise ValueError("strategy_entrypoint is required")
        if not template_kind:
            raise ValueError("template_kind is required")
        object.__setattr__(self, "template_id", template_id)
        object.__setattr__(self, "family", family)
        object.__setattr__(self, "strategy_entrypoint", strategy_entrypoint)
        object.__setattr__(self, "allowed_imports", allowed_imports)
        object.__setattr__(self, "template_kind", template_kind)
        object.__setattr__(self, "parameter_space", dict(self.parameter_space))
        object.__setattr__(self, "risk_assumptions", dict(self.risk_assumptions))
        object.__setattr__(self, "execution_assumptions", dict(self.execution_assumptions))
        object.__setattr__(self, "manifest_template", dict(self.manifest_template))

    @classmethod
    def from_yaml(cls, path: str | Path) -> StrategyTemplate:
        """Load a strategy template from YAML."""

        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("strategy template YAML must contain a mapping")
        return cls.from_payload(payload)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> StrategyTemplate:
        """Create a strategy template from a JSON/YAML mapping."""

        factor_definition = payload.get("factor_definition")
        if not isinstance(factor_definition, Mapping):
            raise ValueError("strategy template factor_definition must be a mapping")
        allowed_imports = payload.get("allowed_imports", ())
        if not isinstance(allowed_imports, Sequence) or isinstance(allowed_imports, str):
            raise ValueError("strategy template allowed_imports must be a sequence")
        parameter_space = payload.get("parameter_space", {})
        if not isinstance(parameter_space, Mapping):
            raise ValueError("strategy template parameter_space must be a mapping")
        risk_assumptions = payload.get("risk_assumptions", {})
        if not isinstance(risk_assumptions, Mapping):
            raise ValueError("strategy template risk_assumptions must be a mapping")
        execution_assumptions = payload.get("execution_assumptions", {})
        if not isinstance(execution_assumptions, Mapping):
            raise ValueError("strategy template execution_assumptions must be a mapping")
        manifest_template = payload.get("manifest_template", {})
        if not isinstance(manifest_template, Mapping):
            raise ValueError("strategy template manifest_template must be a mapping")
        return cls(
            template_id=str(payload.get("template_id", "")),
            family=str(payload.get("family", "")),
            factor_definition=FactorDefinition.from_payload(factor_definition),
            strategy_entrypoint=str(payload.get("strategy_entrypoint", "")),
            allowed_imports=tuple(str(item) for item in allowed_imports),
            parameter_space=parameter_space,
            risk_assumptions=risk_assumptions,
            execution_assumptions=execution_assumptions,
            template_kind=str(payload.get("template_kind", "static")),
            trial_budget=(
                None if payload.get("trial_budget") is None else int(payload["trial_budget"])
            ),
            manifest_template=manifest_template,
        )

    def validate(
        self,
        *,
        allowed_roots: Sequence[str] | None = None,
    ) -> StrategyVariantValidationResult:
        """Validate template boundaries before variant construction."""

        errors: list[str] = []
        factor_result = self.factor_definition.validate(allowed_roots=allowed_roots)
        errors.extend(f"factor_definition: {error}" for error in factor_result.errors)
        errors.extend(self._import_errors())
        errors.extend(self._parameter_space_errors())

        if not self.risk_assumptions:
            errors.append("risk_assumptions are required")
        if not self.execution_assumptions:
            errors.append("execution_assumptions are required")
        if self.template_kind != "static":
            errors.append("dynamic code generation is forbidden")
        if self.trial_budget is not None and self.trial_budget <= 0:
            errors.append("trial_budget must be positive")

        unique_errors = tuple(dict.fromkeys(errors))
        return StrategyVariantValidationResult(accepted=not unique_errors, errors=unique_errors)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready template payload."""

        return {
            "allowed_imports": list(self.allowed_imports),
            "execution_assumptions": dict(self.execution_assumptions),
            "factor_definition": self.factor_definition.to_payload(),
            "family": self.family,
            "manifest_template": dict(self.manifest_template),
            "parameter_space": self._parameter_space_payload(),
            "risk_assumptions": dict(self.risk_assumptions),
            "strategy_entrypoint": self.strategy_entrypoint,
            "template_id": self.template_id,
            "template_kind": self.template_kind,
            "trial_budget": self.trial_budget,
        }

    def finite_parameter_values(self, parameter_name: str) -> tuple[Any, ...] | None:
        """Return finite values for a parameter, if the dimension is finite."""

        value = self.parameter_space.get(parameter_name)
        if isinstance(value, Mapping):
            raw_values = value.get("values")
            if isinstance(raw_values, Sequence) and not isinstance(raw_values, str):
                return tuple(raw_values)
            return None
        if isinstance(value, Sequence) and not isinstance(value, str):
            return tuple(value)
        return None

    def _import_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        for import_name in self.allowed_imports:
            if self._is_forbidden_import(import_name):
                errors.append(f"forbidden import: {import_name}")
        return tuple(errors)

    def _parameter_space_errors(self) -> tuple[str, ...]:
        if not self.parameter_space:
            return ("parameter_space is required",)

        has_unbounded_dimension = False
        errors: list[str] = []
        for parameter_name, parameter_value in self.parameter_space.items():
            if not str(parameter_name).strip():
                errors.append("parameter_space parameter names must not be empty")
            if self._is_finite_dimension(parameter_value):
                if not self.finite_parameter_values(str(parameter_name)):
                    errors.append(f"parameter_space {parameter_name} must not be empty")
            else:
                has_unbounded_dimension = True

        if has_unbounded_dimension and (self.trial_budget is None or self.trial_budget <= 0):
            errors.append("parameter space must be finite or trial_budget must be positive")
        return tuple(errors)

    def _parameter_space_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for parameter_name, parameter_value in self.parameter_space.items():
            if isinstance(parameter_value, Mapping):
                payload[str(parameter_name)] = dict(parameter_value)
            elif isinstance(parameter_value, Sequence) and not isinstance(parameter_value, str):
                payload[str(parameter_name)] = list(parameter_value)
            else:
                payload[str(parameter_name)] = parameter_value
        return payload

    @staticmethod
    def _is_forbidden_import(import_name: str) -> bool:
        return any(
            import_name == prefix or import_name.startswith(f"{prefix}.")
            for prefix in FORBIDDEN_IMPORT_PREFIXES
        )

    @staticmethod
    def _is_finite_dimension(value: Any) -> bool:
        if isinstance(value, Mapping):
            raw_values = value.get("values")
            return isinstance(raw_values, Sequence) and not isinstance(raw_values, str)
        return isinstance(value, Sequence) and not isinstance(value, str)


@dataclass(frozen=True, slots=True)
class StrategyVariant:
    """One deterministic strategy variant artifact."""

    variant_id: str
    template_id: str
    family: str
    factor_id: str
    factor_hash: str
    strategy_entrypoint: str
    parameters: Mapping[str, Any]
    risk_assumptions: Mapping[str, Any]
    execution_assumptions: Mapping[str, Any]
    manifest_patch: Mapping[str, Any]

    def __post_init__(self) -> None:
        variant_id = self.variant_id.strip()
        if not variant_id:
            raise ValueError("variant_id is required")
        object.__setattr__(self, "variant_id", variant_id)
        object.__setattr__(self, "parameters", dict(sorted(self.parameters.items())))
        object.__setattr__(self, "risk_assumptions", dict(self.risk_assumptions))
        object.__setattr__(self, "execution_assumptions", dict(self.execution_assumptions))
        object.__setattr__(self, "manifest_patch", dict(self.manifest_patch))

    @property
    def variant_hash(self) -> str:
        """Return the deterministic hash of this strategy variant."""

        return stable_json_hash(self.to_payload(include_hash=False))

    def to_manifest_patch(self) -> dict[str, Any]:
        """Return the ManifestV2 patch represented by this variant."""

        return dict(self.manifest_patch)

    def to_payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        """Return a deterministic JSON-ready variant payload."""

        payload: dict[str, Any] = {
            "execution_assumptions": dict(self.execution_assumptions),
            "factor_hash": self.factor_hash,
            "factor_id": self.factor_id,
            "family": self.family,
            "manifest_patch": dict(self.manifest_patch),
            "parameters": dict(self.parameters),
            "risk_assumptions": dict(self.risk_assumptions),
            "strategy_entrypoint": self.strategy_entrypoint,
            "template_id": self.template_id,
            "variant_id": self.variant_id,
        }
        if include_hash:
            payload["strategy_variant_hash"] = self.variant_hash
        return payload

    def to_artifact_node(self) -> ResearchArtifactNode:
        """Return the ArtifactGraph node for this strategy variant."""

        return ResearchArtifactNode(
            node_id=self.variant_id,
            node_type="strategy_variant",
            payload_hash=self.variant_hash,
            metadata={
                "factor_hash": self.factor_hash,
                "factor_id": self.factor_id,
                "template_id": self.template_id,
            },
        )


@dataclass(frozen=True, slots=True)
class StrategyVariantFactory:
    """Creates strategy variants from static templates without code generation."""

    template: StrategyTemplate

    def create_variant(
        self,
        parameters: Mapping[str, Any],
        *,
        allowed_roots: Sequence[str] | None = None,
    ) -> StrategyVariant:
        """Validate inputs and return one deterministic strategy variant."""

        validation = self.template.validate(allowed_roots=allowed_roots)
        if not validation.accepted:
            raise ValueError("; ".join(validation.errors))
        normalized_parameters = dict(sorted(parameters.items()))
        self._require_parameters_in_space(normalized_parameters)
        variant_id = self._variant_id(normalized_parameters)
        manifest_patch = self._manifest_patch(variant_id, normalized_parameters)
        return StrategyVariant(
            variant_id=variant_id,
            template_id=self.template.template_id,
            family=self.template.family,
            factor_id=self.template.factor_definition.factor_id,
            factor_hash=self.template.factor_definition.factor_hash,
            strategy_entrypoint=self.template.strategy_entrypoint,
            parameters=normalized_parameters,
            risk_assumptions=self.template.risk_assumptions,
            execution_assumptions=self.template.execution_assumptions,
            manifest_patch=manifest_patch,
        )

    def _require_parameters_in_space(self, parameters: Mapping[str, Any]) -> None:
        expected_names = set(self.template.parameter_space)
        actual_names = set(parameters)
        if actual_names != expected_names:
            missing = sorted(expected_names - actual_names)
            extra = sorted(actual_names - expected_names)
            details: list[str] = []
            if missing:
                details.append(f"missing parameters: {', '.join(missing)}")
            if extra:
                details.append(f"unknown parameters: {', '.join(extra)}")
            raise ValueError("; ".join(details))

        for parameter_name, parameter_value in parameters.items():
            finite_values = self.template.finite_parameter_values(parameter_name)
            if finite_values is not None and parameter_value not in finite_values:
                raise ValueError(f"parameter {parameter_name} is outside the template space")

    def _variant_id(self, parameters: Mapping[str, Any]) -> str:
        digest = stable_json_hash(
            {
                "factor_hash": self.template.factor_definition.factor_hash,
                "parameters": dict(parameters),
                "template_id": self.template.template_id,
            }
        ).split(":", maxsplit=1)[1]
        return f"{self.template.template_id}_{digest[:16]}"

    def _manifest_patch(self, variant_id: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
        return {
            **dict(self.template.manifest_template),
            "execution": {
                "assumptions": dict(self.template.execution_assumptions),
            },
            "research_factory": {
                "factor_hash": self.template.factor_definition.factor_hash,
                "template_id": self.template.template_id,
            },
            "risk": {
                "assumptions": dict(self.template.risk_assumptions),
            },
            "strategy": {
                "entrypoint": self.template.strategy_entrypoint,
                "id": variant_id,
                "parameters": dict(parameters),
            },
        }


__all__ = [
    "StrategyTemplate",
    "StrategyVariant",
    "StrategyVariantFactory",
    "StrategyVariantValidationResult",
]
