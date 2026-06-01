"""Gate-based research workflow orchestration."""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import yaml  # type: ignore[import-untyped]

from qts.research.coercion import (
    iso_datetime,
)
from qts.research.idea_registry import IdeaRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.workflow_optimize import optimize_step
from qts.research.workflow_steps import (
    _ablation,
    _backtest,
    _backtest_matrix,
    _declared_period_payload,
    _factor_candidates,
    _factor_evaluation,
    _factor_review_gate,
    _factor_tearsheet,
    _implementation_gate,
    _portfolio_ensemble,
    _portfolio_ensemble_scan,
    _portfolio_volatility_managed_scan,
    _report_only_period_names,
    _research_report,
    _selection_basis,
    _trade_diagnostics,
)
from qts.research.workflow_support import (
    _FILENAME_SAFE_CHARS,
    _PERIOD_ROLES,
    _REPORT_ONLY_PERIOD_ROLES,
    _SCORING_PERIOD_ROLES,
    ResearchWorkflowStepResult,
    _required_text,
    _string_sequence,
    json_ready,
)


class _ResearchWorkflowSessionConfig(Protocol):
    """Config surface required by research workflow provenance."""

    research_config_path: Path
    backtest_config_path: Path
    dataset_ids: Sequence[str]


@dataclass(frozen=True, slots=True)
class ResearchWorkflowStepConfig:
    """One validated workflow step declaration."""

    step_id: str
    kind: str
    payload: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ResearchWorkflowRunContext:
    """Machine-readable provenance for one research workflow run."""

    workflow_config_path: str
    workflow_config_hash: str
    research_config_path: str = "unknown"
    research_config_hash: str = "unknown"
    git_branch: str = "unknown"
    git_commit: str = "unknown"
    git_dirty: bool | str = "unknown"
    dataset_ids: tuple[str, ...] = ()
    backtest_config_hash: str = "unknown"
    generated_at: str = ""
    promotion_status: str = "research_only"

    def __post_init__(self) -> None:
        if not self.generated_at:
            object.__setattr__(self, "generated_at", datetime.now(UTC).isoformat())
        if self.promotion_status != "research_only":
            raise ValueError("research workflow run context promotion_status must be research_only")

    @classmethod
    def from_session(
        cls,
        session: Any,
        config: ResearchWorkflowConfig,
        *,
        git_command: Callable[[Sequence[str]], str | None] | None = None,
    ) -> ResearchWorkflowRunContext:
        """Build run provenance from workflow/session config with explicit unknown fallbacks."""

        session_config = session.config
        research_config_path = (
            None if session_config is None else session_config.research_config_path
        )
        backtest_config_path = (
            None if session_config is None else session_config.backtest_config_path
        )
        return cls(
            workflow_config_path=str(config.workflow_config_path),
            workflow_config_hash=_sha256_path(config.workflow_config_path),
            research_config_path=_path_text(research_config_path),
            research_config_hash=_sha256_path(research_config_path),
            git_branch=_git_value(["rev-parse", "--abbrev-ref", "HEAD"], git_command),
            git_commit=_git_value(["rev-parse", "HEAD"], git_command),
            git_dirty=_git_dirty(git_command),
            dataset_ids=_dataset_ids(session_config),
            backtest_config_hash=_sha256_path(backtest_config_path),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready run context payload."""

        return {
            "backtest_config_hash": self.backtest_config_hash,
            "dataset_ids": list(self.dataset_ids),
            "generated_at": self.generated_at,
            "git_branch": self.git_branch,
            "git_commit": self.git_commit,
            "git_dirty": self.git_dirty,
            "promotion_status": self.promotion_status,
            "research_config_hash": self.research_config_hash,
            "research_config_path": self.research_config_path,
            "workflow_config_hash": self.workflow_config_hash,
            "workflow_config_path": self.workflow_config_path,
        }


@dataclass(frozen=True, slots=True)
class ResearchRouteMetadata:
    """Research route governance metadata for large workflow programs."""

    route_id: str
    route_name: str
    status: str
    owner: str
    selection_policy: Mapping[str, Any]
    allowed_period_roles: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in _ROUTE_STATUSES:
            raise ValueError(f"unsupported route status: {self.status}")
        if any(role not in _PERIOD_ROLES for role in self.allowed_period_roles):
            raise ValueError("route allowed_period_roles contains unsupported period role")

    def validate_periods(self, periods: tuple[dict[str, Any], ...]) -> None:
        """Validate route metadata against declared workflow periods."""

        role_by_name = {str(period["name"]): str(period["role"]) for period in periods}
        allowed_roles = set(self.allowed_period_roles)
        if allowed_roles:
            disallowed_periods = {
                name: role for name, role in role_by_name.items() if role not in allowed_roles
            }
            if disallowed_periods:
                raise ValueError("route allowed_period_roles excludes declared workflow period")
        for field_name in ("selection_periods", "validation_periods", "report_only_periods"):
            raw_periods = self.selection_policy.get(field_name, ())
            names = _period_names_from_field(raw_periods, field_name=f"route.{field_name}")
            _reject_unknown_period_names(
                names,
                role_by_name=role_by_name,
                field_name=f"route.{field_name}",
            )
        if self.status == "candidate":
            selection_names = _period_names_from_field(
                self.selection_policy.get("selection_periods", ()),
                field_name="route.selection_periods",
            )
            if not selection_names or all(
                role_by_name.get(period_name) in _REPORT_ONLY_PERIOD_ROLES
                for period_name in selection_names
            ):
                raise ValueError("route candidate status requires scoring selection periods")

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready route metadata."""

        return {
            "allowed_period_roles": list(self.allowed_period_roles),
            "owner": self.owner,
            "route_id": self.route_id,
            "route_name": self.route_name,
            "selection_policy": json_ready(self.selection_policy),
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class ResearchIdeaLink:
    """Workflow-level link to an idea registry entry."""

    idea_id: str
    registry_root: Path

    def __post_init__(self) -> None:
        idea_id = self.idea_id.strip()
        if not idea_id:
            raise ValueError("idea.idea_id is required")
        object.__setattr__(self, "idea_id", idea_id)

    def load(self) -> IdeaSpec:
        """Load the linked idea from its registry."""

        return IdeaRegistry(self.registry_root).get(self.idea_id)

    def to_payload(self) -> dict[str, str]:
        """Return JSON-ready idea link metadata."""

        return {
            "idea_id": self.idea_id,
            "registry_root": str(self.registry_root),
        }


@dataclass(frozen=True, slots=True)
class ResearchRouteIndex:
    """Resolved index of route workflow files."""

    routes: tuple[dict[str, str], ...]

    @classmethod
    def from_yaml(cls, path: str | Path) -> ResearchRouteIndex:
        """Load and resolve a route workflow index."""

        index_path = Path(path)
        raw = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        if not isinstance(raw, Mapping):
            raise ValueError("research route index must be a YAML mapping")
        if raw.get("version") != 1:
            raise ValueError("research route index version must be 1")
        raw_routes = raw.get("routes")
        if not isinstance(raw_routes, list) or not raw_routes:
            raise ValueError("research route index routes must not be empty")
        routes: list[dict[str, str]] = []
        for index, item in enumerate(raw_routes):
            if not isinstance(item, Mapping):
                raise ValueError(f"research route index routes[{index}] must be a mapping")
            route_id = _required_text(item, "route_id")
            workflow = Path(_required_text(item, "workflow"))
            workflow_path = workflow if workflow.is_absolute() else index_path.parent / workflow
            if not workflow_path.exists():
                raise FileNotFoundError(f"route workflow not found: {workflow_path}")
            workflow_route_id = _route_id_from_workflow_yaml(workflow_path)
            if workflow_route_id != route_id:
                raise ValueError(
                    f"route index id {route_id} does not match workflow route_id "
                    f"{workflow_route_id}"
                )
            routes.append({"route_id": route_id, "workflow": str(workflow_path)})
        return cls(routes=tuple(routes))


@dataclass(frozen=True, slots=True)
class ResearchWorkflowConfig:
    """Owns validated gate-based research workflow configuration."""

    workflow_config_path: Path
    workflow_id: str
    periods: tuple[dict[str, Any], ...]
    steps: tuple[ResearchWorkflowStepConfig, ...]
    route: ResearchRouteMetadata | None = None
    idea: ResearchIdeaLink | None = None

    def __post_init__(self) -> None:
        """Enforce workflow invariants for direct in-memory construction too."""

        if self.route is not None:
            self.route.validate_periods(self.periods)
        for index, step in enumerate(self.steps):
            _step_from_payload(
                index,
                {**dict(step.payload), "id": step.step_id, "kind": step.kind},
                periods=self.periods,
            )

    @classmethod
    def from_yaml(cls, path: str | Path) -> ResearchWorkflowConfig:
        """Load and validate a research workflow YAML file."""

        workflow_path = Path(path)
        if not workflow_path.exists():
            raise FileNotFoundError(f"research workflow config not found: {workflow_path}")
        raw = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("research workflow config must be a YAML mapping")
        version = raw.get("version")
        if version != 1:
            raise ValueError("research workflow version must be 1")
        workflow_id = cls._required_safe_token(raw, "workflow_id")
        if workflow_path.parent.name == "routes" and raw.get("route") is None:
            raise ValueError("route workflow configs must declare route metadata")
        periods = _periods_from_payload(raw.get("periods"))
        raw_steps = raw.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError("research workflow steps must not be empty")
        steps = tuple(
            _step_from_payload(index, item, periods=periods) for index, item in enumerate(raw_steps)
        )
        return cls(
            workflow_config_path=workflow_path,
            workflow_id=workflow_id,
            periods=periods,
            idea=_idea_link_from_payload(raw.get("idea"), workflow_path=workflow_path),
            route=_route_metadata_from_payload(raw.get("route")),
            steps=steps,
        )

    def period_role(self, period_name: str) -> str | None:
        """Return the declared role for a period, if the workflow declares it."""

        period = self._period_by_name().get(period_name)
        return None if period is None else str(period["role"])

    def period_roles_for(self, period_names: tuple[str, ...]) -> dict[str, str]:
        """Return declared roles for the supplied period names."""

        roles: dict[str, str] = {}
        for period_name in period_names:
            role = self.period_role(period_name)
            if role is not None:
                roles[period_name] = role
        return roles

    def _period_by_name(self) -> dict[str, dict[str, Any]]:
        return {str(period["name"]): period for period in self.periods}

    def resolve_path(self, value: str | Path) -> Path:
        """Resolve workflow-local paths relative to the workflow config file."""

        path = Path(value)
        if path.is_absolute():
            return path
        return self.workflow_config_path.parent / path

    @staticmethod
    def _required_safe_token(payload: Mapping[str, Any], field_name: str) -> str:
        value = _required_text(payload, field_name)
        if any(character not in _FILENAME_SAFE_CHARS for character in value):
            raise ValueError(f"{field_name} must be filename-safe")
        return value


def _step_from_payload(
    index: int,
    payload: Any,
    *,
    periods: tuple[dict[str, Any], ...],
) -> ResearchWorkflowStepConfig:
    if not isinstance(payload, dict):
        raise ValueError(f"research workflow steps[{index}] must be a mapping")
    _reject_forbidden_keys(payload)
    step_id = ResearchWorkflowConfig._required_safe_token(payload, "id")
    kind = _required_text(payload, "kind")
    if kind not in _ALLOWED_STEP_KINDS:
        raise ValueError(f"unsupported workflow step kind: {kind}")
    step_payload = {str(key): value for key, value in payload.items() if key not in {"id", "kind"}}
    if kind == "implementation_gate":
        _validate_implementation_gate_payload(step_payload)
    _validate_step_period_roles(kind=kind, step_payload=step_payload, periods=periods)
    return ResearchWorkflowStepConfig(step_id=step_id, kind=kind, payload=step_payload)


def _periods_from_payload(value: Any) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, Mapping):
        raise ValueError("research workflow periods must be a mapping")
    periods: list[dict[str, Any]] = []
    previous_period: dict[str, Any] | None = None
    for raw_name, raw_period in value.items():
        name = str(raw_name)
        if any(character not in _FILENAME_SAFE_CHARS for character in name):
            raise ValueError("period name must be filename-safe")
        if not isinstance(raw_period, Mapping):
            raise ValueError(f"research workflow periods.{name} must be a mapping")
        start = iso_datetime(raw_period.get("start"), "start")
        raw_end = raw_period.get("end")
        end = None if raw_end is None else iso_datetime(raw_end, "end")
        if end is not None and start >= end:
            raise ValueError(f"period {name} start must be before end")
        if previous_period is not None:
            if start < previous_period["start"]:
                raise ValueError("research workflow periods must be time ordered")
            previous_end = previous_period["end"]
            if previous_end is None:
                raise ValueError(
                    f"period {name} cannot follow open-ended period {previous_period['name']}"
                )
            if start < previous_end:
                raise ValueError(
                    f"period {name} overlaps previous period {previous_period['name']}"
                )
        role = str(raw_period.get("role", "")).strip()
        if role not in _PERIOD_ROLES:
            raise ValueError(f"unsupported period role: {role}")
        period = {"end": end, "name": name, "role": role, "start": start}
        periods.append(period)
        previous_period = period
    return tuple(periods)


def _route_metadata_from_payload(value: Any) -> ResearchRouteMetadata | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("research workflow route metadata must be a mapping")
    raw_allowed_roles = value.get("allowed_period_roles", ())
    if raw_allowed_roles is None:
        raw_allowed_roles = ()
    if not isinstance(raw_allowed_roles, list | tuple):
        raise ValueError("route.allowed_period_roles must be a sequence")
    return ResearchRouteMetadata(
        route_id=ResearchWorkflowConfig._required_safe_token(value, "route_id"),
        route_name=ResearchWorkflowConfig._required_safe_token(value, "route_name"),
        status=_required_text(value, "status"),
        owner=_required_text(value, "owner"),
        selection_policy=(
            dict(value["selection_policy"])
            if isinstance(value.get("selection_policy"), Mapping)
            else {}
        ),
        allowed_period_roles=tuple(str(role) for role in raw_allowed_roles),
    )


def _route_id_from_workflow_yaml(path: Path) -> str:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("route workflow config must be a YAML mapping")
    route = payload.get("route")
    if not isinstance(route, Mapping):
        raise ValueError("indexed route workflow must declare route metadata")
    return ResearchWorkflowConfig._required_safe_token(route, "route_id")


def _idea_link_from_payload(value: Any, *, workflow_path: Path) -> ResearchIdeaLink | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("research workflow idea metadata must be a mapping")
    raw_registry_root = value.get("registry_root", "runs/research/idea_registry")
    if not isinstance(raw_registry_root, str) or not raw_registry_root.strip():
        raise ValueError("idea.registry_root must be a path")
    registry_root = Path(raw_registry_root)
    if not registry_root.is_absolute():
        registry_root = workflow_path.parent / registry_root
    return ResearchIdeaLink(
        idea_id=_required_text(value, "idea_id"),
        registry_root=registry_root,
    )


def _validate_step_period_roles(
    *,
    kind: str,
    step_payload: Mapping[str, Any],
    periods: tuple[dict[str, Any], ...],
) -> None:
    role_by_name = {str(period["name"]): str(period["role"]) for period in periods}
    if not role_by_name:
        _reject_period_sensitive_step_without_periods(kind=kind, step_payload=step_payload)
        return
    for field_name in _SCORE_PERIOD_FIELDS:
        names = _period_names_from_field(step_payload.get(field_name), field_name=field_name)
        _reject_unknown_period_names(names, role_by_name=role_by_name, field_name=field_name)
        _reject_report_only_period_names(names, role_by_name=role_by_name, field_name=field_name)
    if kind == "portfolio_ensemble_scan" and "score_periods" not in step_payload:
        names = _period_names_from_field(step_payload.get("periods"), field_name="score_periods")
        _reject_unknown_period_names(
            names,
            role_by_name=role_by_name,
            field_name="score_periods",
        )
        _reject_report_only_period_names(
            names,
            role_by_name=role_by_name,
            field_name="score_periods",
        )
    if kind == "portfolio_volatility_managed_scan" and "selection_periods" not in step_payload:
        names = _period_names_from_field(
            step_payload.get("periods"),
            field_name="selection_periods",
        )
        _reject_unknown_period_names(
            names,
            role_by_name=role_by_name,
            field_name="selection_periods",
        )
        _reject_report_only_period_names(
            names,
            role_by_name=role_by_name,
            field_name="selection_periods",
        )
    if kind == "optimize":
        validation = step_payload.get("validation")
        if isinstance(validation, Mapping):
            _validate_optimizer_period_roles(validation, periods=periods, role_by_name=role_by_name)
    if kind == "backtest_matrix":
        _validate_backtest_matrix_period_roles(
            step_payload.get("periods"),
            periods=periods,
            field_name="periods",
        )


def _validate_optimizer_period_roles(
    validation: Mapping[str, Any],
    *,
    periods: tuple[dict[str, Any], ...],
    role_by_name: Mapping[str, str],
) -> None:
    veto = validation.get("failure_window_veto")
    if isinstance(veto, Mapping):
        names = _window_names_from_field(
            veto.get("windows"),
            field_name="validation.failure_window_veto.windows",
        )
        _reject_report_only_period_names(
            names,
            role_by_name=role_by_name,
            field_name="validation.failure_window_veto.windows",
        )
        _reject_report_only_window_overlaps(
            veto.get("windows"),
            periods=periods,
            field_name="validation.failure_window_veto.windows",
        )
    walk_forward = validation.get("walk_forward")
    if isinstance(walk_forward, Mapping):
        _reject_report_only_walk_forward_overlaps(
            walk_forward.get("splits"),
            periods=periods,
            field_name="validation.walk_forward.splits",
        )


def _period_names_from_field(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field_name} must be a period name or sequence")
    names: list[str] = []
    for item in value:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, Mapping):
            names.append(_required_text(item, "name"))
        else:
            raise ValueError(f"{field_name} entries must be period names or mappings")
    return tuple(names)


