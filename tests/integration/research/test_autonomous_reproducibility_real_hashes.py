from __future__ import annotations

import json
from pathlib import Path

from tests.integration.research._autonomous_engine_plan_helpers import run_engine


def test_autonomous_reproducibility_uses_real_repo_and_data_hashes(tmp_path: Path) -> None:
    _campaign_path, result = run_engine(tmp_path)
    trial = result.generations[0].experiment_result.trials[0]
    payload = json.loads(trial.reproducibility_path.read_text(encoding="utf-8"))

    assert payload["git_sha"] not in {"unknown", "research-git-sha"}
    assert payload["platform"] != "research-platform"
    assert payload["python_version"]
    assert "pyproject.toml" in payload["dependency_hashes"]
    assert all(str(value).startswith("sha256:") for value in payload["dependency_hashes"].values())
    assert all(str(value).startswith("sha256:") for value in payload["data_hashes"].values())
