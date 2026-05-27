"""Search-space definitions and deterministic candidate generation."""

from __future__ import annotations

import json
import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from itertools import product
from pathlib import Path
from typing import Any, ClassVar, Literal, cast

from qts.core.hashing import stable_json_dumps, stable_json_hash

SearchParameterType = Literal[
    "categorical",
    "int_range",
    "float_range",
    "log_float_range",
    "boolean",
]
SearchConstraintType = Literal["conditional", "forbidden_combination"]


@dataclass(frozen=True, slots=True)
class SearchParameter:
    """One dimension in an autonomous research search space."""

    name: str
    parameter_type: SearchParameterType
    values: tuple[Any, ...] = ()
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    step: Decimal | None = None

    _RANGE_TYPES: ClassVar[frozenset[str]] = frozenset(
        {"int_range", "float_range", "log_float_range"}
    )

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not normalized_name:
            raise ValueError("search parameter name must not be empty")
        object.__setattr__(self, "name", normalized_name)
        object.__setattr__(self, "values", tuple(self.values))
        self._validate_json_safe_values(self.values)
        if self.parameter_type == "categorical":
            self._validate_categorical()
        elif self.parameter_type == "boolean":
            self._validate_boolean()
        elif self.parameter_type == "int_range":
            self._validate_int_range()
        elif self.parameter_type == "float_range":
            self._validate_float_range()
        elif self.parameter_type == "log_float_range":
            self._validate_log_float_range()
        else:
            raise ValueError(f"unsupported search parameter type: {self.parameter_type!r}")

    @classmethod
    def categorical(cls, name: str, values: Sequence[Any]) -> SearchParameter:
        """Create a categorical parameter with values in deterministic grid order."""

        return cls(name=name, parameter_type="categorical", values=tuple(values))

    @classmethod
    def boolean(cls, name: str) -> SearchParameter:
        """Create a boolean parameter with ``False`` before ``True``."""

        return cls(name=name, parameter_type="boolean")

    @classmethod
    def int_range(
        cls,
        name: str,
        *,
        minimum: int,
        maximum: int,
        step: int | None = None,
    ) -> SearchParameter:
        """Create an integer range parameter.

        A missing ``step`` is valid only for budgeted random generation.
        """

        return cls(
            name=name,
            parameter_type="int_range",
            minimum=Decimal(minimum),
            maximum=Decimal(maximum),
            step=None if step is None else Decimal(step),
        )

    @classmethod
    def float_range(
        cls,
        name: str,
        *,
        minimum: str | int | float | Decimal,
        maximum: str | int | float | Decimal,
        step: str | int | float | Decimal | None = None,
    ) -> SearchParameter:
        """Create a bounded linear float range parameter."""

        return cls(
            name=name,
            parameter_type="float_range",
            minimum=cls._decimal(minimum),
            maximum=cls._decimal(maximum),
            step=None if step is None else cls._decimal(step),
        )

    @classmethod
    def log_float_range(
        cls,
        name: str,
        *,
        minimum: str | int | float | Decimal,
        maximum: str | int | float | Decimal,
        step: str | int | float | Decimal | None = None,
    ) -> SearchParameter:
        """Create a bounded log-space float range parameter."""

        return cls(
            name=name,
            parameter_type="log_float_range",
            minimum=cls._decimal(minimum),
            maximum=cls._decimal(maximum),
            step=None if step is None else cls._decimal(step),
        )

    @property
    def is_finite_grid_dimension(self) -> bool:
        """Return whether this parameter can be enumerated without a budget."""

        return self.finite_values() is not None

    def finite_values(self) -> tuple[Any, ...] | None:
        """Return deterministic grid values, or ``None`` for continuous dimensions."""

        if self.parameter_type == "categorical":
            return self.values
        if self.parameter_type == "boolean":
            return (False, True)
        if self.parameter_type == "int_range":
            if self.step is None:
                return None
            return self._finite_int_values()
        if self.parameter_type == "float_range":
            if self.step is None:
                return None
            return self._finite_decimal_values(multiplier=False)
        if self.parameter_type == "log_float_range":
            if self.step is None:
                return None
            return self._finite_decimal_values(multiplier=True)
        raise ValueError(f"unsupported search parameter type: {self.parameter_type!r}")

    def random_value(self, rng: random.Random) -> Any:
        """Return one deterministic random value from this parameter."""

        if self.parameter_type == "categorical":
            return rng.choice(self.values)
        if self.parameter_type == "boolean":
            return bool(rng.getrandbits(1))
        if self.parameter_type == "int_range":
            minimum_int = int(self._required_minimum())
            maximum_int = int(self._required_maximum())
            return rng.randint(minimum_int, maximum_int)
        if self.parameter_type == "float_range":
            minimum_decimal = self._required_minimum()
            maximum_decimal = self._required_maximum()
            unit = Decimal(str(rng.random()))
            return minimum_decimal + ((maximum_decimal - minimum_decimal) * unit)
        if self.parameter_type == "log_float_range":
            minimum_float = float(self._required_minimum())
            maximum_float = float(self._required_maximum())
            sampled = math.exp(rng.uniform(math.log(minimum_float), math.log(maximum_float)))
            return Decimal(str(sampled))
        raise ValueError(f"unsupported search parameter type: {self.parameter_type!r}")

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready parameter payload."""

        payload: dict[str, Any] = {
            "name": self.name,
            "parameter_type": self.parameter_type,
        }
        if self.values:
            payload["values"] = list(self.values)
        if self.minimum is not None:
            payload["minimum"] = self.minimum
        if self.maximum is not None:
            payload["maximum"] = self.maximum
        if self.step is not None:
            payload["step"] = self.step
        return cast("dict[str, Any]", json.loads(stable_json_dumps(payload)))

    def _validate_categorical(self) -> None:
        if not self.values:
            raise ValueError("categorical search parameter must contain values")
        if self.minimum is not None or self.maximum is not None or self.step is not None:
            raise ValueError("categorical search parameter cannot define range bounds")

    def _validate_boolean(self) -> None:
        if (
            self.values
            or self.minimum is not None
            or self.maximum is not None
            or self.step is not None
        ):
            raise ValueError("boolean search parameter cannot define values or range bounds")

    def _validate_int_range(self) -> None:
        self._validate_range_bounds()
        minimum = self._required_minimum()
        maximum = self._required_maximum()
        if minimum != minimum.to_integral_value() or maximum != maximum.to_integral_value():
            raise ValueError("int_range bounds must be integers")
        if self.step is not None:
            if self.step != self.step.to_integral_value():
                raise ValueError("int_range step must be an integer")
            if self.step <= 0:
                raise ValueError("int_range step must be positive")

    def _validate_float_range(self) -> None:
        self._validate_range_bounds()
        if self.step is not None and self.step <= 0:
            raise ValueError("float_range step must be positive")

    def _validate_log_float_range(self) -> None:
        self._validate_range_bounds()
        if self._required_minimum() <= 0 or self._required_maximum() <= 0:
            raise ValueError("log_float_range bounds must be positive")
        if self.step is not None and self.step <= 1:
            raise ValueError("log_float_range step must be greater than 1")

    def _validate_range_bounds(self) -> None:
        if self.values:
            raise ValueError(f"{self.parameter_type} search parameter cannot define values")
        minimum = self._required_minimum()
        maximum = self._required_maximum()
        if not minimum.is_finite() or not maximum.is_finite():
            raise ValueError(f"{self.parameter_type} bounds must be finite")
        if minimum > maximum:
            raise ValueError(f"{self.parameter_type} minimum must be <= maximum")

    def _finite_int_values(self) -> tuple[int, ...]:
        minimum = int(self._required_minimum())
        maximum = int(self._required_maximum())
        step = int(self._required_step())
        values = tuple(range(minimum, maximum + 1, step))
        if not values:
            raise ValueError("int_range finite grid produced no values")
        return values

    def _finite_decimal_values(self, *, multiplier: bool) -> tuple[Decimal, ...]:
        current = self._required_minimum()
        maximum = self._required_maximum()
        step = self._required_step()
        values: list[Decimal] = []
        while current <= maximum:
            values.append(current)
            current = current * step if multiplier else current + step
        if not values:
            raise ValueError(f"{self.parameter_type} finite grid produced no values")
        return tuple(values)

    def _required_minimum(self) -> Decimal:
        if self.minimum is None:
            raise ValueError(f"{self.parameter_type} minimum is required")
        return self.minimum

    def _required_maximum(self) -> Decimal:
        if self.maximum is None:
            raise ValueError(f"{self.parameter_type} maximum is required")
        return self.maximum

    def _required_step(self) -> Decimal:
        if self.step is None:
            raise ValueError(f"{self.parameter_type} step is required")
        return self.step

    @staticmethod
    def _decimal(value: str | int | float | Decimal) -> Decimal:
        return Decimal(str(value))

    @staticmethod
    def _validate_json_safe_values(values: Sequence[Any]) -> None:
        for value in values:
            stable_json_dumps(value)


@dataclass(frozen=True, slots=True)
class SearchConstraint:
    """A conditional activation or forbidden-combination search rule."""

    constraint_type: SearchConstraintType
    parameter: str | None = None
    when: Mapping[str, Any] = field(default_factory=dict)
    values: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.constraint_type == "conditional":
            if self.parameter is None or not self.parameter.strip():
                raise ValueError("conditional constraint parameter is required")
            if not self.when:
                raise ValueError("conditional constraint requires at least one predicate")
            object.__setattr__(self, "parameter", self.parameter.strip())
            object.__setattr__(self, "when", self._json_safe_mapping(self.when))
            object.__setattr__(self, "values", {})
        elif self.constraint_type == "forbidden_combination":
            if not self.values:
                raise ValueError("forbidden_combination constraint requires values")
            object.__setattr__(self, "parameter", None)
            object.__setattr__(self, "when", {})
            object.__setattr__(self, "values", self._json_safe_mapping(self.values))
        else:
            raise ValueError(f"unsupported search constraint type: {self.constraint_type!r}")

    @classmethod
    def conditional(cls, parameter: str, *, when: Mapping[str, Any]) -> SearchConstraint:
        """Create a rule that includes ``parameter`` only when predicates match."""

        return cls(constraint_type="conditional", parameter=parameter, when=when)

    @classmethod
    def forbidden_combination(cls, *, values: Mapping[str, Any]) -> SearchConstraint:
        """Create a rule that rejects candidates matching all provided values."""

        return cls(constraint_type="forbidden_combination", values=values)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready constraint payload."""

        payload: dict[str, Any] = {"constraint_type": self.constraint_type}
        if self.parameter is not None:
            payload["parameter"] = self.parameter
        if self.when:
            payload["when"] = dict(self.when)
        if self.values:
            payload["values"] = dict(self.values)
        return cast("dict[str, Any]", json.loads(stable_json_dumps(payload)))

    @staticmethod
    def _json_safe_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
        stable_json_dumps(dict(payload))
        return dict(payload)


