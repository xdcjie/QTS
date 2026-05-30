"""QTS-FINAL-013: config model modules do not parse files.

``qts.runtime.config.models`` and ``qts.data.historical.config`` validate
normalized payloads only; YAML parsing and file reads belong in their companion
loaders. This locks both the live modules and the ConfigLoaderBoundaryRule.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.rules import ConfigLoaderBoundaryRule

_GUARDED = (
    Path("backend/src/qts/runtime/config/models.py"),
    Path("backend/src/qts/data/historical/config.py"),
)


def _imports_and_reads(path: Path) -> tuple[set[str], int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    read_text_calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
        elif isinstance(node, ast.Attribute) and node.attr == "read_text":
            read_text_calls += 1
    return modules, read_text_calls


def test_config_model_modules_do_not_import_yaml_or_read_files() -> None:
    for path in _GUARDED:
        modules, read_text_calls = _imports_and_reads(path)
        assert "yaml" not in modules, f"{path} must not import yaml"
        assert read_text_calls == 0, f"{path} must not read files directly"


def test_config_loader_boundary_rule_flags_yaml_import() -> None:
    source = "import yaml\n\n\nclass C:\n    pass\n"
    tree = ast.parse(source)
    violations = ConfigLoaderBoundaryRule().check(
        relative_path=Path("backend/src/qts/runtime/config/models.py"),
        qts_relative_path=Path("runtime/config/models.py"),
        tree=tree,
    )
    assert any("must not import yaml" in v.message for v in violations)


def test_config_loader_boundary_rule_flags_read_text() -> None:
    source = "from pathlib import Path\n\n\ndef load(p: Path) -> str:\n    return p.read_text()\n"
    tree = ast.parse(source)
    violations = ConfigLoaderBoundaryRule().check(
        relative_path=Path("backend/src/qts/data/historical/config.py"),
        qts_relative_path=Path("data/historical/config.py"),
        tree=tree,
    )
    assert any("read_text" in v.message for v in violations)


def test_config_loader_boundary_rule_ignores_other_modules() -> None:
    source = "import yaml\n"
    tree = ast.parse(source)
    violations = ConfigLoaderBoundaryRule().check(
        relative_path=Path("backend/src/qts/runtime/config_loader.py"),
        qts_relative_path=Path("runtime/config_loader.py"),
        tree=tree,
    )
    assert violations == []