def _window_names_from_field(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field_name} must be a sequence")
    names: list[str] = []
    for item in value:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, Mapping) and "name" in item:
            names.append(str(item["name"]))
    return tuple(names)


def _reject_report_only_window_overlaps(
    value: Any,
    *,
    periods: tuple[dict[str, Any], ...],
    field_name: str,
) -> None:
    if value is None:
        return
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field_name} must be a sequence")
    report_only_periods = _report_only_declared_periods(periods)
    for index, item in enumerate(value):
        if isinstance(item, str):
            continue
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name}[{index}] must be a mapping")
        if "start" not in item or "end" not in item:
            continue
        window_start = iso_datetime(item["start"], "start")
        window_end = iso_datetime(item["end"], "end")
        if window_start >= window_end:
            raise ValueError(f"{field_name}[{index}] start must be before end")
        _reject_interval_report_only_overlaps(
            window_start,
            window_end,
            periods=report_only_periods,
            field_name=field_name,
        )


def _reject_report_only_walk_forward_overlaps(
    value: Any,
    *,
    periods: tuple[dict[str, Any], ...],
    field_name: str,
) -> None:
    if value is None:
        return
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field_name} must be a sequence")
    report_only_periods = _report_only_declared_periods(periods)
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name}[{index}] must be a mapping")
        train_start = iso_datetime(item.get("train_start"), "train_start")
        train_end = iso_datetime(item.get("train_end"), "train_end")
        if train_start >= train_end:
            raise ValueError(f"{field_name}[{index}] train_start must be before train_end")
        _reject_interval_report_only_overlaps(
            train_start,
            train_end,
            periods=report_only_periods,
            field_name=field_name,
        )
        test_start = iso_datetime(item.get("test_start"), "test_start")
        test_end = iso_datetime(item.get("test_end"), "test_end")
        if test_start >= test_end:
            raise ValueError(f"{field_name}[{index}] test_start must be before test_end")
        _reject_interval_report_only_overlaps(
            test_start,
            test_end,
            periods=report_only_periods,
            field_name=field_name,
        )


