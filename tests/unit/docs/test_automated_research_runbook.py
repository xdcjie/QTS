from __future__ import annotations

import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]


def test_automated_research_runbook_uses_canonical_manifest_workflow_command() -> None:
    runbook = Path("docs/research/automated_research_runbook.md")
    text = runbook.read_text(encoding="utf-8")

    canonical_command = (
        "PYTHONPATH=backend/src uv run python scripts/run_research.py "
        "--config configs/research/quickstart.yaml "
        "workflow configs/research/workflows/quickstart.yaml "
        "--manifest configs/research/manifests/quickstart.yaml"
    )
    assert canonical_command in " ".join(text.split())
    for command in re.findall(
        r"PYTHONPATH=backend/src uv run python scripts/run_research.py[^`\\n]+", text
    ):
        if " workflow " in command:
            assert " --manifest " in f" {command} "


def test_research_automation_checked_in_bundle_and_templates_exist() -> None:
    required_paths = (
        Path("configs/research/manifests/quickstart.yaml"),
        Path("configs/research/workflows/factor_only_template.yaml"),
        Path("configs/research/workflows/strategy_parameter_template.yaml"),
        Path("configs/research/campaigns/quickstart_fixture.yaml"),
        Path("docs/research/automated_research_runbook.md"),
        Path("docs/research/factor_to_strategy_implementation.md"),
        Path("docs/research/autonomous_campaign_runbook.md"),
        Path("docs/research/templates/factor_template.py"),
        Path("docs/research/templates/strategy_template.py"),
        Path("docs/research/templates/test_no_lookahead_template.py"),
    )
    missing = [str(path) for path in required_paths if not path.exists()]
    assert missing == []

    manifest = yaml.safe_load(Path("configs/research/manifests/quickstart.yaml").read_text())
    assert manifest["schema_version"] == 2
    assert manifest["run"]["id"] == "quickstart"
    campaign = yaml.safe_load(
        Path("configs/research/campaigns/quickstart_fixture.yaml").read_text()
    )
    assert campaign["launch_controls"]["paper_live_launches"] == "disabled"
    assert campaign["execution"]["data_mode"] == "fixture"
