from __future__ import annotations

from pathlib import Path

import pytest
from qts.research import (
    ResearchWorkflowReport,
    ResearchWorkflowReportWriter,
    ResearchWorkflowResult,
    ResearchWorkflowStepResult,
)


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


def test_workflow_report_writer_rejects_unsafe_output_path(tmp_path: Path) -> None:
    report = ResearchWorkflowReport(
        workflow_id="unsafe",
        workflow_status="completed",
        steps=(),
    )
    writer = ResearchWorkflowReportWriter(tmp_path)

    with pytest.raises(ValueError, match="output_path must be relative"):
        writer.write(report, output_path="/tmp/unsafe.md")
