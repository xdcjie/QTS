from __future__ import annotations

import json
from pathlib import Path

from qts.research.run_index import ResearchRunIndexWriter


def test_research_run_index_writer_links_workflow_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "workflow_summary.json"
    backtest_manifest = tmp_path / "backtests" / "single-run.manifest.json"
    optimizer_manifest = tmp_path / "optimizer" / "run-0001.manifest.json"
    validation_summary = tmp_path / "optimizer" / "validation-summary.json"
    report_path = tmp_path / "reports" / "workflow-report.md"
    for path in (backtest_manifest, optimizer_manifest, validation_summary, report_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    workflow_payload = {
        "manifest_hash": "sha256:manifest",
        "manifest_path": "configs/research/manifests/quickstart.yaml",
        "status": "completed",
        "steps": [
            {
                "id": "backtest",
                "kind": "backtest",
                "message": "done",
                "outputs": {"manifest_path": str(backtest_manifest)},
                "status": "passed",
            },
            {
                "id": "optimize",
                "kind": "optimize",
                "message": "done",
                "outputs": {
                    "ranked_results": [
                        {
                            "manifest_hash": "sha256:optimizer",
                            "manifest_path": str(optimizer_manifest),
                        }
                    ],
                    "validation_output": str(validation_summary),
                    "validation_summary": {"accepted_count": 1},
                },
                "status": "passed",
            },
            {
                "id": "report",
                "kind": "research_report",
                "message": "done",
                "outputs": {"report_path": str(report_path)},
                "status": "passed",
            },
        ],
        "workflow_id": "quickstart",
    }
    summary_path.write_text(json.dumps(workflow_payload, sort_keys=True), encoding="utf-8")

    result = ResearchRunIndexWriter().write(
        workflow_summary_path=summary_path,
        workflow_payload=workflow_payload,
    )

    index_path = Path(result["index_path"])
    dashboard_path = Path(result["dashboard_path"])
    assert index_path == tmp_path / "research_index.json"
    assert dashboard_path == tmp_path / "research_dashboard.md"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["workflow_id"] == "quickstart"
    assert index["workflow_summary"]["path"] == str(summary_path)
    assert index["workflow_summary"]["hash"].startswith("sha256:")
    assert index["research_manifest"] == {
        "hash": "sha256:manifest",
        "path": "configs/research/manifests/quickstart.yaml",
    }
    assert {artifact["kind"] for artifact in index["artifacts"]} >= {
        "backtest_manifest",
        "optimizer_manifest",
        "optimizer_validation_summary",
        "research_report",
    }
    dashboard = dashboard_path.read_text(encoding="utf-8")
    assert "workflow_summary.json" in dashboard
    assert "validation-summary.json" in dashboard
