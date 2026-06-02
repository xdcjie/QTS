from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_checked_in_research_quickstart_workflow_runs_with_manifest(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "quickstart" / "workflow_summary.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_research.py",
            "--config",
            "configs/research/quickstart.yaml",
            "workflow",
            "configs/research/workflows/quickstart.yaml",
            "--manifest",
            "configs/research/manifests/quickstart.yaml",
            "--output",
            str(output_path),
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
    payload = json.loads(result.stdout)
    assert payload["manifest_hash"].startswith("sha256:")
    assert payload["manifest_path"] == "configs/research/manifests/quickstart.yaml"
    assert payload["status"] == "completed"
    assert [step["id"] for step in payload["steps"]] == [
        "implementation",
        "backtest",
        "optimize",
        "report",
    ]
    assert output_path.exists()
    index_path = output_path.parent / "research_index.json"
    dashboard_path = output_path.parent / "research_dashboard.md"
    assert index_path.exists()
    assert dashboard_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["workflow_id"] == "quickstart-momentum-review"
    assert index["paper_live_launches"] == []
    assert index["workflow_summary"]["hash"].startswith("sha256:")
