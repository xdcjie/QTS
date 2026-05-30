"""Snapshot-completeness guardrail.

Recovery snapshots must preserve every private mutable collection that drives
public state or compaction. A class that exposes both a ``snapshot`` method and
a ``restore`` constructor must reference each such collection in ``snapshot``
(so it round-trips) or declare it ephemeral with a documented reason.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

# Per-class allowlist of private collection attributes that are intentionally
# reconstructed on restore rather than serialized. Each entry documents why the
# attribute does not need to appear in the snapshot.
_EPHEMERAL_ATTRS: dict[str, frozenset[str]] = {
    # OrderManager rebuilds the per-order state machines from each restored
    # order's persisted ``state`` field, so the machines map is derived, not
    # serialized.
    "OrderManager": frozenset({"_machines"}),
    # BrokerOrderMap serializes only the canonical record store
    # (``_by_client_order_id``); the other maps are secondary indexes
    # (ibkr/perm/internal order id -> client order id) rebuilt from the records
    # on restore, so they are derived, not serialized.
    "BrokerOrderMap": frozenset(
        {
            "_client_by_ibkr_order_id",
            "_client_by_perm_id",
            "_client_by_internal_order_id",
        }
    ),
}

_COLLECTION_ANNOTATION_BASES = frozenset(
    {"dict", "set", "Mapping", "MutableMapping", "MutableSet", "defaultdict"}
)
_COLLECTION_CALL_SUFFIXES = ("Store", "Book")


class SnapshotCompletenessRule:
    """Require snapshot/restore classes to serialize every stateful map."""

    code = "SNAPSHOT_COMPLETENESS"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag private collections missing from a class's snapshot."""
        if qts_relative_path.parts[:1] == ("quality",):
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods = {
                item.name: item
                for item in node.body
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
            }
            if "snapshot" not in methods or "restore" not in methods:
                continue
            init = methods.get("__init__")
            if init is None:
                continue
            collections = self._collection_attrs(init)
            referenced = self._attrs_referenced(methods["snapshot"])
            ephemeral = _EPHEMERAL_ATTRS.get(node.name, frozenset())
            for attr in sorted(collections - referenced - ephemeral):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=node.lineno,
                        message=(
                            f"{node.name}.{attr} is a private mutable collection that is not "
                            "represented in snapshot(); serialize it or document it as ephemeral "
                            "in the snapshot guardrail allowlist"
                        ),
                    )
                )
        return violations

    @classmethod
    def _collection_attrs(cls, init: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
        attrs: set[str] = set()
        for node in ast.walk(init):
            if isinstance(node, ast.AnnAssign):
                ann_target = node.target
                if (
                    isinstance(ann_target, ast.Attribute)
                    and isinstance(ann_target.value, ast.Name)
                    and ann_target.value.id == "self"
                    and ann_target.attr.startswith("_")
                    and cls._is_collection_annotation(node.annotation)
                ):
                    attrs.add(ann_target.attr)
            elif isinstance(node, ast.Assign) and cls._is_collection_value(node.value):
                for assign_target in node.targets:
                    if (
                        isinstance(assign_target, ast.Attribute)
                        and isinstance(assign_target.value, ast.Name)
                        and assign_target.value.id == "self"
                        and assign_target.attr.startswith("_")
                    ):
                        attrs.add(assign_target.attr)
        return attrs

    @staticmethod
    def _attrs_referenced(method: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
        referenced: set[str] = set()
        for node in ast.walk(method):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
            ):
                referenced.add(node.attr)
        return referenced

    @classmethod
    def _is_collection_annotation(cls, annotation: ast.expr) -> bool:
        if isinstance(annotation, ast.Subscript):
            return cls._is_collection_annotation(annotation.value)
        if isinstance(annotation, ast.Name):
            return annotation.id in _COLLECTION_ANNOTATION_BASES
        if isinstance(annotation, ast.Attribute):
            return annotation.attr in _COLLECTION_ANNOTATION_BASES
        return False

    @staticmethod
    def _is_collection_value(value: ast.expr) -> bool:
        if isinstance(value, ast.Dict | ast.Set):
            return True
        if isinstance(value, ast.Call):
            func = value.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name in {"dict", "set", "defaultdict"}:
                return True
            return name.endswith(_COLLECTION_CALL_SUFFIXES)
        return False


__all__ = ["SnapshotCompletenessRule"]
