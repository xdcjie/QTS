"""Export a module-level import dependency graph snapshot."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


def _module_name_for_path(project_root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(project_root)
    parts = list(relative.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_relative_import(base_module: str, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    if node.module:
        module = "." * node.level + node.module
    else:
        module = "." * node.level
    return f"{module}"


def export_import_graph(source_root: Path, package_name: str = "qts") -> dict[str, list[str]]:
    source_root = source_root.resolve()
    modules: dict[Path, str] = {}
    for file_path in source_root.rglob("*.py"):
        if file_path.name == "__init__.py":
            continue
        module_name = _module_name_for_path(source_root, file_path)
        if module_name.startswith(package_name):
            modules[file_path] = module_name

    module_index = {name: path for path, name in modules.items()}
    edges: dict[str, set[str]] = {}

    for file_path, module_name in modules.items():
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        edges[module_name] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported = alias.name
                    if imported.startswith(package_name):
                        if imported in module_index:
                            edges[module_name].add(imported)
            elif isinstance(node, ast.ImportFrom):
                if node.module is None and node.level == 0:
                    continue
                imported = (
                    node.module
                    if node.level == 0
                    else _resolve_relative_import(module_name, node).lstrip(".")
                )
                if not imported or not imported.startswith(package_name):
                    if node.level == 0:
                        continue
                    package_parts = module_name.split(".")
                    if not package_parts:
                        continue
                    base_parts = (
                        package_parts[: -node.level] if node.level <= len(package_parts) else []
                    )
                    base_module = ".".join(base_parts)
                    imported = ".".join(
                        filter(None, [base_module, node.module] if node.module else [base_module])
                    )
                if imported.startswith(package_name) and imported in module_index:
                    edges[module_name].add(imported)

    return {src: sorted(targets) for src, targets in sorted(edges.items())}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export import dependency graph snapshot")
    parser.add_argument(
        "--source",
        default="backend/src",
        help="Source root containing Python packages.",
    )
    parser.add_argument(
        "--package",
        default="qts",
        help="Top package filter.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path for import graph.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_root = Path(args.source)
    graph = export_import_graph(source_root=source_root, package_name=args.package)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(graph, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
