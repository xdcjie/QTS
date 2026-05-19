from __future__ import annotations

from pathlib import Path


def test_top_level_local_yaml_configs_are_gitignored() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "configs/*.local.yaml" in gitignore
