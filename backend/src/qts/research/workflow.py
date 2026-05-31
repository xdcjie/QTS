"""Gate-based research workflow orchestration."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.research.ablation import AblationPlan, AblationReport, AblationReportWriter, AblationRun
from qts.research.coercion import (
    float_mapping,
    iso_date,
    iso_datetime,
    nested_float_mapping,
    optional_bool,
    optional_decimal,
    optional_float,
    optional_int,
    optional_mapping,
    optional_non_negative_int,
    optional_string_tuple,
    required_mapping,
    string_tuple,
)
from qts.research.idea_registry import IdeaRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.optimizer import (
    FailureWindow,
    MetricConstraint,
    OptimizerValidationSummary,
    OptimizerValidationSummaryWriter,
    ResearchValidationPolicy,
    WalkForwardPlan,
    WalkForwardRobustnessPolicy,
    WalkForwardSplit,
    derive_capital_metrics,
)
from qts.research.portfolio_ensemble import (
    evaluate_portfolio_ensemble,
    scan_portfolio_ensemble_allocations,
    scan_volatility_managed_allocations,
)
from qts.research.report import (
    ResearchReviewDecision,
    ResearchWorkflowReport,
    ResearchWorkflowReportWriter,
)
from qts.research.trade_diagnostics import (
    TradeDiagnostic,
    TradeDiagnosticsArtifactWriter,
    TradeDiagnosticsReport,
)


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

        session_config = getattr(session, "config", None)
        research_config_path = getattr(session_config, "research_config_path", None)
        backtest_config_path = getattr(session_config, "backtest_config_path", None)
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
            "selection_policy": _json_ready(self.selection_policy),
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


def _review_decision_from_payload(value: Any) -> ResearchReviewDecision | None:
    if value is None:
        return None
    if isinstance(value, ResearchReviewDecision):
        return value
    if not isinstance(value, Mapping):
        raise ValueError("research_report.decision must be a mapping")
    return ResearchReviewDecision(
        status=str(value.get("status", "keep_researching")),
        reviewer=None if value.get("reviewer") is None else str(value["reviewer"]),
        reason=_string_or_sequence_tuple(value.get("reason", ()), field_name="decision.reason"),
        required_next_evidence=_string_or_sequence_tuple(
            value.get("required_next_evidence", ()),
            field_name="decision.required_next_evidence",
        ),
        evidence_bundle_id=(
            None if value.get("evidence_bundle_id") is None else str(value["evidence_bundle_id"])
        ),
        trade_diagnostics_available=bool(value.get("trade_diagnostics_available", False)),
        validation_scorecard_available=bool(value.get("validation_scorecard_available", False)),
        cost_stress_available=bool(value.get("cost_stress_available", False)),
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


def _string_sequence(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field_name} must be a sequence")
    return tuple(str(item) for item in value)


def _string_or_sequence_tuple(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return () if not text else (text,)
    if not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a string or sequence")
    return tuple(str(item) for item in value)


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
class ResearchWorkflowStepResult:
    """One deterministic workflow step execution result."""

    step_id: str
    kind: str
    status: str
    message: str
    outputs: Mapping[str, Any]

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready step result payload."""

        return {
            "id": self.step_id,
            "kind": self.kind,
            "message": self.message,
            "outputs": _json_ready(self.outputs),
            "status": self.status,
        }


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
            payload["idea_metadata"] = _json_ready(self.idea_metadata)
        if self.decision is not None:
            payload["decision"] = _json_ready(self.decision)
        if self.periods:
            period_payloads = [
                ResearchWorkflowRunner._declared_period_payload(period) for period in self.periods
            ]
            payload["periods"] = period_payloads
            payload["report_only_periods"] = ResearchWorkflowRunner._report_only_period_names(
                period_payloads
            )
            payload["selection_basis"] = ResearchWorkflowRunner._selection_basis(period_payloads)
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
                return self._factor_candidates(session, step)
            if step.kind == "factor_review_gate":
                return self._factor_review_gate(session, step)
            if step.kind == "implementation_gate":
                return self._implementation_gate(step)
            if step.kind == "factor_evaluation":
                return self._factor_evaluation(session, config, step)
            if step.kind == "factor_tearsheet":
                return self._factor_tearsheet(session, config, step)
            if step.kind == "ablation":
                return self._ablation(config, step)
            if step.kind == "trade_diagnostics":
                return self._trade_diagnostics(config, step)
            if step.kind == "backtest":
                return self._backtest(session, config, step)
            if step.kind == "backtest_matrix":
                return self._backtest_matrix(session, config, step)
            if step.kind == "optimize":
                return self._optimize(session, config, step)
            if step.kind == "portfolio_ensemble":
                return self._portfolio_ensemble(config, step)
            if step.kind == "portfolio_ensemble_scan":
                return self._portfolio_ensemble_scan(config, step)
            if step.kind == "portfolio_volatility_managed_scan":
                return self._portfolio_volatility_managed_scan(config, step)
            if step.kind == "research_report":
                return self._research_report(
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

    def _factor_candidates(
        self,
        session: Any,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        query = _required_text(step.payload, "query")
        batch = session.find_factor_candidates(
            query,
            sources=optional_string_tuple(step.payload.get("sources")),
            max_results=optional_int(step.payload.get("max_results")),
            from_year=optional_int(step.payload.get("from_year")),
            to_year=optional_int(step.payload.get("to_year")),
            refresh=bool(step.payload.get("refresh", False)),
        )
        specs = tuple(getattr(batch, "specs", ()))
        result_query = getattr(getattr(batch, "result", None), "query", None)
        outputs = {
            "candidate_count": len(specs),
            "query_id": getattr(result_query, "query_id", ""),
            "spec_names": [getattr(spec, "name", "") for spec in specs],
        }
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="factor candidates persisted",
            outputs=outputs,
        )

    def _factor_review_gate(
        self,
        session: Any,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        status = str(step.payload.get("status", "accepted"))
        min_count = int(step.payload.get("min_count", 1))
        if min_count <= 0:
            raise ValueError("min_count must be positive")
        specs = session.list_factor_specs_by_status(status)
        outputs = {
            "matched_count": len(specs),
            "min_count": min_count,
            "spec_names": [getattr(spec, "name", "") for spec in specs],
            "status": status,
        }
        passed = len(specs) >= min_count
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed" if passed else "blocked",
            message="review gate passed" if passed else "review gate blocked workflow",
            outputs=outputs,
        )

    def _implementation_gate(self, step: ResearchWorkflowStepConfig) -> ResearchWorkflowStepResult:
        required_modules = string_tuple(step.payload.get("required_modules", ()))
        required_strategy = step.payload.get("required_strategy")
        missing_modules = [module for module in required_modules if not self._can_import(module)]
        missing_strategies: list[str] = []
        if required_strategy is not None and not self._can_resolve_attribute(
            str(required_strategy)
        ):
            missing_strategies.append(str(required_strategy))
        outputs = {
            "missing_modules": missing_modules,
            "missing_strategies": missing_strategies,
            "required_modules": list(required_modules),
            "required_strategy": required_strategy,
        }
        passed = not missing_modules and not missing_strategies
        message = "implementation gate passed" if passed else "implementation gate blocked workflow"
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed" if passed else "blocked",
            message=message,
            outputs=outputs,
        )

    def _factor_evaluation(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        factor_name = _required_text(step.payload, "factor_name")
        factor_version = _required_text(step.payload, "factor_version")
        bucket_count = int(step.payload.get("bucket_count", 5))
        raw_snapshots = step.payload.get("snapshots")
        if not isinstance(raw_snapshots, list | tuple) or not raw_snapshots:
            raise ValueError("factor_evaluation requires non-empty snapshots")
        output_dir = step.payload.get("output_dir")
        resolved_snapshots: list[dict[str, object]] = []
        for snapshot in raw_snapshots:
            if not isinstance(snapshot, Mapping):
                raise ValueError("factor_evaluation snapshots must be mappings")
            factor_scores = snapshot.get("factor_scores")
            if not isinstance(factor_scores, str | Path):
                raise ValueError("factor_evaluation snapshot.factor_scores must be a path")
            forward_returns = snapshot.get("forward_returns")
            if not isinstance(forward_returns, str | Path):
                raise ValueError("factor_evaluation snapshot.forward_returns must be a path")
            resolved_snapshots.append(
                {
                    **_snapshot_protocol_payload(snapshot),
                    "as_of": _json_ready(snapshot.get("as_of")),
                    "factor_scores": str(config.resolve_path(factor_scores)),
                    "forward_returns": str(config.resolve_path(forward_returns)),
                }
            )
        evaluated = session.evaluate_factor(
            factor_name=factor_name,
            factor_version=factor_version,
            snapshots=resolved_snapshots,
            bucket_count=bucket_count,
            output_dir=config.resolve_path(str(output_dir)) if output_dir is not None else None,
        )
        latest_result = evaluated[-1].result.metrics
        outputs = {
            "factor_name": factor_name,
            "factor_version": factor_version,
            "artifact_paths": [str(item.artifact_path) for item in evaluated],
            "snapshot_count": len(evaluated),
            "rank_ic": str(latest_result.rank_ic),
            "long_short_spread": str(latest_result.long_short_spread),
            "coverage": str(latest_result.coverage),
            "return_count": latest_result.return_count,
            "scored_count": latest_result.scored_count,
            "turnover": None if latest_result.turnover is None else str(latest_result.turnover),
        }
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="factor evaluation completed",
            outputs=outputs,
        )

    def _ablation(
        self,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        baseline = _required_text(step.payload, "baseline")
        modules = string_tuple(step.payload.get("modules", ()))
        primary_metric = _required_text(step.payload, "primary_metric")
        higher_is_better = step.payload.get("higher_is_better", True)
        if not isinstance(higher_is_better, bool):
            raise ValueError("higher_is_better must be a boolean")
        source_summary = step.payload.get("source_summary")
        if source_summary is not None:
            source_payload = _load_json_mapping(config.resolve_path(str(source_summary)))
            plan = AblationPlan.from_backtest_matrix_summary(
                source_payload,
                baseline=baseline,
                module_map=self._module_map(step.payload.get("module_map")),
            )
        else:
            raw_runs = step.payload.get("runs")
            if not isinstance(raw_runs, list) or not raw_runs:
                raise ValueError("ablation runs must not be empty")
            runs = tuple(
                self._ablation_run(raw_run, index=index) for index, raw_run in enumerate(raw_runs)
            )
            plan = AblationPlan(
                baseline=baseline,
                modules=modules,
                runs=runs,
            )
        report = AblationReport.from_plan(
            plan,
            primary_metric=primary_metric,
            higher_is_better=higher_is_better,
        )
        output_root = step.payload.get("output_root", "ablation")
        if not isinstance(output_root, (str, Path)):
            raise ValueError("ablation output_root must be a path")
        writer = AblationReportWriter(config.resolve_path(output_root))
        paths = writer.write(
            report,
            json_path=str(step.payload.get("summary_output", "ablation-summary.json")),
            markdown_path=str(step.payload.get("report_output", "ablation-report.md")),
        )
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="ablation artifacts written",
            outputs={
                "ablation_summary": report.to_dict(),
                "artifact_path": str(paths.json_path),
                "artifact_paths": [str(paths.json_path), str(paths.markdown_path)],
                "report_path": str(paths.markdown_path),
            },
        )

    def _trade_diagnostics(
        self,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        raw_trades = step.payload.get("trades")
        if not isinstance(raw_trades, list) or not raw_trades:
            raise ValueError("trade_diagnostics trades must not be empty")
        trades = tuple(
            self._trade_diagnostic(raw_trade, index=index)
            for index, raw_trade in enumerate(raw_trades)
        )
        output_root = step.payload.get("output_root", "trade-diagnostics")
        if not isinstance(output_root, (str, Path)):
            raise ValueError("trade_diagnostics output_root must be a path")
        report = TradeDiagnosticsReport(trades=trades)
        artifacts = TradeDiagnosticsArtifactWriter().write(
            config.resolve_path(output_root),
            report,
        )
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="trade diagnostics artifacts written",
            outputs={
                "artifact_path": str(artifacts.summary_path),
                "artifact_paths": [
                    str(artifacts.trades_path),
                    str(artifacts.summary_path),
                    str(artifacts.markdown_path),
                ],
                "report_path": str(artifacts.markdown_path),
                "summary_path": str(artifacts.summary_path),
                "trade_count": len(trades),
                "trades_path": str(artifacts.trades_path),
            },
        )

    def _research_report(
        self,
        config: ResearchWorkflowConfig,
        run_context: ResearchWorkflowRunContext,
        steps: tuple[ResearchWorkflowStepResult, ...],
        step: ResearchWorkflowStepConfig,
        *,
        idea_metadata: Mapping[str, Any] | None = None,
    ) -> ResearchWorkflowStepResult:
        writer_root = (
            config.resolve_path(_required_text(step.payload, "output_root"))
            if "output_root" in step.payload
            else None
        )
        if writer_root is None:
            writer_root = config.workflow_config_path.parent / "research-workflow-reports"
        writer = ResearchWorkflowReportWriter(writer_root)
        report_output_path = str(step.payload.get("output_path", "workflow-report.md"))
        report = ResearchWorkflowReport.from_result(
            ResearchWorkflowResult(
                workflow_id=config.workflow_id,
                periods=config.periods,
                decision=_review_decision_from_payload(step.payload.get("decision")),
                run_context=run_context,
                route=config.route,
                idea_metadata=idea_metadata,
                status="completed",
                steps=steps,
            )
        )
        report_path = writer.write(report, output_path=report_output_path)
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="research report written",
            outputs={"decision": report.decision.to_payload(), "report_path": str(report_path)},
        )

    def _portfolio_ensemble(
        self,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        payload = dict(step.payload)
        raw_legs = payload.get("legs")
        if not isinstance(raw_legs, list):
            raise ValueError("portfolio_ensemble.legs must be a non-empty list")
        resolved_legs: list[dict[str, Any]] = []
        for index, raw_leg in enumerate(raw_legs):
            if not isinstance(raw_leg, Mapping):
                raise ValueError(f"portfolio_ensemble.legs[{index}] must be a mapping")
            leg_payload = dict(raw_leg)
            leg_payload["manifest_path"] = str(
                config.resolve_path(_required_text(leg_payload, "manifest_path"))
            )
            resolved_legs.append(leg_payload)
        payload["legs"] = resolved_legs
        result = evaluate_portfolio_ensemble(payload)
        summary_output = step.payload.get("summary_output")
        summary_path = (
            config.resolve_path(str(summary_output))
            if summary_output is not None
            else config.workflow_config_path.parent
            / f"{result['allocation_name']}-portfolio-ensemble-summary.json"
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(_json_ready(result), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="portfolio ensemble research summary written",
            outputs={
                "allocation_name": result["allocation_name"],
                "leg_count": result["leg_count"],
                "point_count": result["point_count"],
                "research_only": result["research_only"],
                "summary_path": str(summary_path),
            },
        )

    def _portfolio_ensemble_scan(
        self,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        payload = dict(step.payload)
        scan_periods = string_tuple(payload.get("periods"))
        period_roles = config.period_roles_for(scan_periods)
        if period_roles:
            payload["period_roles"] = period_roles
        payload["candidates"] = self._resolved_period_manifest_candidates(
            config,
            step,
            kind_name="portfolio_ensemble_scan",
        )
        result = scan_portfolio_ensemble_allocations(payload)
        period_payloads = self._named_period_payloads(config, scan_periods)
        report_only_periods = [
            period for period, role in period_roles.items() if role in _REPORT_ONLY_PERIOD_ROLES
        ]
        summary_payload = dict(result)
        if period_payloads:
            summary_payload["periods"] = period_payloads
            summary_payload["report_only_periods"] = report_only_periods
        summary_output = step.payload.get("summary_output")
        summary_path = (
            config.resolve_path(str(summary_output))
            if summary_output is not None
            else config.workflow_config_path.parent
            / f"{result['scan_name']}-portfolio-ensemble-scan-summary.json"
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(_json_ready(summary_payload), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        outputs: dict[str, Any] = {
            "candidate_count": result["candidate_count"],
            "evaluated_allocation_count": result["evaluated_allocation_count"],
            "satisfying_allocation_count": result["satisfying_allocation_count"],
            "summary_path": str(summary_path),
        }
        if period_payloads:
            outputs["periods"] = period_payloads
            outputs["report_only_periods"] = report_only_periods
            outputs["score_periods"] = result["score_periods"]
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="portfolio ensemble allocation scan written",
            outputs=outputs,
        )

    def _portfolio_volatility_managed_scan(
        self,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        payload = dict(step.payload)
        scan_periods = string_tuple(payload.get("periods"))
        period_roles = config.period_roles_for(scan_periods)
        if period_roles:
            payload["period_roles"] = period_roles
        payload["candidates"] = self._resolved_period_manifest_candidates(
            config,
            step,
            kind_name="portfolio_volatility_managed_scan",
        )
        result = scan_volatility_managed_allocations(payload)
        period_payloads = self._named_period_payloads(config, scan_periods)
        report_only_periods = [
            period for period, role in period_roles.items() if role in _REPORT_ONLY_PERIOD_ROLES
        ]
        summary_payload = dict(result)
        if period_payloads:
            summary_payload["periods"] = period_payloads
            summary_payload["report_only_periods"] = report_only_periods
        summary_output = step.payload.get("summary_output")
        summary_path = (
            config.resolve_path(str(summary_output))
            if summary_output is not None
            else config.workflow_config_path.parent
            / f"{result['scan_name']}-portfolio-volatility-managed-summary.json"
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(_json_ready(summary_payload), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        outputs = {
            "candidate_count": result["candidate_count"],
            "evaluated_parameter_count": result["evaluated_parameter_count"],
            "satisfying_allocation_count": result["satisfying_allocation_count"],
            "summary_path": str(summary_path),
        }
        if period_payloads:
            outputs["periods"] = period_payloads
            outputs["report_only_periods"] = report_only_periods
            outputs["selection_basis"] = result["selection_periods"]
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="portfolio volatility managed allocation scan written",
            outputs=outputs,
        )

    def _resolved_period_manifest_candidates(
        self,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
        *,
        kind_name: str,
    ) -> list[dict[str, Any]]:
        raw_candidates = step.payload.get("candidates")
        if not isinstance(raw_candidates, list):
            raise ValueError(f"{kind_name}.candidates must be a non-empty list")
        resolved_candidates: list[dict[str, Any]] = []
        for index, raw_candidate in enumerate(raw_candidates):
            if not isinstance(raw_candidate, Mapping):
                raise ValueError(f"{kind_name}.candidates[{index}] must be a mapping")
            candidate_payload = dict(raw_candidate)
            raw_manifests = candidate_payload.get("period_manifests")
            if not isinstance(raw_manifests, Mapping):
                raise ValueError(f"{kind_name}.candidate.period_manifests is required")
            candidate_payload["period_manifests"] = {
                str(period): str(config.resolve_path(str(path)))
                for period, path in raw_manifests.items()
            }
            resolved_candidates.append(candidate_payload)
        return resolved_candidates

    @staticmethod
    def _named_period_payloads(
        config: ResearchWorkflowConfig,
        period_names: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        period_by_name = config._period_by_name()
        return [
            ResearchWorkflowRunner._declared_period_payload(period_by_name[period_name])
            for period_name in period_names
            if period_name in period_by_name
        ]

    @staticmethod
    def _declared_period_payload(period: Mapping[str, Any]) -> dict[str, Any]:
        end = period["end"]
        start = period["start"]
        return {
            "end": None if end is None else end.isoformat(),
            "name": str(period["name"]),
            "role": str(period["role"]),
            "start": start.isoformat(),
        }

    def _factor_tearsheet(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        raw_artifact_paths = step.payload.get(
            "artifact_paths",
            step.payload.get("artifacts", ()),
        )
        artifact_paths = tuple(
            config.resolve_path(path) for path in string_tuple(raw_artifact_paths)
        )
        if not artifact_paths:
            raise ValueError("factor_tearsheet requires artifact_paths")
        experiment_id = step.payload.get("experiment_id")
        if experiment_id is None:
            tearsheet = session.factor_tearsheet(artifact_paths)
            outputs = {
                "factor_name": tearsheet.factor_name,
                "factor_version": tearsheet.factor_version,
                "metrics": tearsheet.manifest_metrics(),
            }
        else:
            record = session.record_factor_tearsheet(
                artifact_paths,
                experiment_id=str(experiment_id),
                strategy_name=str(step.payload.get("strategy_name", "factor-tearsheet")),
                strategy_version=str(step.payload.get("strategy_version", "1")),
                dataset_ids=string_tuple(step.payload.get("dataset_ids", ())),
            )
            outputs = {
                "experiment_id": record.experiment_id,
                "manifest_path": str(record.manifest_path),
                "metrics": dict(record.metrics),
            }
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="factor tearsheet recorded",
            outputs=outputs,
        )

    def _backtest(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        strategy_params = optional_mapping(step.payload.get("strategy_params")) or {}
        kwargs: dict[str, Any] = {"strategy_params": strategy_params}
        backtest_config = step.payload.get("backtest_config")
        if backtest_config is not None:
            kwargs["backtest_config_path"] = config.resolve_path(str(backtest_config))
        output_dir = step.payload.get("output_dir")
        if output_dir is not None:
            kwargs["output_dir"] = config.resolve_path(str(output_dir))
        materialized_cache_dir = self._materialized_replay_cache_dir(config, step.payload)
        if materialized_cache_dir is not None:
            kwargs["materialized_replay_cache_dir"] = materialized_cache_dir
        result = session.run_backtest(**kwargs)
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="backtest completed",
            outputs={
                "manifest_path": str(result.manifest_path),
                "processed_bars": result.processed_bars,
                "trading_bars": result.trading_bars,
            },
        )

    def _backtest_matrix(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        output_root = config.resolve_path(_required_text(step.payload, "output_root"))
        periods = self._matrix_periods(config, step.payload.get("periods"))
        period_payloads = self._period_payloads(periods)
        selection_basis = self._selection_basis(period_payloads)
        report_only_periods = self._report_only_period_names(period_payloads)
        candidates = self._matrix_candidates(step.payload.get("candidates"))
        base_strategy_params = optional_mapping(step.payload.get("base_strategy_params")) or {}
        metrics = string_tuple(
            step.payload.get(
                "metrics",
                [
                    "total_return",
                    "sharpe_ratio",
                    "max_drawdown",
                    "total_trades",
                    "profit_factor",
                ],
            )
        )
        kwargs: dict[str, Any] = {
            "base_strategy_params": base_strategy_params,
            "candidates": candidates,
            "metrics": metrics,
            "output_root": output_root,
            "periods": periods,
        }
        backtest_config = step.payload.get("backtest_config")
        if backtest_config is not None:
            kwargs["backtest_config_path"] = config.resolve_path(str(backtest_config))
        materialized_cache_dir = self._materialized_replay_cache_dir(config, step.payload)
        if materialized_cache_dir is not None:
            kwargs["materialized_replay_cache_dir"] = materialized_cache_dir
        rows = list(session.run_backtest_matrix(**kwargs))
        summary_payload = {
            "candidate_count": len(candidates),
            "metrics": list(metrics),
            "output_root": str(output_root),
            "period_count": len(periods),
            "rows": rows,
            "step_id": step.step_id,
            "workflow_id": config.workflow_id,
        }
        if period_payloads:
            summary_payload["periods"] = period_payloads
            summary_payload["report_only_periods"] = report_only_periods
            summary_payload["selection_basis"] = selection_basis
        summary_output = step.payload.get("summary_output")
        summary_path = (
            config.resolve_path(str(summary_output))
            if summary_output is not None
            else output_root / "summary.json"
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(_json_ready(summary_payload), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        outputs: dict[str, Any] = {
            "candidate_count": len(candidates),
            "period_count": len(periods),
            "run_count": len(rows),
            "summary_path": str(summary_path),
        }
        if period_payloads:
            outputs["periods"] = period_payloads
            outputs["report_only_periods"] = report_only_periods
            outputs["selection_basis"] = selection_basis
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="passed",
            message="backtest matrix completed",
            outputs=outputs,
        )

    def _optimize(
        self,
        session: Any,
        config: ResearchWorkflowConfig,
        step: ResearchWorkflowStepConfig,
    ) -> ResearchWorkflowStepResult:
        parameters = required_mapping(step.payload, "parameters")
        kwargs: dict[str, Any] = {
            "parameters": {str(key): list(value) for key, value in parameters.items()},
        }
        objective_metric = step.payload.get("objective_metric")
        if objective_metric is not None:
            kwargs["objective_metric"] = str(objective_metric)
        output_root = step.payload.get("output_root")
        if output_root is not None:
            kwargs["output_root"] = config.resolve_path(str(output_root))
        materialized_cache_dir = self._materialized_replay_cache_dir(config, step.payload)
        if materialized_cache_dir is not None:
            kwargs["materialized_replay_cache_dir"] = materialized_cache_dir
        results = session.optimize(**kwargs)
        capital_metric_config = optional_mapping(step.payload.get("capital_metrics"))
        constraints = self._validation_constraints(step.payload.get("validation"))
        validation_summary = OptimizerValidationSummary.from_results(
            results,
            constraints,
            capital_metric_config=capital_metric_config,
        )
        validation_policy = self._research_validation_policy(step.payload)
        validation_output = step.payload.get("validation_output")
        validation_output_path: Path | None = None
        if validation_output is not None:
            validation_output_path = config.resolve_path(str(validation_output))
            OptimizerValidationSummaryWriter().write(validation_output_path, validation_summary)
        walk_forward_payload = self._walk_forward_payload(step.payload.get("validation"))
        walk_forward_summary_payload: dict[str, Any] | None = None
        walk_forward_robustness_payload: dict[str, Any] | None = None
        walk_forward_output_path: Path | None = None
        failure_veto_payload = self._failure_window_veto_payload(step.payload.get("validation"))
        failure_veto_summary_payload: dict[str, Any] | None = None
        failure_veto_output_path: Path | None = None
        failure_veto_blocked = False
        if walk_forward_payload is not None:
            plan = self._walk_forward_plan(walk_forward_payload)
            top_n = int(walk_forward_payload.get("top_n", 1))
            if top_n <= 0:
                raise ValueError("validation.walk_forward.top_n must be positive")
            walk_forward_output_root = walk_forward_payload.get("output_root")
            walk_forward_summary = session.validate_optimizer_walk_forward(
                candidate_parameters=tuple(dict(result.parameters) for result in results[:top_n]),
                constraints=constraints,
                capital_metric_config=capital_metric_config,
                objective_metric=(None if objective_metric is None else str(objective_metric)),
                output_root=(
                    None
                    if walk_forward_output_root is None
                    else config.resolve_path(str(walk_forward_output_root))
                ),
                plan=plan,
                materialized_replay_cache_dir=materialized_cache_dir,
            )
            walk_forward_summary_payload = walk_forward_summary.to_payload()
            robustness_policy = self._walk_forward_robustness_policy(
                walk_forward_payload.get("robustness")
            )
            if robustness_policy is not None:
                walk_forward_robustness_payload = robustness_policy.evaluate(
                    walk_forward_summary
                ).to_payload()
            raw_walk_forward_output = walk_forward_payload.get("summary_output")
            if raw_walk_forward_output is not None:
                walk_forward_output_path = config.resolve_path(str(raw_walk_forward_output))
                output_payload = dict(walk_forward_summary_payload)
                if walk_forward_robustness_payload is not None:
                    output_payload["robustness"] = walk_forward_robustness_payload
                walk_forward_output_path.parent.mkdir(parents=True, exist_ok=True)
                walk_forward_output_path.write_text(
                    json.dumps(
                        _json_ready(output_payload),
                        sort_keys=True,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
        if failure_veto_payload is not None:
            top_n = int(failure_veto_payload.get("top_n", 1))
            if top_n <= 0:
                raise ValueError("validation.failure_window_veto.top_n must be positive")
            require_passing_candidate = self._failure_veto_require_passing_candidate(
                failure_veto_payload
            )
            failure_veto_output_root = failure_veto_payload.get("output_root")
            failure_veto_summary = session.validate_optimizer_failure_window_veto(
                candidate_parameters=tuple(dict(result.parameters) for result in results[:top_n]),
                constraints=self._failure_veto_constraints(failure_veto_payload),
                capital_metric_config=capital_metric_config,
                objective_metric=(None if objective_metric is None else str(objective_metric)),
                output_root=(
                    None
                    if failure_veto_output_root is None
                    else config.resolve_path(str(failure_veto_output_root))
                ),
                windows=self._failure_windows(
                    failure_veto_payload,
                    field_name="windows",
                    report_only=False,
                ),
                report_only_windows=self._failure_windows(
                    failure_veto_payload,
                    field_name="report_only_windows",
                    report_only=True,
                ),
                materialized_replay_cache_dir=materialized_cache_dir,
            )
            failure_veto_summary_payload = failure_veto_summary.to_payload()
            raw_failure_veto_output = failure_veto_payload.get("summary_output")
            if raw_failure_veto_output is not None:
                failure_veto_output_path = config.resolve_path(str(raw_failure_veto_output))
                failure_veto_output_path.parent.mkdir(parents=True, exist_ok=True)
                failure_veto_output_path.write_text(
                    json.dumps(
                        _json_ready(failure_veto_summary_payload),
                        sort_keys=True,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
            decision = failure_veto_summary_payload.get("decision", {})
            failure_veto_blocked = (
                require_passing_candidate
                and isinstance(decision, Mapping)
                and decision.get("accepted") is False
            )
        validation_payload = optional_mapping(step.payload.get("validation")) or {}
        validation_policy_payload = validation_policy.evaluate(
            validation_summary,
            walk_forward_present=walk_forward_summary_payload is not None,
            failure_window_present=failure_veto_summary_payload is not None,
            cost_stress_present=validation_payload.get("cost_stress") is not None,
        )
        ranked_results = []
        for result in results:
            ranked_result = {
                "manifest_hash": result.manifest_hash,
                "manifest_path": str(result.manifest_path),
                "objective_value": str(result.objective_value),
                "parameters": dict(result.parameters),
            }
            if capital_metric_config is not None:
                ranked_result["capital_metrics"] = derive_capital_metrics(
                    result,
                    capital_metric_config,
                )
            ranked_results.append(ranked_result)
        outputs: dict[str, Any] = {
            "ranked_results": ranked_results,
            "run_count": len(results),
            "validation_output": (
                None if validation_output_path is None else str(validation_output_path)
            ),
            "validation_summary": validation_summary.to_payload(),
            "validation_policy": validation_policy_payload,
            "validation_scorecard": self._validation_scorecard(
                validation_policy_payload=validation_policy_payload,
                validation=validation_payload,
            ),
        }
        if walk_forward_summary_payload is not None:
            outputs["walk_forward_validation"] = walk_forward_summary_payload
            outputs["walk_forward_validation_output"] = (
                None if walk_forward_output_path is None else str(walk_forward_output_path)
            )
            if walk_forward_robustness_payload is not None:
                outputs["walk_forward_robustness"] = walk_forward_robustness_payload
        if failure_veto_summary_payload is not None:
            outputs["failure_window_veto"] = failure_veto_summary_payload
            outputs["failure_window_veto_output"] = (
                None if failure_veto_output_path is None else str(failure_veto_output_path)
            )
        validation_policy_blocked = bool(validation_policy_payload.get("blocked", False))
        blocked = failure_veto_blocked or validation_policy_blocked
        message = "optimization completed"
        if failure_veto_blocked:
            message = "failure-window veto blocked workflow"
        elif validation_policy_blocked:
            message = "optimizer validation policy blocked workflow"
        return ResearchWorkflowStepResult(
            step_id=step.step_id,
            kind=step.kind,
            status="blocked" if blocked else "passed",
            message=message,
            outputs=outputs,
        )

    def _research_validation_policy(
        self, step_payload: Mapping[str, Any]
    ) -> ResearchValidationPolicy:
        raw_policy = optional_mapping(step_payload.get("validation_policy")) or {}
        validation = optional_mapping(step_payload.get("validation")) or {}
        raw_required = raw_policy.get(
            "require_passing_candidate",
            validation.get("require_passing_candidate", False),
        )
        if not isinstance(raw_required, bool):
            raise ValueError("validation_policy.require_passing_candidate must be a boolean")
        return ResearchValidationPolicy(
            require_passing_candidate=raw_required,
            min_accepted_count=optional_non_negative_int(
                raw_policy.get("min_accepted_count"),
                field_name="validation_policy.min_accepted_count",
            ),
            min_robustness_score=optional_decimal(
                raw_policy.get("min_robustness_score"),
                field_name="validation_policy.min_robustness_score",
            ),
            require_walk_forward=optional_bool(
                raw_policy.get("require_walk_forward", False),
                field_name="validation_policy.require_walk_forward",
            ),
            require_failure_window=optional_bool(
                raw_policy.get("require_failure_window", False),
                field_name="validation_policy.require_failure_window",
            ),
            require_cost_stress=optional_bool(
                raw_policy.get("require_cost_stress", False),
                field_name="validation_policy.require_cost_stress",
            ),
            max_rejected_count=optional_non_negative_int(
                raw_policy.get("max_rejected_count"),
                field_name="validation_policy.max_rejected_count",
            ),
        )

    def _validation_scorecard(
        self,
        *,
        validation_policy_payload: Mapping[str, Any],
        validation: Any,
    ) -> dict[str, Any]:
        validation_payload = optional_mapping(validation) or {}
        return {
            "cost_stress_status": (
                "configured"
                if validation_payload.get("cost_stress") is not None
                else "not_configured"
            ),
            "failure_window_status": (
                "configured"
                if validation_payload.get("failure_window_veto") is not None
                else "not_configured"
            ),
            "rejection_reasons": list(validation_policy_payload.get("rejection_reasons", ())),
            "validation_policy_missing_evidence": list(
                validation_policy_payload.get("missing_evidence", ())
            ),
            "validation_policy_reasons": list(validation_policy_payload.get("reasons", ())),
            "robustness_score": validation_policy_payload.get("robustness_score", "0"),
            "walk_forward_status": (
                "configured"
                if validation_payload.get("walk_forward") is not None
                else "not_configured"
            ),
        }

    def _validation_constraints(self, value: Any) -> tuple[MetricConstraint, ...]:
        validation = optional_mapping(value)
        if validation is None:
            return ()
        raw_constraints = validation.get("constraints")
        if raw_constraints is None:
            return ()
        return self._metric_constraints_from_sequence(
            raw_constraints,
            field_name="validation.constraints",
        )

    def _materialized_replay_cache_dir(
        self,
        config: ResearchWorkflowConfig,
        payload: Mapping[str, Any],
    ) -> Path | None:
        value = payload.get("materialized_replay_cache")
        if value is None or value is False:
            return None
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("materialized_replay_cache must not be empty")
            return config.resolve_path(value)
        if isinstance(value, Mapping):
            if not bool(value.get("enabled", False)):
                return None
            raw_cache_dir = value.get("cache_dir")
            if not isinstance(raw_cache_dir, str) or not raw_cache_dir.strip():
                raise ValueError("materialized_replay_cache.cache_dir is required")
            return config.resolve_path(raw_cache_dir)
        raise ValueError("materialized_replay_cache must be a path or mapping")

    def _metric_constraints_from_sequence(
        self,
        value: Any,
        *,
        field_name: str,
    ) -> tuple[MetricConstraint, ...]:
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be a list")
        constraints: list[MetricConstraint] = []
        for index, raw_constraint in enumerate(value):
            if not isinstance(raw_constraint, Mapping):
                raise ValueError(f"{field_name}[{index}] must be a mapping")
            constraint = dict(raw_constraint)
            constraints.append(
                MetricConstraint(
                    metric_name=str(constraint["metric"]),
                    operator=str(constraint["operator"]),
                    threshold=Decimal(str(constraint["threshold"])),
                )
            )
        return tuple(constraints)

    def _walk_forward_payload(self, value: Any) -> dict[str, Any] | None:
        validation = optional_mapping(value)
        if validation is None:
            return None
        raw_walk_forward = validation.get("walk_forward")
        if raw_walk_forward is None:
            return None
        if not isinstance(raw_walk_forward, Mapping):
            raise ValueError("validation.walk_forward must be a mapping")
        return dict(raw_walk_forward)

    def _failure_window_veto_payload(self, value: Any) -> dict[str, Any] | None:
        validation = optional_mapping(value)
        if validation is None:
            return None
        raw_veto = validation.get("failure_window_veto")
        if raw_veto is None:
            return None
        if not isinstance(raw_veto, Mapping):
            raise ValueError("validation.failure_window_veto must be a mapping")
        return dict(raw_veto)

    def _failure_veto_constraints(
        self,
        value: Mapping[str, Any],
    ) -> tuple[MetricConstraint, ...]:
        raw_constraints = value.get("constraints")
        if raw_constraints is None or not isinstance(raw_constraints, list) or not raw_constraints:
            raise ValueError("validation.failure_window_veto.constraints must be a non-empty list")
        return self._metric_constraints_from_sequence(
            raw_constraints,
            field_name="validation.failure_window_veto.constraints",
        )

    @staticmethod
    def _failure_veto_require_passing_candidate(value: Mapping[str, Any]) -> bool:
        raw_value = value.get("require_passing_candidate", False)
        if not isinstance(raw_value, bool):
            raise ValueError(
                "validation.failure_window_veto.require_passing_candidate must be a boolean"
            )
        return raw_value

    def _failure_windows(
        self,
        value: Mapping[str, Any],
        *,
        field_name: str,
        report_only: bool,
    ) -> tuple[FailureWindow, ...]:
        raw_windows = value.get(field_name)
        if raw_windows is None:
            if field_name == "windows":
                raise ValueError("validation.failure_window_veto.windows must be a non-empty list")
            return ()
        if field_name == "windows" and (not isinstance(raw_windows, list) or not raw_windows):
            raise ValueError("validation.failure_window_veto.windows must be a non-empty list")
        if not isinstance(raw_windows, list):
            raise ValueError(f"validation.failure_window_veto.{field_name} must be a list")
        windows: list[FailureWindow] = []
        for index, raw_window in enumerate(raw_windows):
            if not isinstance(raw_window, Mapping):
                raise ValueError(
                    f"validation.failure_window_veto.{field_name}[{index}] must be a mapping"
                )
            window = dict(raw_window)
            windows.append(
                FailureWindow(
                    name=str(window["name"]),
                    start=iso_date(window["start"], "start"),
                    end=iso_date(window["end"], "end"),
                    report_only=report_only,
                )
            )
        return tuple(windows)

    def _walk_forward_plan(self, value: Mapping[str, Any]) -> WalkForwardPlan:
        raw_splits = value.get("splits")
        if not isinstance(raw_splits, list) or not raw_splits:
            raise ValueError("validation.walk_forward.splits must be a non-empty list")
        splits: list[WalkForwardSplit] = []
        for index, raw_split in enumerate(raw_splits):
            if not isinstance(raw_split, Mapping):
                raise ValueError(f"validation.walk_forward.splits[{index}] must be a mapping")
            split = dict(raw_split)
            splits.append(
                WalkForwardSplit(
                    name=str(split["name"]),
                    train_start=iso_date(split["train_start"], "train_start"),
                    train_end=iso_date(split["train_end"], "train_end"),
                    test_start=iso_date(split["test_start"], "test_start"),
                    test_end=iso_date(split["test_end"], "test_end"),
                )
            )
        return WalkForwardPlan(tuple(splits))

    def _matrix_periods(
        self,
        config: ResearchWorkflowConfig,
        value: Any,
    ) -> tuple[dict[str, Any], ...]:
        if not isinstance(value, list) or not value:
            raise ValueError("backtest_matrix.periods must be a non-empty list")
        periods: list[dict[str, Any]] = []
        workflow_periods = config._period_by_name()
        for index, raw_period in enumerate(value):
            if isinstance(raw_period, str):
                declared = workflow_periods.get(raw_period)
                if declared is None:
                    raise ValueError(f"unknown workflow period: {raw_period}")
                if declared["end"] is None:
                    raise ValueError(f"backtest_matrix period {raw_period} requires end")
                periods.append(
                    {
                        "end": declared["end"],
                        "name": declared["name"],
                        "role": declared["role"],
                        "start": declared["start"],
                    }
                )
                continue
            if not isinstance(raw_period, Mapping):
                raise ValueError(
                    f"backtest_matrix.periods[{index}] must be a mapping or period name"
                )
            period = dict(raw_period)
            name = self._safe_token(period, "name")
            role = period.get("role", config.period_role(name))
            if role is not None and str(role) not in _PERIOD_ROLES:
                raise ValueError(f"unsupported period role: {role}")
            periods.append(
                {
                    "end": iso_datetime(period["end"], "end"),
                    "name": name,
                    "role": None if role is None else str(role),
                    "start": iso_datetime(period["start"], "start"),
                }
            )
        return tuple(periods)

    @staticmethod
    def _period_payloads(periods: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
        return [
            {
                "end": None if period.get("end") is None else period["end"].isoformat(),
                "name": str(period["name"]),
                "role": period.get("role"),
                "start": period["start"].isoformat(),
            }
            for period in periods
            if period.get("role") is not None
        ]

    @staticmethod
    def _selection_basis(periods: list[dict[str, Any]]) -> list[str]:
        return [
            str(period["name"]) for period in periods if period.get("role") in _SCORING_PERIOD_ROLES
        ]

    @staticmethod
    def _report_only_period_names(periods: list[dict[str, Any]]) -> list[str]:
        return [
            str(period["name"])
            for period in periods
            if period.get("role") in _REPORT_ONLY_PERIOD_ROLES
        ]

    def _matrix_candidates(self, value: Any) -> tuple[dict[str, Any], ...]:
        if not isinstance(value, list) or not value:
            raise ValueError("backtest_matrix.candidates must be a non-empty list")
        candidates: list[dict[str, Any]] = []
        for index, raw_candidate in enumerate(value):
            if not isinstance(raw_candidate, Mapping):
                raise ValueError(f"backtest_matrix.candidates[{index}] must be a mapping")
            candidate = dict(raw_candidate)
            strategy_params = optional_mapping(candidate.get("strategy_params")) or {}
            candidates.append(
                {
                    "name": self._safe_token(candidate, "name"),
                    "strategy_params": strategy_params,
                }
            )
        return tuple(candidates)

    @staticmethod
    def _safe_token(payload: Mapping[str, Any], field_name: str) -> str:
        value = _required_text(payload, field_name)
        if any(character not in _FILENAME_SAFE_CHARS for character in value):
            raise ValueError(f"{field_name} must be filename-safe")
        return value

    def _walk_forward_robustness_policy(
        self,
        value: Any,
    ) -> WalkForwardRobustnessPolicy | None:
        payload = optional_mapping(value)
        if payload is None:
            return None
        phases = string_tuple(payload.get("phases", ["test"]))
        return WalkForwardRobustnessPolicy(
            phases=phases,
            min_windows=optional_int(payload.get("min_windows")),
            max_losing_windows=optional_int(payload.get("max_losing_windows")),
            min_window_pnl_usd=optional_decimal(payload.get("min_window_pnl_usd")),
            min_window_best_objective=optional_decimal(payload.get("min_window_best_objective")),
            min_total_pnl_usd=optional_decimal(payload.get("min_total_pnl_usd")),
        )

    @classmethod
    def _module_map(cls, value: Any) -> dict[str, tuple[str, ...]]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("module_map must be a mapping")
        return {str(key): string_tuple(item) for key, item in value.items()}

    @classmethod
    def _ablation_run(cls, value: Any, *, index: int) -> AblationRun:
        if not isinstance(value, Mapping):
            raise ValueError(f"ablation runs[{index}] must be a mapping")
        return AblationRun(
            name=_required_text(value, "name"),
            modules=string_tuple(value.get("modules", ())),
            metrics=float_mapping(value.get("metrics"), field_name=f"runs[{index}].metrics"),
            split_metrics=nested_float_mapping(
                value.get("split_metrics"),
                field_name=f"runs[{index}].split_metrics",
            ),
            trade_count=optional_int(value.get("trade_count")),
            cost_stress_metrics=nested_float_mapping(
                value.get("cost_stress_metrics"),
                field_name=f"runs[{index}].cost_stress_metrics",
            ),
        )

    @classmethod
    def _trade_diagnostic(cls, value: Any, *, index: int) -> TradeDiagnostic:
        if not isinstance(value, Mapping):
            raise ValueError(f"trade_diagnostics.trades[{index}] must be a mapping")
        return TradeDiagnostic(
            trade_id=_required_text(value, "trade_id"),
            strategy_id=_required_text(value, "strategy_id"),
            idea_id=_required_text(value, "idea_id"),
            symbol=_required_text(value, "symbol"),
            direction=_required_text(value, "direction"),
            quantity=value.get("quantity"),
            entry_time=iso_datetime(value.get("entry_time"), "entry_time"),
            exit_time=iso_datetime(value.get("exit_time"), "exit_time"),
            entry_price=optional_float(value.get("entry_price")),
            exit_price=optional_float(value.get("exit_price")),
            r_pnl=optional_float(value.get("r_pnl")),
            mae_r=optional_float(value.get("mae_r")),
            mfe_r=optional_float(value.get("mfe_r")),
            holding_bars=optional_int(value.get("holding_bars")),
            exit_reason=_required_text(value, "exit_reason"),
            time_bucket=_required_text(value, "time_bucket"),
            factor_snapshot=float_mapping(
                value.get("factor_snapshot"),
                field_name=f"trade_diagnostics.trades[{index}].factor_snapshot",
            ),
        )

    @staticmethod
    def _can_import(module_name: str) -> bool:
        try:
            importlib.import_module(module_name)
        except ImportError:
            return False
        return True

    @staticmethod
    def _can_resolve_attribute(value: str) -> bool:
        if ":" not in value:
            return False
        module_name, attribute_name = value.split(":", maxsplit=1)
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return False
        return hasattr(module, attribute_name)


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    to_payload = getattr(value, "to_payload", None)
    if callable(to_payload):
        return _json_ready(to_payload())
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_ready(item) for item in value]
    return value


def _snapshot_protocol_payload(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "available_at",
        "forward_return_end",
        "forward_return_start",
        "source_data_end",
    )
    return {field: _json_ready(snapshot[field]) for field in fields if field in snapshot}


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


def _dataset_ids(session_config: Any) -> tuple[str, ...]:
    if session_config is None:
        return ()
    explicit = getattr(session_config, "dataset_ids", None)
    if explicit is not None:
        return tuple(str(item) for item in explicit)
    catalog_name = getattr(session_config, "catalog_name", None)
    roots = getattr(session_config, "roots", ())
    timeframe = getattr(session_config, "timeframe", None)
    if not isinstance(catalog_name, str) or not isinstance(timeframe, str):
        return ()
    if not isinstance(roots, Sequence) or isinstance(roots, str):
        return ()
    return tuple(f"{catalog_name}:{root}:{timeframe}" for root in roots)


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
_SCORING_PERIOD_ROLES = frozenset({"anchor", "selection", "validation"})
_REPORT_ONLY_PERIOD_ROLES = frozenset({"holdout_report_only", "true_oos_report_only"})
_PERIOD_ROLES = _SCORING_PERIOD_ROLES | _REPORT_ONLY_PERIOD_ROLES
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
_FILENAME_SAFE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
