"""Deterministic markdown research workflow report artifacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol, cast


class _WorkflowStepResult(Protocol):
    """Protocol for workflow step result read access."""

    @property
    def step_id(self) -> str: ...

    @property
    def kind(self) -> str: ...

    @property
    def status(self) -> str: ...

    @property
    def message(self) -> str: ...

    @property
    def outputs(self) -> Mapping[str, Any]: ...


class _WorkflowResult(Protocol):
    """Protocol for workflow result read access."""

    @property
    def workflow_id(self) -> str: ...

    @property
    def status(self) -> str: ...

    @property
    def steps(self) -> Sequence[_WorkflowStepResult]: ...

    @property
    def idea_metadata(self) -> Mapping[str, Any] | None: ...


@dataclass(frozen=True, slots=True)
class ResearchReviewDecision:
    """Machine-readable human review decision attached to research evidence."""

    status: str = "keep_researching"
    reviewer: str | None = None
    reason: tuple[str, ...] = ()
    required_next_evidence: tuple[str, ...] = ()
    evidence_bundle_id: str | None = None
    trade_diagnostics_available: bool = False
    validation_scorecard_available: bool = False
    cost_stress_available: bool = False

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_REVIEW_DECISIONS:
            raise ValueError(f"unsupported review decision status: {self.status}")
        if self.status in _PROMOTION_READINESS_DECISIONS:
            if not self.evidence_bundle_id:
                raise ValueError(f"{self.status} requires evidence_bundle_id")
            if not self.trade_diagnostics_available:
                raise ValueError(f"{self.status} requires trade diagnostics")
            if not self.validation_scorecard_available:
                raise ValueError(f"{self.status} requires validation scorecard")
            if not self.cost_stress_available:
                raise ValueError(f"{self.status} requires cost stress evidence")

    def to_payload(self) -> dict[str, Any]:
        """Return deterministic JSON/YAML-compatible decision payload."""

        return {
            "cost_stress_available": self.cost_stress_available,
            "evidence_bundle_id": self.evidence_bundle_id,
            "reason": list(self.reason),
            "required_next_evidence": list(self.required_next_evidence),
            "reviewer": self.reviewer,
            "status": self.status,
            "trade_diagnostics_available": self.trade_diagnostics_available,
            "validation_scorecard_available": self.validation_scorecard_available,
        }


@dataclass(frozen=True, slots=True)
class ResearchWorkflowReport:
    """Deterministic report payload derived from workflow outputs."""

    workflow_id: str
    workflow_status: str
    steps: tuple[dict[str, Any], ...]
    periods: tuple[dict[str, str], ...] = ()
    run_context: Mapping[str, Any] = field(default_factory=dict)
    route: Mapping[str, Any] = field(default_factory=dict)
    idea_metadata: Mapping[str, Any] = field(default_factory=dict)
    decision: ResearchReviewDecision = field(default_factory=ResearchReviewDecision)

    @classmethod
    def from_result(cls, result: _WorkflowResult) -> ResearchWorkflowReport:
        """Build a deterministic report from a workflow execution result."""

        return cls(
            periods=_normalize_periods(getattr(result, "periods", ())),
            run_context=_normalize_run_context(getattr(result, "run_context", None)),
            route=_normalize_route(getattr(result, "route", None)),
            idea_metadata=_normalize_idea_metadata(getattr(result, "idea_metadata", None)),
            decision=_normalize_decision(getattr(result, "decision", None)),
            workflow_id=_required_text(result, "workflow_id"),
            workflow_status=_required_text(result, "status"),
            steps=tuple(_normalize_step(step) for step in result.steps),
        )

    def to_markdown(self) -> str:
        """Render a markdown report that is stable for the same workflow output."""

        sections = [
            self._header(),
            self._evidence_header(),
        ]
        idea_section = self._idea_section()
        if idea_section:
            sections.append(idea_section)
        sections.extend([self._summary(), self._step_section()])
        period_roles = self._period_roles_section()
        if period_roles:
            sections.append(period_roles)
        route_section = self._route_section()
        if route_section:
            sections.append(route_section)
        sections.extend([self._evidence_section(), self._decision_section(), self._footer()])
        return "\n\n".join(sections).strip()

    def _evidence_section(self) -> str:
        """Build the evidence section from recognized step outputs."""

        lines: list[str] = ["## Evidence Summary"]
        evidence = _collect_evidence(self.steps)
        for heading, content in evidence:
            lines.append(f"### {heading}")
            if not content:
                lines.append("- no data")
                continue
            for entry in content:
                lines.append(f"- {entry}")
        return "\n".join(lines)

    def _header(self) -> str:
        """Render report title and workflow metadata."""

        return (
            "# Research Workflow Report\n\n"
            f"workflow_id: {self.workflow_id}\n"
            f"workflow_status: {self.workflow_status}"
        )

    def _evidence_header(self) -> str:
        """Render run-context evidence required for promotion review traceability."""

        context = self.run_context
        dataset_ids = context.get("dataset_ids", [])
        return "\n".join(
            [
                "## Evidence Header",
                f"- Workflow config: {context.get('workflow_config_path', 'unknown')}",
                f"- Workflow config hash: {context.get('workflow_config_hash', 'unknown')}",
                f"- Research config: {context.get('research_config_path', 'unknown')}",
                f"- Research config hash: {context.get('research_config_hash', 'unknown')}",
                f"- Git branch: {context.get('git_branch', 'unknown')}",
                f"- Git commit: {context.get('git_commit', 'unknown')}",
                f"- Dirty workspace: {context.get('git_dirty', 'unknown')}",
                f"- Dataset IDs: {dataset_ids}",
                f"- Backtest config hash: {context.get('backtest_config_hash', 'unknown')}",
                f"- Generated at: {context.get('generated_at', 'unknown')}",
                f"- Promotion status: {context.get('promotion_status', 'research_only')}",
            ]
        )

    def _summary(self) -> str:
        """Render a compact count-style summary."""

        statuses = tuple(step.get("status", "unknown") for step in self.steps)
        step_counts = {
            "passed": sum(1 for status in statuses if status == "passed"),
            "failed": sum(1 for status in statuses if status == "failed"),
            "blocked": sum(1 for status in statuses if status == "blocked"),
        }
        return (
            "## Execution Summary\n"
            f"- step_count: {len(self.steps)}\n"
            f"- passed: {step_counts['passed']}\n"
            f"- blocked: {step_counts['blocked']}\n"
            f"- failed: {step_counts['failed']}"
        )

    def _step_section(self) -> str:
        """Render per-step details."""

        lines = ["## Step Results"]
        for index, step in enumerate(self.steps, start=1):
            lines.append(f"### {index}. {step['step_id']} ({step['kind']})")
            lines.append(f"- status: {step['status']}")
            lines.append(f"- message: {step['message']}")
            outputs = _dump_outputs(step.get("outputs", {}))
            if outputs:
                lines.append("- outputs:")
                lines.extend(f"  - {line}" for line in outputs.splitlines())
        return "\n".join(lines)

    def _period_roles_section(self) -> str:
        """Render declared period roles from workflow step outputs."""

        periods = _collect_period_roles(self.steps, self.periods)
        if not periods:
            return ""
        lines = [
            "## Period Roles",
            "| Period | Start | End | Role | Usage |",
            "| --- | --- | --- | --- | --- |",
        ]
        for period in periods:
            lines.append(
                "| "
                f"{period['name']} | "
                f"{period['start']} | "
                f"{period['end']} | "
                f"{period['role']} | "
                f"{period['usage']} |"
            )
        return "\n".join(lines)

    def _footer(self) -> str:
        """Render boundary statement and non-promotion note."""

        return (
            "## Non-Promotion Boundary\n"
            "This workflow report is research evidence only. "
            "It does not promote strategy code into paper/live execution."
        )

    def _route_section(self) -> str:
        """Render optional route governance metadata."""

        if not self.route:
            return ""
        lines = ["## Route Metadata"]
        for key in ("route_id", "route_name", "status", "owner"):
            if key in self.route:
                lines.append(f"- {key}: {self.route[key]}")
        if "selection_policy" in self.route:
            lines.append(f"- selection_policy: {_json_ready(self.route['selection_policy'])}")
        if "allowed_period_roles" in self.route:
            lines.append(f"- allowed_period_roles: {self.route['allowed_period_roles']}")
        return "\n".join(lines)

    def _idea_section(self) -> str:
        """Render optional research idea metadata and process warnings."""

        if not self.idea_metadata:
            return ""
        lines = ["## Idea Metadata"]
        for key in (
            "idea_id",
            "title",
            "edge_type",
            "edge_types",
            "source",
            "status",
            "trial_count",
            "data_required",
            "kill_criteria",
            "trial_budget",
        ):
            if key in self.idea_metadata:
                lines.append(f"- {key}: {_json_ready(self.idea_metadata[key])}")
        warning = _trial_budget_warning_line(self.idea_metadata)
        if warning:
            lines.append(f"- trial_budget_warning: {warning}")
        return "\n".join(lines)

    def _decision_section(self) -> str:
        """Render the machine-readable review decision block."""

        payload = self.decision.to_payload()
        lines = ["## Review Decision", "```yaml", "decision:"]
        for key in sorted(payload):
            value = payload[key]
            if isinstance(value, list):
                lines.append(f"  {key}:")
                if value:
                    lines.extend(f"    - {item}" for item in value)
                else:
                    lines.append("    []")
            else:
                lines.append(f"  {key}: {_yaml_scalar(value)}")
        lines.append("```")
        return "\n".join(lines)


class ResearchWorkflowReportWriter:
    """Owns deterministic report markdown file serialization."""

    def __init__(self, output_root: Path) -> None:
        self._output_root = output_root

    def write(
        self,
        report: ResearchWorkflowReport,
        *,
        output_path: str | Path = "workflow-report.md",
    ) -> Path:
        """Write a deterministic markdown report under the configured output root."""

        output_path = Path(output_path)
        if output_path.is_absolute():
            raise ValueError("output_path must be relative to report output root")
        if any(part == ".." for part in output_path.parts):
            raise ValueError("output_path must not use parent traversal")
        if output_path.as_posix() in {"", "."}:
            raise ValueError("output_path must include a filename")

        target = (self._output_root / output_path).resolve()
        root = self._output_root.resolve()
        if not target.is_relative_to(root):
            raise ValueError("output_path must remain inside report output root")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report.to_markdown() + "\n", encoding="utf-8")
        return target


def _collect_evidence(steps: Sequence[Mapping[str, Any]]) -> list[tuple[str, list[str]]]:
    """Collect user-facing evidence from well-known step kinds."""

    evidence: list[tuple[str, list[str]]] = []
    candidate_steps = [step for step in steps if step.get("kind") == "factor_candidates"]
    review_steps = [step for step in steps if step.get("kind") == "factor_review_gate"]
    impl_steps = [step for step in steps if step.get("kind") == "implementation_gate"]
    eval_steps = [step for step in steps if step.get("kind") == "factor_evaluation"]
    tearsheet_steps = [step for step in steps if step.get("kind") == "factor_tearsheet"]
    ablation_steps = [step for step in steps if step.get("kind") == "ablation"]
    diagnostics_steps = [step for step in steps if step.get("kind") == "trade_diagnostics"]
    backtest_steps = [step for step in steps if step.get("kind") == "backtest"]
    optimize_steps = [step for step in steps if step.get("kind") == "optimize"]
    report_steps = [step for step in steps if step.get("kind") == "research_report"]
    if candidate_steps:
        evidence.append(
            (
                "Factor Candidates",
                [
                    f"candidate_count: {latest_step_output(candidate_steps, 'candidate_count')}",
                    f"last_query_id: {latest_step_output(candidate_steps, 'query_id', '<none>')}",
                    f"last_spec_names: {latest_step_output(candidate_steps, 'spec_names', [])}",
                ],
            )
        )
    if review_steps:
        evidence.append(
            (
                "Review Gates",
                [
                    f"status: {latest_step_output(review_steps, 'status', 'accepted')}",
                    f"matched_count: {latest_step_output(review_steps, 'matched_count', 0)}",
                    f"min_count: {latest_step_output(review_steps, 'min_count', 0)}",
                ],
            )
        )
    if impl_steps:
        evidence.append(
            (
                "Implementation Gate",
                [
                    f"required_modules: {latest_step_output(impl_steps, 'required_modules', [])}",
                    (
                        "required_strategy: "
                        + str(latest_step_output(impl_steps, "required_strategy", "<none>"))
                    ),
                    f"missing_modules: {latest_step_output(impl_steps, 'missing_modules', [])}",
                    (
                        "missing_strategies: "
                        f"{latest_step_output(impl_steps, 'missing_strategies', [])}"
                    ),
                ],
            )
        )
    for index, snapshot_step in enumerate(eval_steps):
        outputs = snapshot_step.get("outputs", {})
        evidence.append(
            (
                f"Factor Evaluation #{index + 1}",
                [
                    f"factor_name: {outputs.get('factor_name')}",
                    f"factor_version: {outputs.get('factor_version')}",
                    f"snapshot_count: {outputs.get('snapshot_count')}",
                    f"artifact_paths: {outputs.get('artifact_paths', [])}",
                ],
            )
        )
    for index, tearsheet in enumerate(tearsheet_steps):
        outputs = tearsheet.get("outputs", {})
        factor_name = outputs.get("factor_name")
        experiment_id = outputs.get("experiment_id", "<not recorded>")
        manifest_path = outputs.get("manifest_path", "<not recorded>")
        evidence.append(
            (
                f"Factor Teardown #{index + 1}",
                [
                    f"factor_name: {factor_name}",
                    (f"experiment_id: {experiment_id}"),
                    (f"manifest_path: {manifest_path}"),
                ],
            )
        )
    for index, ablation_step in enumerate(ablation_steps):
        outputs = ablation_step.get("outputs", {})
        summary = _as_mapping(outputs.get("ablation_summary", {}))
        variants = summary.get("variants", ())
        variant_count = len(variants) if isinstance(variants, Sequence) else 0
        evidence.append(
            (
                f"Ablation #{index + 1}",
                [
                    f"baseline: {summary.get('baseline', '<none>')}",
                    f"primary_metric: {summary.get('primary_metric', '<none>')}",
                    f"variant_count: {variant_count}",
                    f"artifact_path: {outputs.get('artifact_path', '<none>')}",
                    f"report_path: {outputs.get('report_path', '<none>')}",
                ],
            )
        )
    for index, diagnostics_step in enumerate(diagnostics_steps):
        outputs = diagnostics_step.get("outputs", {})
        evidence.append(
            (
                f"Trade Diagnostics #{index + 1}",
                [
                    f"trade_count: {outputs.get('trade_count', 0)}",
                    f"trades_path: {outputs.get('trades_path', '<none>')}",
                    f"summary_path: {outputs.get('summary_path', '<none>')}",
                    f"report_path: {outputs.get('report_path', '<none>')}",
                ],
            )
        )
    if backtest_steps:
        evidence.append(
            (
                "Backtest",
                [
                    f"manifest_path: {latest_step_output(backtest_steps, 'manifest_path')}",
                    f"processed_bars: {latest_step_output(backtest_steps, 'processed_bars', 0)}",
                    f"trading_bars: {latest_step_output(backtest_steps, 'trading_bars', 0)}",
                ],
            )
        )
    if optimize_steps:
        validation_summary = latest_step_output(optimize_steps, "validation_summary", {})
        validation_mapping = validation_summary if isinstance(validation_summary, Mapping) else {}
        validation_scorecard = latest_step_output(optimize_steps, "validation_scorecard", {})
        scorecard_mapping = (
            validation_scorecard if isinstance(validation_scorecard, Mapping) else {}
        )
        validation_policy = latest_step_output(optimize_steps, "validation_policy", {})
        policy_mapping = validation_policy if isinstance(validation_policy, Mapping) else {}
        evidence.append(
            (
                "Optimize",
                [
                    f"run_count: {latest_step_output(optimize_steps, 'run_count', 0)}",
                    f"accepted_count: {validation_mapping.get('accepted_count', '<none>')}",
                    f"rejected_count: {validation_mapping.get('rejected_count', '<none>')}",
                    (
                        "cost_stress_status: "
                        f"{scorecard_mapping.get('cost_stress_status', '<none>')}"
                    ),
                    (
                        "walk_forward_status: "
                        f"{scorecard_mapping.get('walk_forward_status', '<none>')}"
                    ),
                    (
                        "failure_window_status: "
                        f"{scorecard_mapping.get('failure_window_status', '<none>')}"
                    ),
                    f"robustness_score: {scorecard_mapping.get('robustness_score', '<none>')}",
                    (
                        "top_objective: "
                        f"{first_ranked_result_value(optimize_steps, 'objective_value')}"
                    ),
                    (f"top_pnl_usd: {first_ranked_capital_metric(optimize_steps, 'pnl_usd')}"),
                    (
                        "top_return_on_margin_proxy: "
                        f"{first_ranked_capital_metric(optimize_steps, 'return_on_margin_proxy')}"
                    ),
                    *_optimizer_rejection_lines(validation_mapping),
                    *_optimizer_validation_policy_lines(policy_mapping),
                ],
            )
        )
    if report_steps:
        evidence.append(
            (
                "Research Report",
                [
                    f"report_path: {latest_step_output(report_steps, 'report_path', '<none>')}",
                ],
            )
        )
    return evidence


def _optimizer_rejection_lines(validation_summary: Mapping[str, Any]) -> list[str]:
    """Return readable optimizer rejection evidence lines."""

    raw_rejections = validation_summary.get("rejections", ())
    if not isinstance(raw_rejections, Sequence) or isinstance(raw_rejections, str):
        return []

    lines: list[str] = []
    for index, raw_rejection in enumerate(raw_rejections, start=1):
        if not isinstance(raw_rejection, Mapping):
            continue
        lines.append(f"Rejected Candidates #{index}:")
        for key in ("manifest_path", "raw_rank", "accepted_rank", "objective_value"):
            if key in raw_rejection:
                lines.append(f"{key}: {_json_ready(raw_rejection[key])}")
        reasons = raw_rejection.get("rejection_reasons", raw_rejection.get("reasons", ()))
        if isinstance(reasons, Sequence) and not isinstance(reasons, str):
            for reason in reasons:
                lines.append(f"rejection_reason: {reason}")
        elif reasons:
            lines.append(f"rejection_reason: {reasons}")
    return lines


def _optimizer_validation_policy_lines(validation_policy: Mapping[str, Any]) -> list[str]:
    """Return readable validation-policy hard-gate evidence lines."""

    lines: list[str] = []
    if not validation_policy:
        return lines
    if "blocked" in validation_policy:
        lines.append(f"validation_policy_blocked: {validation_policy['blocked']}")
    reasons = validation_policy.get("reasons", ())
    if isinstance(reasons, Sequence) and not isinstance(reasons, str):
        lines.extend(f"validation_policy_reason: {reason}" for reason in reasons)
    elif reasons:
        lines.append(f"validation_policy_reason: {reasons}")
    missing = validation_policy.get("missing_evidence", ())
    if isinstance(missing, Sequence) and not isinstance(missing, str):
        lines.extend(f"missing_evidence: {item}" for item in missing)
    elif missing:
        lines.append(f"missing_evidence: {missing}")
    return lines


def _collect_period_roles(
    steps: Sequence[Mapping[str, Any]],
    declared_periods: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, str]]:
    """Collect deterministic period role rows from step outputs."""

    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for step in steps:
        outputs = _as_mapping(step.get("outputs", {}))
        raw_periods = outputs.get("periods", ())
        if not isinstance(raw_periods, Sequence) or isinstance(raw_periods, str):
            continue
        selection_basis = _string_set(outputs.get("selection_basis", ()))
        report_only = _string_set(outputs.get("report_only_periods", ()))
        score_periods = _string_set(outputs.get("score_periods", ()))
        for raw_period in raw_periods:
            if not isinstance(raw_period, Mapping):
                continue
            name = raw_period.get("name")
            role = raw_period.get("role")
            if not isinstance(name, str) or not isinstance(role, str):
                continue
            if name in seen:
                continue
            seen.add(name)
            usage = "period_role"
            if name in report_only:
                usage = "report_only"
            elif name in selection_basis:
                usage = "selection_basis"
            elif name in score_periods:
                usage = "score_period"
            rows.append(
                {
                    "end": str(raw_period.get("end")),
                    "name": name,
                    "role": role,
                    "start": str(raw_period.get("start")),
                    "usage": usage,
                }
            )
    for period in declared_periods:
        name = period.get("name")
        role = period.get("role")
        if not isinstance(name, str) or not isinstance(role, str):
            continue
        if name in seen:
            continue
        seen.add(name)
        rows.append(
            {
                "end": str(period.get("end")),
                "name": name,
                "role": role,
                "start": str(period.get("start")),
                "usage": "declared",
            }
        )
    return rows


def _normalize_periods(periods: Any) -> tuple[dict[str, str], ...]:
    if not isinstance(periods, Sequence) or isinstance(periods, str):
        return ()
    normalized: list[dict[str, str]] = []
    for period in periods:
        if not isinstance(period, Mapping):
            continue
        name = period.get("name")
        role = period.get("role")
        if not isinstance(name, str) or not isinstance(role, str):
            continue
        normalized.append(
            {
                "end": _format_period_bound(period.get("end")),
                "name": name,
                "role": role,
                "start": _format_period_bound(period.get("start")),
            }
        )
    return tuple(normalized)


def _normalize_run_context(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], _json_ready(value))
    to_payload = getattr(value, "to_payload", None)
    if callable(to_payload):
        payload = to_payload()
        if isinstance(payload, Mapping):
            return cast(Mapping[str, Any], _json_ready(payload))
    raise ValueError("run_context must be a mapping-like payload")


def _normalize_route(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], _json_ready(value))
    to_payload = getattr(value, "to_payload", None)
    if callable(to_payload):
        payload = to_payload()
        if isinstance(payload, Mapping):
            return cast(Mapping[str, Any], _json_ready(payload))
    raise ValueError("route must be a mapping-like payload")


def _normalize_idea_metadata(value: Any) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], _json_ready(value))
    to_payload = getattr(value, "to_payload", None)
    if callable(to_payload):
        payload = to_payload()
        if isinstance(payload, Mapping):
            return cast(Mapping[str, Any], _json_ready(payload))
    raise ValueError("idea_metadata must be a mapping-like payload")


def _normalize_decision(value: Any) -> ResearchReviewDecision:
    if value is None:
        return ResearchReviewDecision()
    if isinstance(value, ResearchReviewDecision):
        return value
    if isinstance(value, Mapping):
        return ResearchReviewDecision(
            status=str(value.get("status", "keep_researching")),
            reviewer=None if value.get("reviewer") is None else str(value["reviewer"]),
            reason=_string_tuple_field(value.get("reason", ()), field_name="reason"),
            required_next_evidence=_string_tuple_field(
                value.get("required_next_evidence", ()),
                field_name="required_next_evidence",
            ),
            evidence_bundle_id=(
                None
                if value.get("evidence_bundle_id") is None
                else str(value["evidence_bundle_id"])
            ),
            trade_diagnostics_available=bool(value.get("trade_diagnostics_available", False)),
            validation_scorecard_available=bool(value.get("validation_scorecard_available", False)),
            cost_stress_available=bool(value.get("cost_stress_available", False)),
        )
    raise ValueError("decision must be a ResearchReviewDecision or mapping")


def _format_period_bound(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def _string_set(value: Any) -> set[str]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return set()
    return {str(item) for item in value}


def _string_tuple_field(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return () if not text else (text,)
    if not isinstance(value, Sequence):
        raise ValueError(f"decision {field_name} must be a string or sequence")
    return tuple(str(item) for item in value)


def first_ranked_result_value(steps: Sequence[Mapping[str, Any]], key: str) -> Any:
    """Return first ranked result value for optimize output, if present."""

    for step in steps:
        ranked_results = step.get("outputs", {}).get("ranked_results", ())
        if not isinstance(ranked_results, Sequence) or not ranked_results:
            continue
        first = ranked_results[0]
        if isinstance(first, Mapping):
            value = first.get(key)
            if value is not None:
                return value
    return "<none>"


def first_ranked_capital_metric(steps: Sequence[Mapping[str, Any]], key: str) -> Any:
    """Return first ranked capital metric value for optimize output, if present."""

    for step in steps:
        ranked_results = step.get("outputs", {}).get("ranked_results", ())
        if not isinstance(ranked_results, Sequence) or not ranked_results:
            continue
        first = ranked_results[0]
        if not isinstance(first, Mapping):
            continue
        capital_metrics = first.get("capital_metrics")
        if not isinstance(capital_metrics, Mapping):
            continue
        value = capital_metrics.get(key)
        if value is not None:
            return value
    return "<none>"


def latest_step_output(
    steps: Sequence[Mapping[str, Any]],
    key: str,
    default: Any = "",
) -> Any:
    """Return the output field value from the most recent step."""

    if not steps:
        return default
    outputs = _as_mapping(steps[-1].get("outputs"))
    return outputs.get(key, default)


def _dump_outputs(outputs: Mapping[str, Any]) -> str:
    """Render mapping outputs as deterministic key-value lines."""

    lines: list[str] = []
    for key in sorted(outputs):
        lines.append(f"{key}: {_json_ready(outputs[key])}")
    return "\n".join(lines)


def _required_text_from_mapping(payload: Mapping[str, Any], field_name: str) -> str:
    """Return a required string value from mapping-like payload."""

    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _json_ready(value: Any) -> Any:
    """Convert common values to JSON-safe equivalents for report rendering."""

    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _normalize_step(step: _WorkflowStepResult) -> dict[str, Any]:
    """Map a typed workflow step result into JSON-ready dict form."""

    if isinstance(step, Mapping):
        step_map: Mapping[str, Any] = step
    else:
        step_map = {
            "kind": getattr(step, "kind", None),
            "status": getattr(step, "status", None),
            "step_id": getattr(step, "step_id", None),
            "message": getattr(step, "message", None),
            "outputs": getattr(step, "outputs", None),
        }
    return {
        "kind": _required_text_from_mapping(step_map, "kind"),
        "status": _required_text_from_mapping(step_map, "status"),
        "step_id": _required_text_from_mapping(step_map, "step_id"),
        "message": _required_text_from_mapping(step_map, "message"),
        "outputs": _json_ready(_as_mapping(step_map.get("outputs", {}))),
    }


def _required_text(payload: _WorkflowResult, field_name: str) -> str:
    """Return a required string value from a protocol payload."""

    value = getattr(payload, field_name, None)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    """Cast and validate mapping-like values."""

    if not isinstance(value, Mapping):
        raise ValueError("expected mapping payload")
    return value


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _trial_budget_warning_line(idea_metadata: Mapping[str, Any]) -> str | None:
    trial_budget = idea_metadata.get("trial_budget")
    if not isinstance(trial_budget, Mapping):
        return None
    budget = trial_budget.get("max_strategy_trials")
    if budget is None:
        return None
    try:
        budget_int = int(budget)
        trial_count = int(idea_metadata.get("trial_count", 0))
    except (TypeError, ValueError):
        return None
    if budget_int < 0 or trial_count <= budget_int:
        return None
    idea_id = str(idea_metadata.get("idea_id", "<unknown>"))
    return f"{idea_id} trial_count {trial_count} exceeds budget {budget_int}"


_ALLOWED_REVIEW_DECISIONS = frozenset(
    {
        "freeze_forward",
        "keep_researching",
        "paper_candidate",
        "reject",
        "retire",
        "small_live_candidate",
    }
)
_PROMOTION_READINESS_DECISIONS = frozenset({"paper_candidate", "small_live_candidate"})

__all__ = [
    "ResearchReviewDecision",
    "ResearchWorkflowReport",
    "ResearchWorkflowReportWriter",
]
