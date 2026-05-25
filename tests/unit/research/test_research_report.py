from __future__ import annotations

from pathlib import Path

import pytest
from qts.research import (
    ResearchWorkflowReport,
    ResearchWorkflowReportWriter,
    ResearchWorkflowResult,
    ResearchWorkflowStepResult,
)
from qts.research.report import ResearchReviewDecision
from qts.research.workflow import ResearchWorkflowRunContext


def _result_step(
    kind: str,
    status: str,
    outputs: dict[str, object] | None = None,
) -> ResearchWorkflowStepResult:
    return ResearchWorkflowStepResult(
        step_id=kind,
        kind=kind,
        status=status,
        message=f"{kind} done",
        outputs=outputs or {},
    )


def test_workflow_report_renders_stable_markdown(tmp_path: Path) -> None:
    report = ResearchWorkflowReport.from_result(
        ResearchWorkflowResult(
            workflow_id="momentum-flow",
            status="completed",
            steps=(
                _result_step(
                    "factor_candidates",
                    "passed",
                    {"candidate_count": 2},
                ),
                _result_step(
                    "factor_evaluation",
                    "passed",
                    {
                        "factor_name": "momentum",
                        "factor_version": "1",
                        "snapshot_count": 2,
                    },
                ),
            ),
        )
    )
    body = report.to_markdown()

    assert "# Research Workflow Report" in body
    assert "workflow_id: momentum-flow" in body
    assert "workflow_status: completed" in body
    assert "Step Results" in body
    assert "factor_candidates" in body
    assert "factor_evaluation" in body
    assert "Non-Promotion Boundary" in body

    assert (
        body
        == ResearchWorkflowReport.from_result(
            ResearchWorkflowResult(
                workflow_id="momentum-flow",
                status="completed",
                steps=(
                    _result_step(
                        "factor_candidates",
                        "passed",
                        {"candidate_count": 2},
                    ),
                    _result_step(
                        "factor_evaluation",
                        "passed",
                        {
                            "factor_name": "momentum",
                            "factor_version": "1",
                            "snapshot_count": 2,
                        },
                    ),
                ),
            )
        ).to_markdown()
    )


def test_workflow_report_renders_optimizer_capital_metrics() -> None:
    report = ResearchWorkflowReport.from_result(
        ResearchWorkflowResult(
            workflow_id="vwap-flow",
            status="completed",
            steps=(
                _result_step(
                    "optimize",
                    "passed",
                    {
                        "ranked_results": [
                            {
                                "capital_metrics": {
                                    "pnl_usd": "160.00",
                                    "return_on_margin_proxy": "0.0133333333",
                                },
                                "manifest_path": "runs/vwap/top.manifest.json",
                                "objective_value": "1.7",
                            }
                        ],
                        "run_count": 3,
                        "validation_summary": {
                            "accepted_count": 2,
                            "rejected_count": 1,
                        },
                    },
                ),
            ),
        )
    )

    body = report.to_markdown()

    assert "accepted_count: 2" in body
    assert "rejected_count: 1" in body
    assert "top_pnl_usd: 160.00" in body
    assert "top_return_on_margin_proxy: 0.0133333333" in body


def test_research_report_contains_evidence_header() -> None:
    run_context = ResearchWorkflowRunContext(
        workflow_config_path="configs/research/workflows/quickstart.yaml",
        workflow_config_hash="sha256:workflow",
        research_config_path="configs/research/quickstart.yaml",
        research_config_hash="sha256:research",
        git_branch="master",
        git_commit="abc123",
        git_dirty=False,
        dataset_ids=("fixture:GC:15m",),
        backtest_config_hash="sha256:backtest",
        generated_at="2026-05-25T00:00:00+00:00",
    )
    report = ResearchWorkflowReport.from_result(
        ResearchWorkflowResult(
            workflow_id="quickstart-flow",
            status="completed",
            steps=(),
            run_context=run_context,
        )
    )

    body = report.to_markdown()

    assert "## Evidence Header" in body
    assert "- Workflow config: configs/research/workflows/quickstart.yaml" in body
    assert "- Workflow config hash: sha256:workflow" in body
    assert "- Research config: configs/research/quickstart.yaml" in body
    assert "- Git branch: master" in body
    assert "- Dirty workspace: False" in body
    assert "- Promotion status: research_only" in body


def test_report_decision_status_enum() -> None:
    with pytest.raises(ValueError, match="unsupported review decision status"):
        ResearchReviewDecision(status="looks_good")


def test_report_decision_requires_evidence_bundle_for_paper_candidate() -> None:
    with pytest.raises(ValueError, match="paper_candidate requires evidence_bundle_id"):
        ResearchReviewDecision(status="paper_candidate")


def test_report_decision_blocks_paper_without_required_evidence() -> None:
    with pytest.raises(ValueError, match="paper_candidate requires trade diagnostics"):
        ResearchReviewDecision(
            status="paper_candidate",
            evidence_bundle_id="evb_fixture",
            validation_scorecard_available=True,
            cost_stress_available=True,
        )


def test_report_renders_machine_readable_decision_block() -> None:
    report = ResearchWorkflowReport.from_result(
        ResearchWorkflowResult(
            workflow_id="decision-flow",
            status="completed",
            steps=(),
            decision=ResearchReviewDecision(
                status="keep_researching",
                reason=("Need cost stress evidence.",),
                required_next_evidence=("cost_stress_2x_3x",),
            ),
        )
    )

    body = report.to_markdown()

    assert "## Review Decision" in body
    assert "status: keep_researching" in body
    assert "required_next_evidence:" in body
    assert "- cost_stress_2x_3x" in body


def test_research_report_prints_period_roles() -> None:
    report = ResearchWorkflowReport.from_result(
        ResearchWorkflowResult(
            workflow_id="period-role-flow",
            status="completed",
            steps=(
                _result_step(
                    "backtest_matrix",
                    "passed",
                    {
                        "periods": [
                            {
                                "end": "2022-01-01T00:00:00+00:00",
                                "name": "selection_2020_2022",
                                "role": "selection",
                                "start": "2020-01-01T00:00:00+00:00",
                            },
                            {
                                "end": "2026-01-01T00:00:00+00:00",
                                "name": "holdout_2024_2026",
                                "role": "holdout_report_only",
                                "start": "2024-01-01T00:00:00+00:00",
                            },
                        ],
                        "report_only_periods": ["holdout_2024_2026"],
                        "selection_basis": ["selection_2020_2022"],
                    },
                ),
            ),
        )
    )

    body = report.to_markdown()

    selection_row = (
        "| selection_2020_2022 | 2020-01-01T00:00:00+00:00 | "
        "2022-01-01T00:00:00+00:00 | selection | selection_basis |"
    )
    holdout_row = (
        "| holdout_2024_2026 | 2024-01-01T00:00:00+00:00 | "
        "2026-01-01T00:00:00+00:00 | holdout_report_only | report_only |"
    )
    assert "## Period Roles" in body
    assert selection_row in body
    assert holdout_row in body


def test_workflow_report_writer_rejects_unsafe_output_path(tmp_path: Path) -> None:
    report = ResearchWorkflowReport(
        workflow_id="unsafe",
        workflow_status="completed",
        steps=(),
    )
    writer = ResearchWorkflowReportWriter(tmp_path)

    with pytest.raises(ValueError, match="output_path must be relative"):
        writer.write(report, output_path="/tmp/unsafe.md")