def _validate_backtest_matrix_period_roles(
    value: Any,
    *,
    periods: tuple[dict[str, Any], ...],
    field_name: str,
) -> None:
    if value is None:
        return
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field_name} must be a sequence")
    report_only_periods = _report_only_declared_periods(periods)
    role_by_name = {str(period["name"]): str(period["role"]) for period in periods}
    period_by_name = {str(period["name"]): period for period in periods}
    for index, item in enumerate(value):
        if isinstance(item, str):
            _reject_unknown_period_names((item,), role_by_name=role_by_name, field_name=field_name)
            continue
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name}[{index}] must be a mapping")
        name = ResearchWorkflowConfig._required_safe_token(item, "name")
        declared_role = role_by_name.get(name)
        declared_period = period_by_name.get(name)
        role = str(item.get("role", "")).strip()
        if declared_role is None:
            _validate_undeclared_backtest_matrix_period_role(
                name=name,
                role=role,
                field_name=field_name,
            )
        if declared_role is not None and role and role != declared_role:
            raise ValueError(f"{field_name} period {name} cannot override declared role")
        if declared_period is not None:
            _validate_named_inline_period_bounds(
                item,
                declared_period=declared_period,
                field_name=field_name,
            )
        if role in _REPORT_ONLY_PERIOD_ROLES or declared_role in _REPORT_ONLY_PERIOD_ROLES:
            continue
        if "start" not in item or "end" not in item:
            continue
        inline_start = iso_datetime(item["start"], "start")
        inline_end = iso_datetime(item["end"], "end")
        if inline_start >= inline_end:
            raise ValueError(f"{field_name}[{index}] start must be before end")
        _reject_interval_report_only_overlaps(
            inline_start,
            inline_end,
            periods=report_only_periods,
            field_name=field_name,
        )


