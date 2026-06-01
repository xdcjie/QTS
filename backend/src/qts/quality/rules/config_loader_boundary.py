"""Config-loader boundary guardrail.

Config value-object modules validate normalized payloads; file-format parsing
belongs in loaders. The configured model modules must therefore not import a
YAML parser or read files directly (``Path.read_text``); those concerns live in
their companion ``*_loader`` modules.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation, _iter_imports

# Config model modules that must stay free of file-format parsing.
_GUARDED_MODULES: frozenset[tuple[str, ...]] = frozenset(
    {
        ("runtime", "config", "models.py"),
        ("data", "historical", "config.py"),
    }
)


class ConfigLoaderBoundaryRule:
    """Forbid YAML imports and file reads in configured config-model modules."""

    code = "CONFIG_LOADER_BOUNDARY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag yaml imports or read_text calls in config model modules."""
        if qts_relative_path.parts not in _GUARDED_MODULES:
            return []
        violations: list[GuardrailViolation] = []
        for imported_module, line in _iter_imports(tree):
            if imported_module == "yaml" or imported_module.startswith("yaml."):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=line,
                        message=(
                            "config model modules must not import yaml; parse files in the "
                            "companion config loader and pass a normalized payload"
                        ),
                    )
                )
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "read_text":
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=self._node_line(node),
                        message=(
                            "config model modules must not read files (read_text); file IO "
                            "belongs in the companion config loader"
                        ),
                    )
                )
        return violations

    @staticmethod
    def _node_line(node: ast.AST) -> int:
        try:
            return int(object.__getattribute__(node, "lineno"))
        except AttributeError:
            return 1


__all__ = ["ConfigLoaderBoundaryRule"]
