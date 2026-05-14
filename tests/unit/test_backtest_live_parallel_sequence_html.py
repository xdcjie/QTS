from __future__ import annotations

import ast
import re
from pathlib import Path


def _production_classes() -> dict[str, set[str]]:
    classes: dict[str, set[str]] = {}
    for path in sorted(Path("backend/src/qts").rglob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.setdefault(node.name, set()).add(path.as_posix())
    return classes


def test_backtest_live_parallel_sequence_documents_all_production_classes() -> None:
    html = Path("docs/architecture/backtest_live_parallel_sequence.html").read_text(
        encoding="utf-8"
    )
    missing: list[str] = []
    for path in sorted(Path("backend/src/qts").rglob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                location = f"{path.as_posix()}:{node.lineno}"
                if node.name not in html or location not in html:
                    missing.append(f"{path}:{node.lineno}:{node.name}")

    assert not missing


def test_backtest_live_parallel_sequence_references_only_implemented_classes() -> None:
    html = Path("docs/architecture/backtest_live_parallel_sequence.html").read_text(
        encoding="utf-8"
    )
    class_names = set(_production_classes())
    implementation_text = html.split('aria-label="生产类全量索引"', maxsplit=1)[0]

    missing = sorted(
        {
            token
            for token in re.findall(r"<code>([A-Z][A-Za-z0-9_]+)</code>", implementation_text)
            if token not in class_names
        }
    )

    assert missing == []


def test_backtest_live_parallel_sequence_current_implementation_list_maps_classes_to_files() -> (
    None
):
    html = Path("docs/architecture/backtest_live_parallel_sequence.html").read_text(
        encoding="utf-8"
    )
    classes = _production_classes()
    match = re.search(
        r'aria-label="当前实现清单".*?<ul>(.*?)</ul>',
        html,
        flags=re.DOTALL,
    )
    assert match is not None

    wrong_locations: list[str] = []
    for path, class_fragment in re.findall(
        r"<li><code>(qts/[^<]+\.py)</code> -> (.*?)</li>",
        match.group(1),
        flags=re.DOTALL,
    ):
        source_path = f"backend/src/{path}"
        for class_name in re.findall(r"<code>([A-Z][A-Za-z0-9_]+)</code>", class_fragment):
            if source_path not in classes.get(class_name, set()):
                wrong_locations.append(f"{class_name} listed under {source_path}")

    assert wrong_locations == []
