"""Gate test for the class-boundary matrix line-count drift check (C5b).

The matrix records each oversized class's line count and a retain/split
decision. Previously the gate parsed the recorded count but never compared it to
the class's actual span, so a god-object could quietly triple while the matrix
(and its retain decision) referenced a stale size. ``_line_count_drifted`` makes
that drift a guardrail failure.
"""

from __future__ import annotations

from qts.quality.rules.inventory import _line_count_drifted, _parse_recorded_lines


def test_parse_recorded_lines_extracts_leading_integer() -> None:
    assert _parse_recorded_lines("715") == 715
    assert _parse_recorded_lines("  492 ") == 492
    assert _parse_recorded_lines("") is None
    assert _parse_recorded_lines("n/a") is None


def test_small_edits_within_tolerance_do_not_drift() -> None:
    # Tolerance is max(50, 15% of measured); routine growth stays green.
    assert _line_count_drifted(recorded=400, measured=430) is False
    assert _line_count_drifted(recorded=421, measured=480) is False  # 59 <= 72 (15% of 480)


def test_god_object_growth_is_flagged_as_drift() -> None:
    # The real regression: a class recorded at 715 that has grown to 2429.
    assert _line_count_drifted(recorded=715, measured=2429) is True
    assert _line_count_drifted(recorded=492, measured=2000) is True


def test_material_shrink_is_flagged_as_drift() -> None:
    # Drift is bidirectional so the matrix stays honest after a split/refactor.
    assert _line_count_drifted(recorded=2000, measured=600) is True
