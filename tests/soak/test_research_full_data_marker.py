from __future__ import annotations

from pathlib import Path


def test_research_full_data_smoke_gate_is_explicit() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "research-full-smoke" in makefile
    assert "--config configs/backtest.gc_si.example.yaml" in makefile
    assert "--output-dir runs/backtests/full-smoke" in makefile
