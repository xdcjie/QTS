from __future__ import annotations

from pathlib import Path


def test_backtest_full_data_smoke_gate_is_explicit() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "backtest-full-smoke" in makefile
    assert "--config configs/backtest.gc_si.example.yaml" in makefile
    assert "--output-dir runs/backtests/full-smoke" in makefile


def test_backtest_acceptance_gate_is_explicit() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "backtest-acceptance:" in makefile
    assert (
        "scripts/validate_historical.py --root historical --roots GC --sample-rows 1000" in makefile
    )
    assert "tests/unit/data/test_historical_data_config.py" in makefile
    assert "tests/unit/data/test_historical_csv_dataset.py" in makefile
    assert "tests/unit/runtime/test_market_data_actor.py" in makefile
    assert "tests/unit/strategy_sdk/test_data_view.py" in makefile
    assert "tests/integration/test_backtest_gc_si.py" in makefile
    assert "tests/integration/test_backtest_engine_flow.py" in makefile
    assert "tests/anchor" in makefile
    assert "tests/replay/test_backtest_determinism.py" in makefile
    assert "tests/replay/test_backtest_report_hash.py" in makefile
    assert "--output-dir runs/backtests/stage-acceptance" in makefile


def test_gc_full_backtest_gate_is_explicit() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "backtest-gc-full:" in makefile
    assert "--streaming" in makefile
    assert "--config configs/backtest.gc.full.example.yaml" in makefile
    assert "--output-dir runs/backtests/gc-full" in makefile
