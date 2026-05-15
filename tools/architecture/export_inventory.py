"""Export a stable class inventory snapshot for the project.

The snapshot is intentionally simple: one entry per class with enough metadata to:

- detect class additions/removals across refactors,
- spot stale documentation/class-index mismatches,
- inspect canonical docstrings and method surface size.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


def _class_module_name(project_root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(project_root)
    return relative.with_suffix("").as_posix().replace("/", ".")


def _module_direct_imports(tree: ast.Module) -> list[str]:
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None and node.level == 0:
                continue
            if node.level == 0:
                imports.add(node.module)
                continue
            # Relative imports are intentionally skipped here; they are expanded in
            # export_import_graph.py where module resolution is needed.
            imports.add(".".join(["." for _ in range(node.level)]))
    return sorted(imports)


def export_inventory(source_root: Path) -> list[dict[str, Any]]:
    source_root = source_root.resolve()
    entries: list[dict[str, Any]] = []

    for py_file in sorted(source_root.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        text = py_file.read_text(encoding="utf-8")
        tree = ast.parse(text)
        module_name = _class_module_name(source_root, py_file)
        imports = _module_direct_imports(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            first_line = ""
            if ast.get_docstring(node):
                first_line = ast.get_docstring(node).splitlines()[0]
            entries.append(
                {
                    "name": node.name,
                    "module": module_name,
                    "file": py_file.as_posix(),
                    "lineno": node.lineno,
                    "public": not node.name.startswith("_"),
                    "docstring_first_line": first_line,
                    "direct_imports": imports,
                    "method_count": sum(
                        isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                        for member in node.body
                    ),
                }
            )

    entries.sort(key=lambda item: (item["module"], item["name"], item["lineno"]))
    return entries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export class inventory snapshot")
    parser.add_argument(
        "--source",
        default="backend/src",
        help="Source root containing Python packages.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path for class inventory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_root = Path(args.source)
    output_path = Path(args.output)
    payload = export_inventory(source_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