def _validate_undeclared_backtest_matrix_period_role(
    *,
    name: str,
    role: str,
    field_name: str,
) -> None:
    if not role:
        raise ValueError(f"{field_name} period {name} must declare a role or reference a period")
    if role not in _PERIOD_ROLES:
        raise ValueError(f"unsupported period role: {role}")
    if role in _SCORING_PERIOD_ROLES:
        raise ValueError(f"declared periods are required for scoring period {name}")


def _validate_named_inline_period_bounds(
    value: Mapping[str, Any],
    *,
    declared_period: Mapping[str, Any],
    field_name: str,
) -> None:
    if "start" not in value or "end" not in value:
        return
    inline_start = iso_datetime(value["start"], "start")
    inline_end = iso_datetime(value["end"], "end")
    if inline_start >= inline_end:
        raise ValueError(f"{field_name} period {declared_period['name']} start must be before end")
    declared_start = declared_period["start"]
    declared_end = declared_period["end"]
    if declared_end is None:
        if inline_start < declared_start:
            raise ValueError(
                f"{field_name} period {declared_period['name']} starts before declaration"
            )
        return
    if inline_start != declared_start or inline_end != declared_end:
        raise ValueError(
            f"{field_name} period {declared_period['name']} must match declared boundaries"
        )


def _reject_interval_report_only_overlaps(
    start: datetime,
    end: datetime,
    *,
    periods: tuple[dict[str, Any], ...],
    field_name: str,
) -> None:
    for period in periods:
        if _intervals_overlap(start, end, period["start"], period["end"]):
            raise ValueError(
                f"{period['role']} report-only period {period['name']} overlaps {field_name}"
            )


