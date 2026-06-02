"""Docs gate: subsystem deferrals require explicit owner-use decisions."""

from __future__ import annotations

import re
from pathlib import Path

_DEFERRALS = Path("docs/plan/wiring_deferrals.md")
_SUBSYSTEM_LINE = re.compile(r"^(?P<symbol>\S+)\s+expires=\d{4}-\d{2}-\d{2}\s+target=subsystem$")
_DECISION_ROW = re.compile(
    r"^\|\s*`(?P<symbol>[^`]+)`\s*\|\s*"
    r"(?P<decision>keep-owned|wire-entrypoint|move-experimental|delete)\s*\|\s*"
    r"(?P<owner>[^|]+?)\s*\|\s*(?P<evidence>[^|]+?)\s*\|"
)


def test_wiring_deferrals_have_deletion_decisions() -> None:
    text = _DEFERRALS.read_text(encoding="utf-8")
    subsystem_symbols = _subsystem_symbols(text)
    decisions = _decision_symbols(text)

    assert sorted(subsystem_symbols - set(decisions)) == []
    assert sorted(set(decisions) - subsystem_symbols) == []
    assert all(owner.strip() and evidence.strip() for owner, evidence in decisions.values())


def _subsystem_symbols(text: str) -> set[str]:
    symbols: set[str] = set()
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            continue
        match = _SUBSYSTEM_LINE.match(stripped)
        if match is not None:
            symbols.add(match.group("symbol"))
    return symbols


def _decision_symbols(text: str) -> dict[str, tuple[str, str]]:
    decisions: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        match = _DECISION_ROW.match(line.strip())
        if match is not None:
            decisions[match.group("symbol")] = (
                match.group("owner").strip(),
                match.group("evidence").strip(),
            )
    return decisions
