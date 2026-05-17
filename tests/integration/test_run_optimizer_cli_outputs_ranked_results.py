"""Anchor: scripts/run_optimizer.py prints ranked parameter-sweep results.

Domain fact: the optimizer is a library API; until a script driver exists,
the OPT-19 classes remain deferred and the CallerPresenceRule rejects
removing them from wiring_deferrals.md. OPT-65 ships the CLI that
satisfies the caller gate.

Owner: ``scripts/run_optimizer.py`` (entrypoint) +
``examples/strategies/quickstart_optimizer.py`` (parameterizable strategy).

Forbidden shortcut: embedding strategy code in the CLI; bypassing
``BacktestEngine``; printing JSON instead of a human-readable ranked
table.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_runs_quickstart_config_and_prints_ranked_table(tmp_path: Path) -> None:
    config_path = Path("configs/optimizer/quickstart.yaml")
    assert config_path.exists(), f"quickstart config missing at {config_path}"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_optimizer.py",
            str(config_path),
            "--output-root",
            str(tmp_path / "optimizer-runs"),
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
    output = result.stdout
    assert "rank" in output.lower()
    # The quickstart config has 2 parameters × 2 values each = 4 combinations.
    rank_lines = [line for line in output.splitlines() if line.strip().startswith("1")]
    assert rank_lines, f"expected ranked results, got:\n{output}"
