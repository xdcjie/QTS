"""M7: wiring_deferrals.md machine-readable block and rationale must not drift.

Domain fact / invariant: ``docs/plan/wiring_deferrals.md`` is the single
registry of knowingly-unwired production symbols. It carries two views of the
same data -- a fenced machine-readable code block (parsed by
``qts.quality.rules.caller_presence``) and a human rationale. The two views
must stay consistent:

- every per-symbol rationale **table row** must point at a live code-block
  entry (no orphan rationale rows left behind after a symbol gets wired);
- every **non-batch** code-block entry must have a per-symbol table row, and
  every **C5a-batch** entry (the 43 surfaced by the re-export-aware caller
  gate) is accounted for by the batch prose rather than a row.

Forbidden shortcut: deleting a symbol from the code block but leaving its
rationale row, or adding a code-block entry with no rationale.

Owner: ``docs/plan/wiring_deferrals.md`` (data) + this drift gate.
"""

from __future__ import annotations

import re
from pathlib import Path

_DEFERRALS_PATH = Path("docs/plan/wiring_deferrals.md")
_C5A_BATCH_MARKER = "C5a batch"
_TABLE_ROW_PATTERN = re.compile(r"^\|\s*`([^`]+)`\s*\|")
_CODE_LINE_PATTERN = re.compile(r"^(?P<symbol>\S+)\s+expires=\d{4}-\d{2}-\d{2}\s+target=\S+$")


def _read() -> str:
    return _DEFERRALS_PATH.read_text(encoding="utf-8")


def _code_block_symbols() -> dict[str, bool]:
    """Return ``{symbol: in_c5a_batch}`` for every fenced code-block entry."""
    symbols: dict[str, bool] = {}
    in_block = False
    in_c5a_batch = False
    for line in _read().splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            continue
        if stripped.startswith("#"):
            if _C5A_BATCH_MARKER in stripped:
                in_c5a_batch = True
            continue
        if not stripped:
            continue
        match = _CODE_LINE_PATTERN.match(stripped)
        assert match is not None, f"unparseable deferral line: {stripped!r}"
        symbols[match.group("symbol")] = in_c5a_batch
    return symbols


def _rationale_table_symbols() -> set[str]:
    """Return the symbols listed as per-symbol rows in the rationale table."""
    return {
        match.group(1)
        for line in _read().splitlines()
        if (match := _TABLE_ROW_PATTERN.match(line.strip())) is not None
    }


def test_every_rationale_row_maps_to_a_live_code_block_entry() -> None:
    code_symbols = set(_code_block_symbols())
    orphans = sorted(_rationale_table_symbols() - code_symbols)
    assert orphans == [], (
        f"rationale rows without a code-block entry (stale after wiring?): {orphans}"
    )


def test_every_non_batch_code_entry_has_a_rationale_row() -> None:
    table_symbols = _rationale_table_symbols()
    missing = sorted(
        symbol
        for symbol, in_batch in _code_block_symbols().items()
        if not in_batch and symbol not in table_symbols
    )
    assert missing == [], f"code-block entries without a rationale row: {missing}"


def test_c5a_batch_prose_accounts_for_batch_entries() -> None:
    batch_count = sum(1 for in_batch in _code_block_symbols().values() if in_batch)
    text = _read()
    assert _C5A_BATCH_MARKER in text
    # The prose states the batch is split into `library` (8) and `OPT-65` (35).
    assert "**`library` (8)**" in text
    assert "**`OPT-65` (35)**" in text
    assert batch_count == 8 + 35
