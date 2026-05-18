"""Integration tests for optimizer validation summary artifacts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


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


def test_optimizer_cli_applies_configured_validation_constraints(tmp_path: Path) -> None:
    config_path = tmp_path / "optimizer-validation.yaml"
    config_path.write_text(
        dedent(
            """
            strategy_module: examples.strategies.quickstart_optimizer
            strategy_factory: build_strategy
            bars_factory: build_bars
            initial_cash: "100000"
            objective_metric: total_return
            parameters:
              - name: entry_bar
                values: [1, 2]
              - name: target_quantity
                values: ["1", "2"]
            validation:
              constraints:
                - metric: total_return
                  operator: ">="
                  threshold: "999"
              walk_forward:
                splits:
                  - name: split-1
                    train_start: "2026-01-01"
                    train_end: "2026-01-15"
                    test_start: "2026-01-15"
                    test_end: "2026-01-31"
            """
        ).lstrip(),
        encoding="utf-8",
    )
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
            "PATH": os.environ.get("PATH", ""),
        },
    )

    assert result.returncode == 0, (
        f"CLI failed (returncode={result.returncode}):\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    payload = json.loads(validation_output.read_text(encoding="utf-8"))
    assert payload["run_count"] == 4
    assert payload["accepted_count"] == 0
    assert payload["rejected_count"] == 4
    assert payload["walk_forward_splits"] == [
        {
            "name": "split-1",
            "train_start": "2026-01-01",
            "train_end": "2026-01-15",
            "test_start": "2026-01-15",
            "test_end": "2026-01-31",
        }
    ]
    assert all(
        "total_return" in reason
        for rejection in payload["rejections"]
        for reason in rejection["reasons"]
    )
