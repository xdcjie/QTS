"""Architecture gate for VWAP taxonomy presence (DR-030)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from qts.quality.rules import VwapTaxonomyPresenceRule

REPO_ROOT = Path(__file__).resolve().parents[3]


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)


def test_rule_flags_undocumented_vwap_artifact(tmp_path: Path) -> None:
    """An undocumented tracked VWAP artifact is reported."""
    taxonomy_dir = tmp_path / "docs" / "architecture"
    taxonomy_dir.mkdir(parents=True)
    (taxonomy_dir / "vwap_taxonomy.md").write_text(
        "# VWAP Artifact Taxonomy\n\nNo entries yet.\n", encoding="utf-8"
    )
    artifact = tmp_path / "strategies" / "vwap_orphan" / "card.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("orphan\n", encoding="utf-8")
    _git_init(tmp_path)

    violations = VwapTaxonomyPresenceRule().check_repository(tmp_path)

    assert [violation.path for violation in violations] == ["strategies/vwap_orphan/card.md"]
    assert violations[0].code == "VWAP_TAXONOMY_PRESENCE"


def test_rule_passes_when_artifact_documented(tmp_path: Path) -> None:
    """A documented tracked VWAP artifact yields no violation."""
    taxonomy_dir = tmp_path / "docs" / "architecture"
    taxonomy_dir.mkdir(parents=True)
    (taxonomy_dir / "vwap_taxonomy.md").write_text(
        "# VWAP Artifact Taxonomy\n\n"
        "| File | Description |\n"
        "| --- | --- |\n"
        "| `strategies/vwap_orphan/card.md` | Documented now |\n",
        encoding="utf-8",
    )
    artifact = tmp_path / "strategies" / "vwap_orphan" / "card.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("documented\n", encoding="utf-8")
    _git_init(tmp_path)

    assert VwapTaxonomyPresenceRule().check_repository(tmp_path) == []


def test_taxonomy_doc_itself_is_exempt(tmp_path: Path) -> None:
    """The taxonomy doc is the registry and is not treated as an undocumented artifact."""
    taxonomy_dir = tmp_path / "docs" / "architecture"
    taxonomy_dir.mkdir(parents=True)
    (taxonomy_dir / "vwap_taxonomy.md").write_text(
        "# VWAP Artifact Taxonomy\n\nNo artifact entries.\n", encoding="utf-8"
    )
    _git_init(tmp_path)

    assert VwapTaxonomyPresenceRule().check_repository(tmp_path) == []


@pytest.mark.skipif(
    not (REPO_ROOT / ".git").exists(),
    reason="real-repo assertion requires a git checkout",
)
def test_real_repository_has_no_undocumented_vwap_artifacts() -> None:
    """Every tracked VWAP artifact in this repository is classified in the taxonomy."""
    violations = VwapTaxonomyPresenceRule().check_repository(REPO_ROOT)

    assert violations == [], "\n".join(violation.format() for violation in violations)
