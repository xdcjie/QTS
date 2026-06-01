"""Backtest compatibility import for the runtime instrument context."""

from __future__ import annotations

from qts.runtime.instrument_context import RuntimeInstrumentContext

BacktestInstrumentContext = RuntimeInstrumentContext


__all__ = ["BacktestInstrumentContext"]
