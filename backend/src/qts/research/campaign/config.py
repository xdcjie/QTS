"""Research campaign configuration contract."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Self

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_hash


@dataclass(frozen=True, slots=True)
class ResearchCampaignObjective:
    """Multi-objective scoring contract for a research campaign."""

    primary: str
    components: Mapping[str, float]

    def __post_init__(self) -> None:
        primary = self.primary.strip()
        if not primary:
            raise ValueError("objective.primary is required")
        components = self._component_weights(self.components)
        if not any(weight > 0 for weight in components.values()):
            raise ValueError("objective.components must include at least one positive weight")
        object.__setattr__(self, "primary", primary)
        object.__setattr__(self, "components", components)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Self:
        """Construct an objective from a campaign YAML payload section."""

        return cls(
            primary=ResearchCampaignConfig.required_text(payload, "objective.primary", "primary"),
            components=cls._required_components(payload.get("components")),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready objective payload."""

        return {
            "components": {name: self.components[name] for name in sorted(self.components)},
            "primary": self.primary,
        }

    @classmethod
    def _required_components(cls, value: Any) -> dict[str, float]:
        if not isinstance(value, Mapping) or not value:
            raise ValueError("objective.components must be a non-empty mapping")
        return cls._component_weights(value)

    @staticmethod
    def _component_weights(value: Mapping[str, Any]) -> dict[str, float]:
        components: dict[str, float] = {}
        for raw_name, raw_weight in value.items():
            name = str(raw_name).strip()
            field_name = f"objective.components.{name}"
            ResearchCampaignConfig.validate_safe_token(name, field_name)
            weight = ResearchCampaignConfig.finite_number(raw_weight, field_name)
            components[name] = weight
        return dict(sorted(components.items()))


