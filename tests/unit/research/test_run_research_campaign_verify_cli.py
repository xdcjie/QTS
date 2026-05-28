from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_research


def test_campaign_verify_rejects_missing_release_bundle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_root = tmp_path / "missing-campaign"

    exit_code = run_research.main(["campaign", "verify", "--output-root", str(output_root)])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is False
    assert payload["criteria"]["validation_summary"]["accepted"] is False
    assert payload["criteria"]["artifact_graph"]["accepted"] is False
    assert (output_root / "release_verification.json").exists()
