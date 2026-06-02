from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_implementation_task_cli_scaffolds_non_executable_review_packet(
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "momentum-spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "candidate_tags": ["momentum"],
                "data_requirements": ["historical bars"],
                "expected_direction": "higher_score_higher_expected_return",
                "hypothesis": "Momentum should be tested out of sample.",
                "inputs": ["close"],
                "lookback": "20 bars",
                "name": "momentum_alpha",
                "notes": ["human review required"],
                "promotion_gate": "human_review_required",
                "rebalance": "daily",
                "review_status": "accepted",
                "source_refs": [
                    {
                        "external_id": "fixture:momentum",
                        "source": "fixture",
                        "title": "Momentum",
                        "url": "https://example.test/momentum",
                        "year": 2026,
                    }
                ],
                "universe": "research_session_universe",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "implementation-task"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_research.py",
            "implementation",
            "task",
            "--factor-spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
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
    assert payload["promotion_boundary"] == "research_task_only"
    assert payload["factor_spec_name"] == "momentum_alpha"
    for file_name in (
        "ai_prompt.md",
        "factor_template.py",
        "implementation_task.json",
        "strategy_template.py",
        "test_no_lookahead_template.py",
    ):
        assert (output_dir / file_name).exists(), file_name
    task_payload = json.loads((output_dir / "implementation_task.json").read_text())
    assert task_payload["review_status"] == "accepted"
    assert task_payload["runtime_promotion_allowed"] is False
    assert "No broker, runtime, order, or account imports" in (
        output_dir / "ai_prompt.md"
    ).read_text(encoding="utf-8")
