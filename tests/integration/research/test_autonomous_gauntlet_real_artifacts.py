from __future__ import annotations

import json
from pathlib import Path

from tests.integration.research._autonomous_engine_plan_helpers import run_engine


def test_autonomous_gauntlet_consumes_validation_artifact_refs(tmp_path: Path) -> None:
    _campaign_path, result = run_engine(tmp_path)

    payload = json.loads(
        (result.output_root / "generation-000" / "validation_gauntlet.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["results"]
    for gauntlet_result in payload["results"]:
        for decision in gauntlet_result["gate_decisions"]:
            assert Path(decision["evidence"]["artifact_path"]).exists()
            assert str(decision["evidence"]["payload_hash"]).startswith("sha256:")
