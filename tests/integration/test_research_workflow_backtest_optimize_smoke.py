from __future__ import annotations

import json
from pathlib import Path

from tests.integration.test_research_session_facade import _write_research_session_config
from tests.integration.test_run_research_cli import _run_cli, _write_workflow


def test_research_workflow_backtest_optimize_smoke_writes_index_and_manifest_evidence(
    tmp_path: Path,
) -> None:
    config_path = _write_research_session_config(tmp_path)
    output_path = tmp_path / "workflow-output" / "workflow_summary.json"
    workflow_path = _write_workflow(
        tmp_path,
        f"""
version: 1
workflow_id: backtest-optimize-smoke
steps:
  - id: implementation
    kind: implementation_gate
    required_modules:
      - examples.strategies.gc_si_momentum
    required_strategy: examples.strategies.gc_si_momentum:GcSiMomentumStrategy
  - id: backtest
    kind: backtest
    strategy_params:
      quantity: "2"
      entry_bar: 1
  - id: optimize
    kind: optimize
    objective_metric: total_return
    validation_output: {tmp_path / "workflow-output" / "validation-summary.json"}
    parameters:
      entry_bar: [1, 2]
      quantity: ["1", "2"]
  - id: report
    kind: research_report
    output_root: {tmp_path / "workflow-output" / "reports"}
""",
    )

    result = _run_cli(
        "--config",
        str(config_path),
        "workflow",
        str(workflow_path),
        "--manifest",
        "configs/research/manifests/gc_si_smoke_v2.yaml",
        "--output",
        str(output_path),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "completed"
    assert [step["id"] for step in payload["steps"]] == [
        "implementation",
        "backtest",
        "optimize",
        "report",
    ]
    backtest_manifest = Path(payload["steps"][1]["outputs"]["manifest_path"])
    optimize_outputs = payload["steps"][2]["outputs"]
    optimizer_manifest = Path(optimize_outputs["ranked_results"][0]["manifest_path"])
    validation_summary = Path(optimize_outputs["validation_output"])
    for path in (backtest_manifest, optimizer_manifest, validation_summary):
        assert path.exists(), path
    manifest_payload = json.loads(backtest_manifest.read_text(encoding="utf-8"))
    assert manifest_payload["artifact_schema_version"] == "1"
    assert isinstance(manifest_payload["manifest_hash"], str)
    artifacts = manifest_payload["artifacts"]
    assert isinstance(artifacts, dict)
    assert artifacts
    assert all("sha256" in artifact for artifact in artifacts.values())
    index_path = output_path.parent / "research_index.json"
    dashboard_path = output_path.parent / "research_dashboard.md"
    assert index_path.exists()
    assert dashboard_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["workflow_summary"]["path"] == str(output_path)
    assert {artifact["kind"] for artifact in index["artifacts"]} >= {
        "backtest_manifest",
        "optimizer_manifest",
        "optimizer_validation_summary",
        "research_report",
    }