def _report_only_declared_periods(
    periods: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    return tuple(period for period in periods if period["role"] in _REPORT_ONLY_PERIOD_ROLES)


def _reject_period_sensitive_step_without_periods(
    *,
    kind: str,
    step_payload: Mapping[str, Any],
) -> None:
    if kind in {"portfolio_ensemble_scan", "portfolio_volatility_managed_scan"}:
        raise ValueError(f"declared periods are required for {kind}")
    if kind == "backtest_matrix" and step_payload.get("periods") is not None:
        raise ValueError("declared periods are required for backtest_matrix.periods")
    if kind != "optimize":
        return
    validation = step_payload.get("validation")
    if not isinstance(validation, Mapping):
        return
    if "failure_window_veto" in validation:
        raise ValueError("declared periods are required for failure_window_veto")
    if "walk_forward" in validation:
        raise ValueError("declared periods are required for walk_forward")


def _intervals_overlap(
    left_start: datetime,
    left_end: datetime,
    right_start: datetime,
    right_end: datetime | None,
) -> bool:
    if right_end is None:
        return left_end > right_start
    return left_start < right_end and right_start < left_end


def _reject_report_only_period_names(
    period_names: tuple[str, ...],
    *,
    role_by_name: Mapping[str, str],
    field_name: str,
) -> None:
    for period_name in period_names:
        role = role_by_name.get(period_name)
        if role in _REPORT_ONLY_PERIOD_ROLES:
            raise ValueError(
                f"{role} report-only period {period_name} cannot be used in {field_name}"
            )


def _reject_unknown_period_names(
    period_names: tuple[str, ...],
    *,
    role_by_name: Mapping[str, str],
    field_name: str,
) -> None:
    for period_name in period_names:
        if period_name not in role_by_name:
            raise ValueError(f"{field_name} period {period_name} is not declared")


def _reject_forbidden_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_WORKFLOW_KEYS:
                raise ValueError(f"forbidden workflow key: {key_text}")
            _reject_forbidden_keys(item)
    elif isinstance(value, list):
        for item in value:
            _reject_forbidden_keys(item)


def _validate_implementation_gate_payload(payload: Mapping[str, Any]) -> None:
    module_names = _string_sequence(
        payload.get("required_modules", ()),
        field_name="required_modules",
    )
    required_strategy = payload.get("required_strategy")
    if required_strategy is not None:
        module_names += (_strategy_module_name(str(required_strategy)),)
    for module_name in module_names:
        _reject_internal_implementation_import(module_name)


def _strategy_module_name(value: str) -> str:
    if ":" not in value:
        return value
    return value.split(":", maxsplit=1)[0]


def _reject_internal_implementation_import(module_name: str) -> None:
    if module_name == "qts" or (
        module_name.startswith("qts.")
        and not any(
            module_name == prefix or module_name.startswith(f"{prefix}.")
            for prefix in _ALLOWED_IMPLEMENTATION_QTS_PREFIXES
        )
    ):
        raise ValueError(f"implementation_gate cannot require internal module: {module_name}")


@dataclass(frozen=True, slots=True)
class ResearchWorkflowResult:
    """Deterministic workflow execution result."""

    workflow_id: str
    status: str
    steps: tuple[ResearchWorkflowStepResult, ...]
    periods: tuple[dict[str, Any], ...] = ()
    run_context: ResearchWorkflowRunContext | None = None
    route: ResearchRouteMetadata | None = None
    idea_metadata: Mapping[str, Any] | None = None
    projection_refs: Mapping[str, Any] | None = None
    decision: Any | None = None

    @property
    def succeeded(self) -> bool:
        """Return whether all executed workflow steps passed."""

        return self.status == "completed"

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready workflow result payload."""

        payload: dict[str, Any] = {
            "status": self.status,
            "steps": [step.to_payload() for step in self.steps],
            "workflow_id": self.workflow_id,
        }
        if self.run_context is not None:
            payload["run_context"] = self.run_context.to_payload()
        if self.route is not None:
            payload["route"] = self.route.to_payload()
        if self.idea_metadata is not None:
            payload["idea_metadata"] = json_ready(self.idea_metadata)
        if self.projection_refs is not None:
            payload["projection_refs"] = json_ready(self.projection_refs)
        if self.decision is not None:
            payload["decision"] = json_ready(self.decision)
        if self.periods:
            period_payloads = [_declared_period_payload(period) for period in self.periods]
            payload["periods"] = period_payloads
            payload["report_only_periods"] = _report_only_period_names(period_payloads)
            payload["selection_basis"] = _selection_basis(period_payloads)
        return payload


class ResearchWorkflowRunner:
    """Runs research workflow steps through ``ResearchSession`` public APIs."""

    def run(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        *,
        step_id: str | None = None,
        from_step_id: str | None = None,
        to_step_id: str | None = None,
    ) -> ResearchWorkflowResult:
        """Run a workflow until completion or a blocking gate."""

        run_context = ResearchWorkflowRunContext.from_session(session, config)
        idea_metadata = self._idea_metadata(config)
        results: list[ResearchWorkflowStepResult] = []
        overall_status = "completed"
        for step in self._selected_steps(
            config,
            step_id=step_id,
            from_step_id=from_step_id,
            to_step_id=to_step_id,
        ):
            result = self._run_step(
                session,
                config,
                step,
                steps=tuple(results),
                run_context=run_context,
                idea_metadata=idea_metadata,
            )
            results.append(result)
            if result.status != "passed":
                overall_status = "failed" if result.status == "failed" else "blocked"
                if (
                    result.status == "failed"
                    or step.kind in _HARD_STOP_STEP_KINDS
                    or step.payload.get("on_fail", "stop") == "stop"
                ):
                    break
        return ResearchWorkflowResult(
            workflow_id=config.workflow_id,
            periods=config.periods,
            decision=self._result_decision(tuple(results)),
            idea_metadata=idea_metadata,
            run_context=run_context,
            route=config.route,
            status=overall_status,
            steps=tuple(results),
        )

    def _selected_steps(
        self,
        config: ResearchWorkflowConfig,
        *,
        step_id: str | None,
        from_step_id: str | None,
        to_step_id: str | None,
    ) -> tuple[ResearchWorkflowStepConfig, ...]:
        self._validate_selection(
            step_id=step_id,
            from_step_id=from_step_id,
            to_step_id=to_step_id,
        )
        if step_id is None and from_step_id is None and to_step_id is None:
            return config.steps
        step_index_by_id = {step.step_id: index for index, step in enumerate(config.steps)}
        if step_id is not None:
            return (config.steps[self._step_index(step_index_by_id, step_id)],)
        start_index = (
            0 if from_step_id is None else self._step_index(step_index_by_id, from_step_id)
        )
        end_index = (
            len(config.steps) - 1
            if to_step_id is None
            else self._step_index(step_index_by_id, to_step_id)
        )
        if start_index > end_index:
            raise ValueError(
                "workflow step range is empty: "
                f"{config.steps[start_index].step_id} is after {config.steps[end_index].step_id}"
            )
        return config.steps[start_index : end_index + 1]

    @staticmethod
    def _validate_selection(
        *,
        step_id: str | None,
        from_step_id: str | None,
        to_step_id: str | None,
    ) -> None:
        if step_id is not None and (from_step_id is not None or to_step_id is not None):
            raise ValueError("--step cannot be combined with --from-step or --to-step")
        for field_name, value in {
            "step_id": step_id,
            "from_step_id": from_step_id,
            "to_step_id": to_step_id,
        }.items():
            if value is not None and not value.strip():
                raise ValueError(f"{field_name} must not be empty")

    @staticmethod
    def _step_index(step_index_by_id: Mapping[str, int], step_id: str) -> int:
        try:
            return step_index_by_id[step_id]
        except KeyError as exc:
            raise ValueError(f"workflow step not found: {step_id}") from exc

    @staticmethod
    def _idea_metadata(config: ResearchWorkflowConfig) -> Mapping[str, Any] | None:
        if config.idea is None:
            return None
        return config.idea.load().to_payload()

    @staticmethod
    def _result_decision(
        steps: tuple[ResearchWorkflowStepResult, ...],
    ) -> Mapping[str, Any] | None:
        for step in reversed(steps):
            if step.kind != "research_report":
                continue
            decision = step.outputs.get("decision")
            if isinstance(decision, Mapping):
                return decision
        return None

    def _run_step(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
        *,
        run_context: ResearchWorkflowRunContext,
        idea_metadata: Mapping[str, Any] | None,
        steps: tuple[ResearchWorkflowStepResult, ...],
    ) -> ResearchWorkflowStepResult:
        try:
            if step.kind == "factor_candidates":
                return _factor_candidates(session, step)
            if step.kind == "factor_review_gate":
                return _factor_review_gate(session, step)
            if step.kind == "implementation_gate":
                return _implementation_gate(step)
            if step.kind == "factor_evaluation":
                return _factor_evaluation(session, config, step)
            if step.kind == "factor_tearsheet":
                return _factor_tearsheet(session, config, step)
            if step.kind == "ablation":
                return _ablation(config, step)
            if step.kind == "trade_diagnostics":
                return _trade_diagnostics(config, step)
            if step.kind == "backtest":
                return _backtest(session, config, step)
            if step.kind == "backtest_matrix":
                return _backtest_matrix(session, config, step)
            if step.kind == "optimize":
                return optimize_step(session, config, step)
            if step.kind == "portfolio_ensemble":
                return _portfolio_ensemble(config, step)
            if step.kind == "portfolio_ensemble_scan":
                return _portfolio_ensemble_scan(config, step)
            if step.kind == "portfolio_volatility_managed_scan":
                return _portfolio_volatility_managed_scan(config, step)
            if step.kind == "research_report":
                return _research_report(
                    config,
                    run_context,
                    steps,
                    step,
                    idea_metadata=idea_metadata,
                )
        except Exception as exc:  # pragma: no cover - exercised by CLI integration.
            return ResearchWorkflowStepResult(
                step_id=step.step_id,
                kind=step.kind,
                status="failed",
                message=str(exc),
                outputs={},
            )
        raise ValueError(f"unsupported workflow step kind: {step.kind}")


def _path_text(value: Any) -> str:
    if isinstance(value, str | Path):
        return str(value)
    return "unknown"


def _sha256_path(value: Any) -> str:
    if not isinstance(value, str | Path):
        return "unknown"
    path = Path(value)
    if not path.exists() or not path.is_file():
        return "unknown"
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _git_value(
    args: Sequence[str],
    git_command: Callable[[Sequence[str]], str | None] | None,
) -> str:
    value = _call_git(args, git_command)
    if value is None or not value.strip():
        return "unknown"
    return value.strip()


def _git_dirty(git_command: Callable[[Sequence[str]], str | None] | None) -> bool | str:
    value = _call_git(["status", "--porcelain"], git_command)
    if value is None:
        return "unknown"
    return bool(value.strip())


def _call_git(
    args: Sequence[str],
    git_command: Callable[[Sequence[str]], str | None] | None,
) -> str | None:
    if git_command is not None:
        return git_command(args)
    try:
        completed = subprocess.run(
            ["git", *args],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def _dataset_ids(session_config: _ResearchWorkflowSessionConfig | None) -> tuple[str, ...]:
    if session_config is None:
        return ()
    return tuple(str(item) for item in session_config.dataset_ids)


__all__ = [
    "ResearchIdeaLink",
    "ResearchRouteIndex",
    "ResearchRouteMetadata",
    "ResearchWorkflowConfig",
    "ResearchWorkflowResult",
    "ResearchWorkflowRunContext",
    "ResearchWorkflowRunner",
    "ResearchWorkflowStepConfig",
    "ResearchWorkflowStepResult",
]

_ALLOWED_STEP_KINDS = frozenset(
    {
        "ablation",
        "backtest",
        "backtest_matrix",
        "factor_candidates",
        "factor_review_gate",
        "factor_evaluation",
        "factor_tearsheet",
        "implementation_gate",
        "optimize",
        "portfolio_ensemble",
        "portfolio_ensemble_scan",
        "portfolio_volatility_managed_scan",
        "research_report",
        "trade_diagnostics",
    }
)
_ROUTE_STATUSES = frozenset({"candidate", "exploration", "frozen", "rejected"})
_SCORE_PERIOD_FIELDS = frozenset(
    {
        "baseline_period",
        "objective_period",
        "objective_periods",
        "post_periods",
        "post_selection_periods",
        "ranking_period",
        "ranking_periods",
        "score_period",
        "score_periods",
        "selection_period",
        "selection_periods",
    }
)
_HARD_STOP_STEP_KINDS = frozenset({"factor_review_gate", "implementation_gate"})
_ALLOWED_IMPLEMENTATION_QTS_PREFIXES = ("qts.factors", "qts.indicators")
_FORBIDDEN_WORKFLOW_KEYS = frozenset(
    {
        "broker",
        "generate_code",
        "live",
        "orders",
        "paper",
        "promote",
        "promotion",
        "runtime",
        "trade",
    }
)
