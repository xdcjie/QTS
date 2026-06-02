"""Quality gate: validation writers wrap verdict payloads only."""

from __future__ import annotations

import ast
from pathlib import Path


def test_validation_writer_is_wrapper_only_for_walk_forward_verdicts() -> None:
    path = Path("backend/src/qts/research/orchestrator/validation_artifact_writer.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    method = _method(tree, "ValidationArtifactWriter", "_walk_forward_validation_payload")

    source_names = {node.id for node in ast.walk(method) if isinstance(node, ast.Name)}
    dict_keys = {
        node.value
        for node in ast.walk(method)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }

    assert "WalkForwardValidationArtifact" in source_names
    assert source_names.isdisjoint({"accepted", "consistent", "gap", "allowed_gap"})
    assert dict_keys.isdisjoint({"accepted", "consistent"})


def _method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for child in node.body:
            if isinstance(child, ast.FunctionDef) and child.name == method_name:
                return child
    raise AssertionError(f"{class_name}.{method_name} not found")
