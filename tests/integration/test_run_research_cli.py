"""Integration tests for the research workflow CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from qts.research import ExperimentStore
from qts.research.factor_evaluation import (
    FactorEvaluationArtifactWriter,
    FactorEvaluationMetrics,
    FactorEvaluationResult,
)

from tests.integration.test_research_session_facade import _write_research_session_config


def _write_evaluation(
    writer: FactorEvaluationArtifactWriter,
    as_of: date,
    *,
    rank_ic: str,
    spread: str,
    coverage: str,
) -> Path:
    return writer.write(
        FactorEvaluationResult(
            as_of=as_of,
            factor_name="momentum",
            factor_version="1",
            metrics=FactorEvaluationMetrics(
                rank_ic=Decimal(rank_ic),
                long_short_spread=Decimal(spread),
                coverage=Decimal(coverage),
                turnover=None,
                scored_count=3,
                return_count=3,
                missing_symbols=(),
            ),
        )
    )


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/run_research.py", *args],
        capture_output=True,
        text=True,
        check=False,
        env={
            "PYTHONPATH": "backend/src",
            "QTS_API_DEV_TOKENS": "1",
            "PATH": os.environ.get("PATH", ""),
        },
    )


def test_research_cli_records_factor_tearsheet_and_lists_runs(tmp_path: Path) -> None:
    config_path = _write_research_session_config(tmp_path)
    writer = FactorEvaluationArtifactWriter(tmp_path / "factor-evaluations")
    first = _write_evaluation(
        writer,
        date(2026, 1, 2),
        rank_ic="0.1",
        spread="0.01",
        coverage="0.8",
    )
    second = _write_evaluation(
        writer,
        date(2026, 1, 3),
        rank_ic="0.3",
        spread="0.03",
        coverage="0.9",
    )

    result = _run_cli(
        "--config",
        str(config_path),
        "factor-tearsheet",
        str(second),
        str(first),
        "--experiment-id",
        "momentum-tearsheet",
        "--dataset-id",
        "fixture-bars",
    )

    assert result.returncode == 0, result.stderr
    assert "tearsheet_path=" in result.stdout
    assert "manifest_path=" in result.stdout
    assert "store_index=" in result.stdout
    output_lines = dict(line.split("=", maxsplit=1) for line in result.stdout.splitlines())
    manifest_payload = json.loads(Path(output_lines["manifest_path"]).read_text(encoding="utf-8"))
    manifest_artifact_path = next(iter(manifest_payload["artifact_paths_by_hash"].values()))
    assert output_lines["tearsheet_path"] == manifest_artifact_path
    store = ExperimentStore(tmp_path / "research-store")
    records = store.list_runs()
    assert [record.experiment_id for record in records] == ["momentum-tearsheet"]
    assert records[0].metrics["mean_rank_ic"] == "0.2"

    runs = _run_cli("--config", str(config_path), "runs", "--sort-by", "mean_rank_ic")

    assert runs.returncode == 0, runs.stderr
    assert "experiment_id" in runs.stdout
    assert "momentum-tearsheet" in runs.stdout
    assert "0.2" in runs.stdout


def test_research_cli_runs_command_lists_unsorted_store_records(tmp_path: Path) -> None:
    config_path = _write_research_session_config(tmp_path)
    store = ExperimentStore(tmp_path / "research-store")
    writer = FactorEvaluationArtifactWriter(tmp_path / "factor-evaluations")
    artifact = _write_evaluation(
        writer,
        date(2026, 1, 2),
        rank_ic="0.1",
        spread="0.01",
        coverage="0.8",
    )
    result = _run_cli(
        "--config",
        str(config_path),
        "factor-tearsheet",
        str(artifact),
        "--experiment-id",
        "single-snapshot",
    )
    assert result.returncode == 0, result.stderr
    assert store.list_runs()[0].experiment_id == "single-snapshot"

    listed = _run_cli("--config", str(config_path), "runs")

    assert listed.returncode == 0, listed.stderr
    assert "single-snapshot" in listed.stdout