@dataclass(frozen=True, slots=True)
class GeneratedCandidate:
    """One generated research candidate and its deterministic identity."""

    ordinal: int
    parameters: Mapping[str, Any]
    candidate_space_hash: str
    candidate_id: str

    @classmethod
    def create(
        cls,
        *,
        ordinal: int,
        parameters: Mapping[str, Any],
        candidate_space_hash: str,
    ) -> GeneratedCandidate:
        """Create a candidate with a deterministic hash identity."""

        normalized_parameters = cls._json_safe_mapping(parameters)
        candidate_id = stable_json_hash(
            {
                "candidate_space_hash": candidate_space_hash,
                "ordinal": ordinal,
                "parameters": normalized_parameters,
            }
        )
        return cls(
            ordinal=ordinal,
            parameters=normalized_parameters,
            candidate_space_hash=candidate_space_hash,
            candidate_id=candidate_id,
        )

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise ValueError("candidate ordinal must be non-negative")
        if not self.candidate_space_hash:
            raise ValueError("candidate_space_hash is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        object.__setattr__(self, "parameters", self._json_safe_mapping(self.parameters))

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready candidate payload."""

        return cast(
            "dict[str, Any]",
            json.loads(
                stable_json_dumps(
                    {
                        "candidate_id": self.candidate_id,
                        "candidate_space_hash": self.candidate_space_hash,
                        "ordinal": self.ordinal,
                        "parameters": dict(self.parameters),
                    }
                )
            ),
        )

    @staticmethod
    def _json_safe_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
        stable_json_dumps(dict(payload))
        return dict(payload)


@dataclass(frozen=True, slots=True)
class SearchSpaceSpec:
    """Complete deterministic search-space contract for candidate generation."""

    parameters: tuple[SearchParameter, ...]
    constraints: tuple[SearchConstraint, ...] = ()

    def __post_init__(self) -> None:
        if not self.parameters:
            raise ValueError("search space requires at least one parameter")
        object.__setattr__(self, "parameters", tuple(self.parameters))
        object.__setattr__(self, "constraints", tuple(self.constraints))
        names = [parameter.name for parameter in self.parameters]
        if len(set(names)) != len(names):
            raise ValueError("duplicate search parameter names are not allowed")
        self._validate_constraints(frozenset(names))

    @property
    def candidate_space_hash(self) -> str:
        """Return the deterministic hash of the candidate search space."""

        return stable_json_hash(self.to_payload())

    @property
    def is_finite_grid(self) -> bool:
        """Return whether every parameter can be exhaustively enumerated."""

        return all(parameter.is_finite_grid_dimension for parameter in self.parameters)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready search-space payload."""

        return {
            "constraints": [constraint.to_payload() for constraint in self.constraints],
            "parameters": [parameter.to_payload() for parameter in self.parameters],
        }

    def finite_assignments(self) -> tuple[dict[str, Any], ...]:
        """Return raw cartesian assignments before conditional normalization."""

        value_sets: list[tuple[Any, ...]] = []
        for parameter in self.parameters:
            values = parameter.finite_values()
            if values is None:
                raise ValueError("unbounded search space requires budget")
            value_sets.append(values)
        assignments: list[dict[str, Any]] = []
        names = [parameter.name for parameter in self.parameters]
        for values in product(*value_sets):
            assignments.append(dict(zip(names, values, strict=True)))
        return tuple(assignments)

    def normalize_candidate(self, parameters: Mapping[str, Any]) -> dict[str, Any] | None:
        """Apply conditional and forbidden-combination constraints."""

        normalized = dict(parameters)
        for constraint in self.constraints:
            if constraint.constraint_type != "conditional":
                continue
            if constraint.parameter is None:
                raise ValueError("conditional constraint parameter is required")
            if not self._matches(normalized, constraint.when):
                normalized.pop(constraint.parameter, None)
        for constraint in self.constraints:
            if constraint.constraint_type == "forbidden_combination" and self._matches(
                normalized,
                constraint.values,
            ):
                return None
        return dict(sorted(normalized.items()))

    def random_assignment(self, rng: random.Random) -> dict[str, Any]:
        """Return one raw deterministic random assignment."""

        return {parameter.name: parameter.random_value(rng) for parameter in self.parameters}

    def _validate_constraints(self, parameter_names: frozenset[str]) -> None:
        for constraint in self.constraints:
            referenced_names = set(constraint.when) | set(constraint.values)
            if constraint.parameter is not None:
                if constraint.parameter not in parameter_names:
                    raise ValueError(f"unknown conditional parameter: {constraint.parameter}")
                referenced_names.add(constraint.parameter)
            unknown_names = sorted(name for name in referenced_names if name not in parameter_names)
            if unknown_names:
                raise ValueError(f"unknown search constraint parameter: {unknown_names[0]}")

    @staticmethod
    def _matches(parameters: Mapping[str, Any], expected: Mapping[str, Any]) -> bool:
        return all(parameters.get(name) == value for name, value in expected.items())


class CandidateGenerator:
    """Generates deterministic candidate streams from a ``SearchSpaceSpec``."""

    def __init__(self, spec: SearchSpaceSpec) -> None:
        self._spec = spec

    @property
    def candidate_space_hash(self) -> str:
        """Return the hash of the generator's search-space spec."""

        return self._spec.candidate_space_hash

    def grid(self, *, budget: int | None = None) -> tuple[GeneratedCandidate, ...]:
        """Return a deterministic finite grid, optionally truncated by budget."""

        if budget is not None and budget < 0:
            raise ValueError("budget must be non-negative")
        candidates = self._deduplicated_candidates(self._spec.finite_assignments())
        if budget is None:
            return candidates
        return candidates[:budget]

    def random(self, *, seed: int, budget: int) -> tuple[GeneratedCandidate, ...]:
        """Return deterministic random candidates under ``seed`` and ``budget``."""

        if budget <= 0:
            raise ValueError("budget must be positive")
        rng = random.Random(seed)
        assignments: list[dict[str, Any]] = []
        seen: set[str] = set()
        max_attempts = max(100, budget * 1000)
        attempts = 0
        while len(assignments) < budget and attempts < max_attempts:
            attempts += 1
            normalized = self._spec.normalize_candidate(self._spec.random_assignment(rng))
            if normalized is None:
                continue
            key = stable_json_dumps(normalized)
            if key in seen:
                continue
            seen.add(key)
            assignments.append(normalized)
        return tuple(
            GeneratedCandidate.create(
                ordinal=ordinal,
                parameters=parameters,
                candidate_space_hash=self.candidate_space_hash,
            )
            for ordinal, parameters in enumerate(assignments)
        )

    def write_jsonl(self, path: Path, candidates: Sequence[GeneratedCandidate]) -> Path:
        """Write generated candidate parameters as deterministic JSONL."""

        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(candidate.to_payload(), sort_keys=True) for candidate in candidates]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return path

    def _deduplicated_candidates(
        self,
        assignments: Sequence[Mapping[str, Any]],
    ) -> tuple[GeneratedCandidate, ...]:
        deduplicated: list[dict[str, Any]] = []
        seen: set[str] = set()
        for assignment in assignments:
            normalized = self._spec.normalize_candidate(assignment)
            if normalized is None:
                continue
            key = stable_json_dumps(normalized)
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(normalized)
        return tuple(
            GeneratedCandidate.create(
                ordinal=ordinal,
                parameters=parameters,
                candidate_space_hash=self.candidate_space_hash,
            )
            for ordinal, parameters in enumerate(deduplicated)
        )


__all__ = [
    "CandidateGenerator",
    "GeneratedCandidate",
    "SearchConstraint",
    "SearchConstraintType",
    "SearchParameter",
    "SearchParameterType",
    "SearchSpaceSpec",
]
