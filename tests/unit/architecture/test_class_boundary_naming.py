"""Architecture checks for ambiguous backend class names."""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND_ROOT = Path("backend/src/qts")


def _class_locations(class_name: str) -> list[str]:
    locations: list[str] = []
    for path in sorted(BACKEND_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                locations.append(f"{path}:{node.lineno}")
    return locations


def test_known_ambiguous_backend_class_names_are_context_explicit() -> None:
    """Known duplicate backend class names stay renamed at their owning boundaries."""

    assert _class_locations("SessionLookup") == []
    assert _class_locations("PositionSnapshot") == []
    assert _class_locations("CashSnapshot") == []
    assert _class_locations("Fill") == ["backend/src/qts/strategy_sdk/events.py:107"]


def test_context_explicit_replacement_classes_exist_at_owning_boundaries() -> None:
    """The renamed classes remain available from their intended backend owners."""

    expected_locations = {
        "CalendarSessionLookup": [
            "backend/src/qts/data/sessions/calendar_lookup.py:11",
        ],
        "DashboardPositionSnapshot": [
            "backend/src/qts/observability/dashboard.py:50",
        ],
        "DashboardCashSnapshot": [
            "backend/src/qts/observability/dashboard.py:67",
        ],
        "ReconciliationPositionSnapshot": [
            "backend/src/qts/reconciliation/snapshots.py:31",
        ],
        "ReconciliationCashSnapshot": [
            "backend/src/qts/reconciliation/snapshots.py:39",
        ],
    }

    for class_name, locations in expected_locations.items():
        assert _class_locations(class_name) == locations