@dataclass(frozen=True, slots=True)
class ResearchCampaignBudget:
    """Finite search budget limits for a research campaign."""

    max_generations: int
    max_trials_per_generation: int
    max_total_trials: int
    max_family_trials: int
    wall_clock_limit_minutes: int
    compute_budget_limit: int | None = None

    def __post_init__(self) -> None:
        max_generations = self._positive_int(
            self.max_generations,
            "budget.max_generations",
        )
        max_trials_per_generation = self._positive_int(
            self.max_trials_per_generation,
            "budget.max_trials_per_generation",
        )
        max_total_trials = self._positive_int(
            self.max_total_trials,
            "budget.max_total_trials",
        )
        max_family_trials = self._positive_int(
            self.max_family_trials,
            "budget.max_family_trials",
        )
        wall_clock_limit_minutes = self._positive_int(
            self.wall_clock_limit_minutes,
            "budget.wall_clock_limit_minutes",
        )
        compute_budget_limit = (
            None
            if self.compute_budget_limit is None
            else self._positive_int(self.compute_budget_limit, "budget.compute_budget_limit")
        )
        if max_trials_per_generation > max_total_trials:
            raise ValueError(
                "budget.max_trials_per_generation must not exceed budget.max_total_trials"
            )
        if max_family_trials > max_total_trials:
            raise ValueError("budget.max_family_trials must not exceed budget.max_total_trials")
        object.__setattr__(self, "max_generations", max_generations)
        object.__setattr__(self, "max_trials_per_generation", max_trials_per_generation)
        object.__setattr__(self, "max_total_trials", max_total_trials)
        object.__setattr__(self, "max_family_trials", max_family_trials)
        object.__setattr__(self, "wall_clock_limit_minutes", wall_clock_limit_minutes)
        object.__setattr__(self, "compute_budget_limit", compute_budget_limit)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Self:
        """Construct a campaign budget from a YAML payload section."""

        return cls(
            max_generations=cls._required_positive_int(payload, "max_generations"),
            max_trials_per_generation=cls._required_positive_int(
                payload,
                "max_trials_per_generation",
            ),
            max_total_trials=cls._required_positive_int(payload, "max_total_trials"),
            max_family_trials=cls._required_positive_int(payload, "max_family_trials"),
            wall_clock_limit_minutes=cls._required_positive_int(
                payload,
                "wall_clock_limit_minutes",
            ),
            compute_budget_limit=(
                None
                if payload.get("compute_budget_limit") is None
                else cls._required_positive_int(payload, "compute_budget_limit")
            ),
        )

    def to_payload(self) -> dict[str, int]:
        """Return a JSON-ready budget payload."""

        payload = {
            "max_family_trials": self.max_family_trials,
            "max_generations": self.max_generations,
            "max_total_trials": self.max_total_trials,
            "max_trials_per_generation": self.max_trials_per_generation,
            "wall_clock_limit_minutes": self.wall_clock_limit_minutes,
        }
        if self.compute_budget_limit is not None:
            payload["compute_budget_limit"] = self.compute_budget_limit
        return payload

    @classmethod
    def _required_positive_int(cls, payload: Mapping[str, Any], field_name: str) -> int:
        return cls._positive_int(payload.get(field_name), f"budget.{field_name}")

    @staticmethod
    def _positive_int(value: Any, field_name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{field_name} must be a finite positive integer")
        if value <= 0:
            raise ValueError(f"{field_name} must be a finite positive integer")
        return value


@dataclass(frozen=True, slots=True)
class ResearchCampaignExecution:
    """Execution and data materialization policy for a research campaign."""

    default_mode: str
    metrics_source: str
    data_mode: str
    max_rows: int | None = None

    _DATA_MODES = frozenset({"fixture", "full"})

    def __post_init__(self) -> None:
        default_mode = ResearchCampaignConfig.required_text_value(
            self.default_mode,
            "execution.default_mode",
        )
        metrics_source = ResearchCampaignConfig.required_text_value(
            self.metrics_source,
            "execution.metrics_source",
        )
        data_mode = ResearchCampaignConfig.required_text_value(
            self.data_mode,
            "execution.data_mode",
        )
        if data_mode not in self._DATA_MODES:
            raise ValueError("execution.data_mode must be fixture or full")
        max_rows = self.max_rows
        if data_mode == "fixture":
            if max_rows is None:
                raise ValueError("execution.max_rows is required for fixture data_mode")
            max_rows = ResearchCampaignBudget._positive_int(max_rows, "execution.max_rows")
        elif max_rows is not None:
            raise ValueError("execution.max_rows is only allowed for fixture data_mode")
        object.__setattr__(self, "default_mode", default_mode)
        object.__setattr__(self, "metrics_source", metrics_source)
        object.__setattr__(self, "data_mode", data_mode)
        object.__setattr__(self, "max_rows", max_rows)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Self:
        """Construct execution policy from a campaign YAML payload section."""

        return cls(
            default_mode=ResearchCampaignConfig.required_text(
                payload,
                "execution.default_mode",
                "default_mode",
            ),
            metrics_source=ResearchCampaignConfig.required_text(
                payload,
                "execution.metrics_source",
                "metrics_source",
            ),
            data_mode=ResearchCampaignConfig.required_text(
                payload,
                "execution.data_mode",
                "data_mode",
            ),
            max_rows=None
            if payload.get("max_rows") is None
            else ResearchCampaignBudget._positive_int(
                payload.get("max_rows"), "execution.max_rows"
            ),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready execution policy payload."""

        payload: dict[str, Any] = {
            "data_mode": self.data_mode,
            "default_mode": self.default_mode,
            "metrics_source": self.metrics_source,
        }
        if self.max_rows is not None:
            payload["max_rows"] = self.max_rows
        return payload


@dataclass(frozen=True, slots=True)
class ResearchCampaignUniverse:
    """Universe and data contract fields for a research campaign."""

    roots: tuple[str, ...]
    asset_class: str
    calendar: str
    timeframe: str
    dataset_id: str

    def __post_init__(self) -> None:
        roots = self._validated_roots(self.roots)
        object.__setattr__(self, "roots", roots)
        object.__setattr__(
            self,
            "asset_class",
            ResearchCampaignConfig.required_text_value(
                self.asset_class,
                "universe.asset_class",
            ),
        )
        object.__setattr__(
            self,
            "calendar",
            ResearchCampaignConfig.required_text_value(self.calendar, "universe.calendar"),
        )
        object.__setattr__(
            self,
            "timeframe",
            ResearchCampaignConfig.required_text_value(self.timeframe, "universe.timeframe"),
        )
        object.__setattr__(
            self,
            "dataset_id",
            ResearchCampaignConfig.required_text_value(self.dataset_id, "universe.dataset_id"),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Self:
        """Construct a campaign universe from a YAML payload section."""

        return cls(
            roots=cls._roots_from_payload(payload.get("roots")),
            asset_class=ResearchCampaignConfig.required_text(
                payload,
                "universe.asset_class",
                "asset_class",
            ),
            calendar=ResearchCampaignConfig.required_text(
                payload,
                "universe.calendar",
                "calendar",
            ),
            timeframe=ResearchCampaignConfig.required_text(
                payload,
                "universe.timeframe",
                "timeframe",
            ),
            dataset_id=ResearchCampaignConfig.required_text(
                payload,
                "universe.dataset_id",
                "dataset_id",
            ),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready universe payload."""

        return {
            "asset_class": self.asset_class,
            "calendar": self.calendar,
            "dataset_id": self.dataset_id,
            "roots": list(self.roots),
            "timeframe": self.timeframe,
        }

    @classmethod
    def _roots_from_payload(cls, value: Any) -> tuple[str, ...]:
        if not isinstance(value, list):
            raise ValueError("universe.roots must be a list")
        return cls._validated_roots(tuple(value))

    @staticmethod
    def _validated_roots(value: tuple[Any, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("universe.roots must not be empty")
        roots: list[str] = []
        for index, raw_root in enumerate(value):
            root = ResearchCampaignConfig.required_text_value(
                raw_root,
                f"universe.roots[{index}]",
            )
            ResearchCampaignConfig.validate_safe_token(root, f"universe.roots[{index}]")
            roots.append(root)
        if len(set(roots)) != len(roots):
            raise ValueError("universe.roots must not contain duplicates")
        return tuple(roots)


@dataclass(frozen=True, slots=True)
class ResearchCampaignFamily:
    """One factor or strategy family declaration in a campaign."""

    id: str
    template: str
    manifest_template: str
    search_space: str

    def __post_init__(self) -> None:
        family_id = ResearchCampaignConfig.required_text_value(self.id, "families[].id")
        ResearchCampaignConfig.validate_safe_token(family_id, "families[].id")
        template = ResearchCampaignConfig.required_text_value(
            self.template,
            f"families.{family_id}.template",
        )
        ResearchCampaignConfig.validate_safe_token(template, f"families.{family_id}.template")
        object.__setattr__(self, "id", family_id)
        object.__setattr__(self, "template", template)
        object.__setattr__(
            self,
            "manifest_template",
            ResearchCampaignConfig.required_text_value(
                self.manifest_template,
                f"families.{family_id}.manifest_template",
            ),
        )
        object.__setattr__(
            self,
            "search_space",
            ResearchCampaignConfig.required_text_value(
                self.search_space,
                f"families.{family_id}.search_space",
            ),
        )

    @classmethod
    def from_payload(cls, index: int, payload: Mapping[str, Any]) -> Self:
        """Construct a campaign family from one YAML list item."""

        return cls(
            id=ResearchCampaignConfig.required_text(payload, f"families[{index}].id", "id"),
            template=ResearchCampaignConfig.required_text(
                payload,
                f"families[{index}].template",
                "template",
            ),
            manifest_template=ResearchCampaignConfig.required_text(
                payload,
                f"families[{index}].manifest_template",
                "manifest_template",
            ),
            search_space=ResearchCampaignConfig.required_text(
                payload,
                f"families[{index}].search_space",
                "search_space",
            ),
        )

    def to_payload(self) -> dict[str, str]:
        """Return a JSON-ready family payload."""

        return {
            "id": self.id,
            "manifest_template": self.manifest_template,
            "search_space": self.search_space,
            "template": self.template,
        }


@dataclass(frozen=True, slots=True)
class ResearchCampaignConstraint:
    """One validated candidate-selection constraint threshold."""

    name: str
    value: float

    def __post_init__(self) -> None:
        name = ResearchCampaignConfig.required_text_value(self.name, "constraints[].name")
        ResearchCampaignConfig.validate_safe_token(name, "constraints[].name")
        if name not in ResearchCampaignConfig.SUPPORTED_CONSTRAINTS:
            raise ValueError(f"unsupported campaign constraint: {name}")
        value = ResearchCampaignConfig.finite_number(self.value, f"constraints.{name}")
        self._validate_constraint_value(name, value)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "value", value)

    @classmethod
    def from_payload(cls, name: str, value: Any) -> Self:
        """Construct a campaign constraint from a YAML mapping item."""

        return cls(name=name, value=value)

    def to_payload_value(self) -> float | int:
        """Return a JSON-ready threshold value."""

        if self.value.is_integer():
            return int(self.value)
        return self.value

    @staticmethod
    def _validate_constraint_value(name: str, value: float) -> None:
        if name in {"min_oos_months", "min_oos_trade_count"}:
            if value <= 0 or not value.is_integer():
                raise ValueError(f"constraints.{name} must be a positive integer threshold")
            return
        if name == "min_profit_factor":
            if value <= 0:
                raise ValueError("constraints.min_profit_factor must be greater than 0")
            return
        if name in {"max_drawdown", "max_cost_impact", "max_correlation_to_active"}:
            if value < 0 or value > 1:
                raise ValueError(f"constraints.{name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ResearchCampaignConfig:
    """Validated input contract for one autonomous alpha research campaign."""

    campaign_id: str
    owner: str
    created_at: str
    universe: ResearchCampaignUniverse
    families: tuple[ResearchCampaignFamily, ...]
    objective: ResearchCampaignObjective
    constraints: tuple[ResearchCampaignConstraint, ...]
    budget: ResearchCampaignBudget
    execution: ResearchCampaignExecution

    SAFE_TOKEN_CHARS = frozenset(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    )
    SUPPORTED_CONSTRAINTS = frozenset(
        {
            "max_correlation_to_active",
            "max_cost_impact",
            "max_drawdown",
            "min_oos_months",
            "min_oos_trade_count",
            "min_profit_factor",
        }
    )

    def __post_init__(self) -> None:
        campaign_id = self.required_text_value(self.campaign_id, "campaign_id")
        self.validate_safe_token(campaign_id, "campaign_id")
        owner = self.required_text_value(self.owner, "owner")
        self.validate_safe_token(owner, "owner")
        created_at = self._normalized_created_at(self.created_at)
        families = tuple(self.families)
        if not families:
            raise ValueError("families must not be empty")
        self._validate_unique_family_ids(families)
        constraints = tuple(self.constraints)
        if not constraints:
            raise ValueError("constraints must not be empty")
        object.__setattr__(self, "campaign_id", campaign_id)
        object.__setattr__(self, "owner", owner)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "families", families)
        object.__setattr__(
            self, "constraints", tuple(sorted(constraints, key=lambda item: item.name))
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> Self:
        """Load and validate a research campaign YAML file."""

        campaign_path = Path(path)
        if not campaign_path.exists():
            raise FileNotFoundError(f"research campaign config not found: {campaign_path}")
        raw = yaml.safe_load(campaign_path.read_text(encoding="utf-8"))
        if not isinstance(raw, Mapping):
            raise ValueError("research campaign config must be a YAML mapping")
        return cls.from_payload(raw)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Self:
        """Construct and validate a research campaign from a decoded payload."""

        universe = cls.required_mapping(payload, "universe")
        objective = cls.required_mapping(payload, "objective")
        constraints = cls.required_mapping(payload, "constraints")
        budget = cls.required_mapping(payload, "budget")
        execution = cls.required_mapping(payload, "execution")
        return cls(
            campaign_id=cls.required_text(payload, "campaign_id", "campaign_id"),
            owner=cls.required_text(payload, "owner", "owner"),
            created_at=cls.required_text(payload, "created_at", "created_at"),
            universe=ResearchCampaignUniverse.from_payload(universe),
            families=cls.families_from_payload(payload.get("families")),
            objective=ResearchCampaignObjective.from_payload(objective),
            constraints=cls.constraints_from_payload(constraints),
            budget=ResearchCampaignBudget.from_payload(budget),
            execution=ResearchCampaignExecution.from_payload(execution),
        )

    @property
    def campaign_hash(self) -> str:
        """Return the deterministic hash of the normalized campaign contract."""

        return stable_json_hash(self.to_payload(include_hash=False))

    def to_payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        """Return a JSON-ready payload suitable for campaign_config.json."""

        payload: dict[str, Any] = {
            "budget": self.budget.to_payload(),
            "campaign_id": self.campaign_id,
            "constraints": {
                constraint.name: constraint.to_payload_value() for constraint in self.constraints
            },
            "created_at": self.created_at,
            "execution": self.execution.to_payload(),
            "families": [family.to_payload() for family in self.families],
            "objective": self.objective.to_payload(),
            "owner": self.owner,
            "universe": self.universe.to_payload(),
        }
        if include_hash:
            payload["campaign_hash"] = self.campaign_hash
        return payload

    @classmethod
    def required_mapping(cls, payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
        """Return a required mapping field from a decoded campaign payload."""

        value = payload.get(field_name)
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        return dict(value)

    @classmethod
    def families_from_payload(cls, value: Any) -> tuple[ResearchCampaignFamily, ...]:
        """Return validated family declarations from a decoded campaign payload."""

        if not isinstance(value, list) or not value:
            raise ValueError("families must be a non-empty list")
        families: list[ResearchCampaignFamily] = []
        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                raise ValueError(f"families[{index}] must be a mapping")
            families.append(ResearchCampaignFamily.from_payload(index, item))
        return tuple(families)

    @classmethod
    def constraints_from_payload(
        cls,
        payload: Mapping[str, Any],
    ) -> tuple[ResearchCampaignConstraint, ...]:
        """Return validated constraints from a decoded campaign payload."""

        if not payload:
            raise ValueError("constraints must not be empty")
        return tuple(
            ResearchCampaignConstraint.from_payload(str(name), payload[name])
            for name in sorted(payload)
        )

    @classmethod
    def required_text(
        cls,
        payload: Mapping[str, Any],
        field_name: str,
        payload_key: str,
    ) -> str:
        """Return a required non-empty text field from a decoded mapping."""

        return cls.required_text_value(payload.get(payload_key), field_name)

    @staticmethod
    def required_text_value(value: Any, field_name: str) -> str:
        """Return a stripped non-empty text value."""

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()

    @classmethod
    def validate_safe_token(cls, value: str, field_name: str) -> None:
        """Require token fields to stay deterministic and filename-safe."""

        if any(character not in cls.SAFE_TOKEN_CHARS for character in value):
            raise ValueError(f"{field_name} must be filename-safe")

    @staticmethod
    def finite_number(value: Any, field_name: str) -> float:
        """Return a finite numeric value."""

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a finite number")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{field_name} must be finite")
        return number

    @staticmethod
    def _normalized_created_at(value: str) -> str:
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("created_at must be an ISO-8601 datetime") from exc
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return timestamp.isoformat()

    @staticmethod
    def _validate_unique_family_ids(families: tuple[ResearchCampaignFamily, ...]) -> None:
        ids = [family.id for family in families]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate campaign family id")


__all__ = [
    "ResearchCampaignBudget",
    "ResearchCampaignConfig",
    "ResearchCampaignConstraint",
    "ResearchCampaignExecution",
    "ResearchCampaignFamily",
    "ResearchCampaignObjective",
    "ResearchCampaignUniverse",
]
