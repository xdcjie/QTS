from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qts.research.clock import DeterministicResearchClock


def test_deterministic_research_clock_returns_offset_timestamps() -> None:
    clock = DeterministicResearchClock(datetime(2026, 6, 1, 9, 30, tzinfo=UTC))

    assert clock.now(offset_seconds=15) == datetime(2026, 6, 1, 9, 30, 15, tzinfo=UTC)


def test_research_runtime_code_does_not_hardcode_fixed_audit_clock() -> None:
    research_root = Path("backend/src/qts/research")
    offenders: list[str] = []
    for path in sorted(research_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        if "datetime(2026, 5, 26" in source:
            offenders.append(str(path))

    assert offenders == []
