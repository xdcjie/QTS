"""Unit tests for backtest strategy loading."""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any, cast

import pytest
from qts.backtest.runner import _load_strategy


def test_load_strategy_supports_module_and_class_syntax() -> None:
    """Load strategies from both supported class path formats."""
    colon_strategy = _load_strategy(
        "tests.integration.test_backtest_gc_si:BuyOneGcStrategy",
        {},
    )
    dotted_strategy = _load_strategy(
        "tests.integration.test_backtest_gc_si.BuyOneGcStrategy",
        {},
    )

    assert colon_strategy.__class__.__name__ == "BuyOneGcStrategy"
    assert dotted_strategy.__class__.__name__ == "BuyOneGcStrategy"


def test_load_strategy_loads_from_relative_python_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Load a strategy from a file when module import fails but .py exists."""
    module_name = "tmp_backtest_strategy_fixture"
    module_path = tmp_path / f"{module_name}.py"
    module_path.write_text(
        textwrap.dedent(
            """
            from qts.strategy_sdk import Strategy


            class FileBacktestStrategy(Strategy):
                def __init__(self, note: str = "ok") -> None:
                    self.note = note
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    strategy = _load_strategy(f"{module_name}:FileBacktestStrategy", {"note": "loaded"})
    assert cast(Any, strategy).note == "loaded"


def test_load_strategy_rejects_invalid_class_path() -> None:
    """Reject malformed strategy class references."""
    with pytest.raises(ValueError, match="strategy_class must be 'module:Class'"):
        _load_strategy("not_a_path", {})


def test_load_strategy_rejects_missing_class() -> None:
    """Reject when class name does not exist in module."""
    with pytest.raises(ValueError, match="not found in module"):
        _load_strategy(
            "tests.integration.test_backtest_gc_si:MissingBacktestStrategy",
            {},
        )


def test_load_strategy_rejects_non_strategy_class(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject classes that do not subclass qts.strategy_sdk.Strategy."""
    module_name = "tmp_backtest_not_strategy"
    module_path = tmp_path / f"{module_name}.py"
    module_path.write_text(
        textwrap.dedent(
            """
            class NotStrategy:
                pass
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(TypeError, match="must subclass"):
        _load_strategy(f"{module_name}:NotStrategy", {})
