"""Replay coverage for canonical research workflow determinism."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

from tests.integration.test_research_session_facade import _write_research_session_config


def test_identical_canonical_research_workflows_match_ranked_results_and_metrics(
    tmp_path: Path,
) -> None:
    left = _run_canonical_optimize_workflow(tmp_path / "left")
    right = _run_canonical_optimize_workflow(tmp_path / "right")

    assert _normalized_optimizer_outputs(left) == _normalized_optimizer_outputs(right)


def _run_canonical_optimize_workflow(root: Path) -> dict[str, Any]:
    root.mkdir()
    config_path = _write_research_session_config(root)
    workflow_path = root / "workflow.yaml"
    workflow_path.write_text(
        f"""
version: 1
workflow_id: deterministic-research
steps:
  - id: optimize
    kind: optimize
    objective_metric: total_return
    output_root: {root / "workflow-optimizer"}
    capital_metrics:
      margin_proxy: "1000"
    parameters:
      entry_bar: [1, 2]
      quantity: ["1", "2"]
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_research.py",
            "--config",
            str(config_path),
            "workflow",
            str(workflow_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={
            "PYTHONPATH": f"backend/src{os.pathsep}.",
            "QTS_API_DEV_TOKENS": "1",
            "PATH": os.environ.get("PATH", ""),
        },
    )

    assert result.returncode == 0, result.stderr
    return cast(dict[str, Any], json.loads(result.stdout))


def _normalized_optimizer_outputs(payload: dict[str, Any]) -> dict[str, Any]:
    assert payload["status"] == "completed"
    assert payload["workflow_id"] == "deterministic-research"
    assert len(payload["steps"]) == 1
    step = payload["steps"][0]
    assert step["id"] == "optimize"
    assert step["kind"] == "optimize"
    assert step["status"] == "passed"
    outputs = step["outputs"]
    return {
        "ranked_results": [
            _normalized_optimizer_evidence(item) for item in outputs["ranked_results"]
        ],
        "run_count": outputs["run_count"],
        "validation_summary": _normalized_validation_summary(outputs["validation_summary"]),
    }


def _normalized_validation_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "accepted_count": summary["accepted_count"],
        "accepted_runs": [
            _normalized_optimizer_evidence(item) for item in summary["accepted_runs"]
        ],
        "rejected_count": summary["rejected_count"],
        "rejections": [
            {
                **_normalized_optimizer_evidence(item),
                "reasons": list(item.get("reasons", ())),
            }
            for item in summary["rejections"]
        ],
        "run_count": summary["run_count"],
        "walk_forward_splits": summary["walk_forward_splits"],
    }


def _normalized_optimizer_evidence(item: dict[str, Any]) -> dict[str, Any]:
    manifest_path = Path(item["manifest_path"])
    normalized = {
        key: _normalized_json_value(value)
        for key, value in item.items()
        if key not in {"manifest_hash", "manifest_path", "reasons"}
    }
    normalized["manifest_metrics"] = _normalized_manifest_metrics(manifest_path)
    return normalized


def _normalized_manifest_metrics(manifest_path: Path) -> dict[str, Any]:
    payload = cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))
    return {
        str(key): _normalized_json_value(value) for key, value in sorted(payload["metrics"].items())
    }


def _normalized_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalized_json_value(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_normalized_json_value(item) for item in value]
    return value
