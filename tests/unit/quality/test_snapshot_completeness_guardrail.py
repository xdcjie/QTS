"""QTS-FINAL-006 guardrail: snapshots must serialize every stateful private map.

``SnapshotCompletenessRule`` flags a snapshot/restore class whose ``__init__``
owns a private mutable collection that ``snapshot()`` neither serializes nor
declares ephemeral.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.rules import SnapshotCompletenessRule


def _check(source: str) -> list[str]:
    tree = ast.parse(source)
    violations = SnapshotCompletenessRule().check(
        relative_path=Path("backend/src/qts/execution/sample.py"),
        qts_relative_path=Path("execution/sample.py"),
        tree=tree,
    )
    return [v.message for v in violations]


def test_flags_private_map_missing_from_snapshot() -> None:
    source = (
        "class Widget:\n"
        "    def __init__(self) -> None:\n"
        "        self._seen: set[str] = set()\n"
        "        self._owned_by: dict[str, set[str]] = {}\n"
        "    def snapshot(self):\n"
        "        return (tuple(self._seen),)\n"
        "    @classmethod\n"
        "    def restore(cls, snap):\n"
        "        return cls()\n"
    )
    messages = _check(source)
    assert any("_owned_by" in message for message in messages)
    assert not any("_seen" in message for message in messages)


def test_passes_when_all_maps_are_serialized() -> None:
    source = (
        "class Widget:\n"
        "    def __init__(self) -> None:\n"
        "        self._seen: set[str] = set()\n"
        "        self._owned_by: dict[str, set[str]] = {}\n"
        "    def snapshot(self):\n"
        "        return (tuple(self._seen), tuple(self._owned_by.items()))\n"
        "    @classmethod\n"
        "    def restore(cls, snap):\n"
        "        return cls()\n"
    )
    assert _check(source) == []


def test_ignores_classes_without_snapshot_restore_pair() -> None:
    source = (
        "class Widget:\n"
        "    def __init__(self) -> None:\n"
        "        self._owned_by: dict[str, set[str]] = {}\n"
        "    def snapshot(self):\n"
        "        return ()\n"
    )
    # No restore() -> not a recovery-snapshot class -> not enforced.
    assert _check(source) == []


def test_production_order_manager_passes_the_rule() -> None:
    path = Path("backend/src/qts/execution/order_manager.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations = SnapshotCompletenessRule().check(
        relative_path=path,
        qts_relative_path=Path("execution/order_manager.py"),
        tree=tree,
    )
    assert violations == []
