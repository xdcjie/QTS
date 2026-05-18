"""Integration tests for optimizer validation summary artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_optimizer_cli_writes_validation_summary_artifact(tmp_path: Path) -> None:
    config_path = Path("configs/optimizer/quickstart.yaml")
    validation_output = tmp_path / "validation-summary.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_optimizer.py",
            str(config_path),
            "--output-root",
            str(tmp_path / "optimizer-runs"),
            "--validation-output",
            str(validation_output),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={
            "PYTHONPATH": "backend/src",
            "QTS_API_DEV_TOKENS": "1",
            "PATH": __import__("os").environ.get("PATH", ""),
        },
    )

    assert result.returncode == 0, (
        f"CLI failed (returncode={result.returncode}):\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    payload = json.loads(validation_output.read_text(encoding="utf-8"))
    assert payload["run_count"] == 4
    assert payload["accepted_count"] == 4
    assert payload["rejected_count"] == 0
    assert payload["rejections"] == []
    assert validation_output.read_text(encoding="utf-8").endswith("\n")
