"""Anchor: freeze exceptions must have a near-term expiry and a real reason.

Domain fact: a freeze exception without a near-term expiry becomes permanent
dead weight. The loader rejects entries that are already expired or whose
expiry is further than one year out from today.

Owner: ``qts.quality.guardrails._load_platform_freeze_config`` (loader) +
``scripts/verify_guardrails.py`` enforcement.

Forbidden shortcut: hard-coding ``expiry: 2099-12-31``; an empty or generic
``reason`` field.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import yaml

_EXCEPTIONS_PATH = Path("docs/architecture/platform_freeze_exceptions.yaml")
_MAX_EXPIRY_HORIZON = timedelta(days=365)


def _load_raw() -> list[dict[str, object]]:
    data = yaml.safe_load(_EXCEPTIONS_PATH.read_text(encoding="utf-8"))
    raw = data.get("exceptions", []) if isinstance(data, dict) else []
    assert isinstance(raw, list)
    return raw


def test_every_freeze_exception_has_non_empty_reason() -> None:
    bad = [
        (index, entry.get("class_name"))
        for index, entry in enumerate(_load_raw())
        if not isinstance(entry.get("reason"), str) or not str(entry["reason"]).strip()
    ]
    assert bad == [], f"freeze exceptions without reason: {bad}"


def test_every_freeze_exception_has_expiry_within_one_year() -> None:
    today = date.today()
    horizon = today + _MAX_EXPIRY_HORIZON
    overshoot: list[tuple[int, str, str]] = []
    expired: list[tuple[int, str, str]] = []
    for index, entry in enumerate(_load_raw()):
        expiry_value = str(entry.get("expiry", ""))
        try:
            expiry = date.fromisoformat(expiry_value)
        except ValueError:
            overshoot.append((index, str(entry.get("class_name")), expiry_value))
            continue
        if expiry < today:
            expired.append((index, str(entry.get("class_name")), expiry_value))
        if expiry > horizon:
            overshoot.append((index, str(entry.get("class_name")), expiry_value))
    assert expired == [], f"expired freeze exceptions: {expired[:5]}..."
    assert overshoot == [], (
        f"freeze exceptions with expiry > 1 year (or invalid): {overshoot[:5]}..."
    )
