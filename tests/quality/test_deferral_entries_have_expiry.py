"""Anchor: every wiring deferral has expires_on + target category; no past dates.

Domain fact: a deferral without an expiry becomes a permanent exemption.
Every entry must carry a clock. ``target=production`` is forbidden by
``CallerPresenceRule`` and final-readiness.

Owner: ``docs/plan/wiring_deferrals.md`` (data) +
``qts.quality.rules.caller_presence`` (loader/enforcement).

Forbidden shortcut: ``expires=never`` literals; bulk-set all entries to
the same date (OPT-18 avalanche risk).
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

_DEFERRALS_PATH = Path("docs/plan/wiring_deferrals.md")
_MAX_HORIZON = timedelta(days=365)
_WIRING_FOLLOWUP_HORIZON = timedelta(days=92)
_LINE_PATTERN = re.compile(
    r"^(?P<symbol>\S+)\s+expires=(?P<expires>\d{4}-\d{2}-\d{2})\s+target=(?P<target>\S+)$"
)


def _parse_entries() -> list[dict[str, str]]:
    text = _DEFERRALS_PATH.read_text(encoding="utf-8")
    entries: list[dict[str, str]] = []
    in_code_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block or not stripped or stripped.startswith("#"):
            continue
        match = _LINE_PATTERN.match(stripped)
        assert match is not None, f"unparseable deferral line: {stripped!r}"
        entries.append(match.groupdict())
    return entries


def test_every_entry_has_three_fields() -> None:
    entries = _parse_entries()
    assert len(entries) >= 1
    for entry in entries:
        assert entry["symbol"].startswith("qts."), entry
        assert entry["target"], entry
        date.fromisoformat(entry["expires"])


def test_no_entry_is_expired() -> None:
    today = date.today()
    expired = [entry for entry in _parse_entries() if date.fromisoformat(entry["expires"]) < today]
    assert expired == [], f"expired deferrals: {expired}"


def test_no_entry_exceeds_one_year_horizon() -> None:
    horizon = date.today() + _MAX_HORIZON
    overshoot = [
        entry for entry in _parse_entries() if date.fromisoformat(entry["expires"]) > horizon
    ]
    assert overshoot == [], f"deferrals beyond 1-year horizon: {overshoot}"


def test_production_entries_expire_within_three_months() -> None:
    today = date.today()
    horizon = today + _WIRING_FOLLOWUP_HORIZON
    overshoot = [
        entry
        for entry in _parse_entries()
        if entry["target"] == "production" and date.fromisoformat(entry["expires"]) > horizon
    ]
    assert overshoot == [], f"production wiring deferrals must expire within 3 months: {overshoot}"


def test_no_roadmap_targets_are_allowed() -> None:
    forbidden = [entry for entry in _parse_entries() if entry["target"].startswith("OPT-")]
    assert forbidden == [], f"roadmap deferral targets are forbidden: {forbidden}"
