from __future__ import annotations

from pathlib import Path

from tests.unit.research.engine.test_autonomous_engine_trial_generation import (
    test_backtest_data_materialization_mode_controls_truncation as _assert_materialization_mode,
)


def test_backtest_data_materialization_mode_controls_truncation(tmp_path: Path) -> None:
    _assert_materialization_mode(tmp_path)
