"""QTS-FINAL-004 anchor: the default fill policy is next-obtainable.

Domain invariant: a decision made at the close of a completed bar N can only be
acted on at the next obtainable price (bar N+1's open). The system default must
therefore be ``next_bar_open``; the optimistic ``same_bar_close`` look-ahead is
opt-in only, requires an explicit waiver, and is never promotion-grade.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from qts.core.ids import InstrumentId
from qts.domain.execution_timing import ExecutionTimingModel, FillPolicy
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
)

pytestmark = pytest.mark.anchor

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _config(**overrides: object) -> BacktestRuntimeConfig:
    params: dict[str, object] = {
        "roots": ("AAPL",),
        "symbols": ("AAPL",),
        "start": datetime(2026, 1, 2, tzinfo=UTC),
        "end": datetime(2026, 1, 3, tzinfo=UTC),
        "timeframe": "1m",
        "initial_cash": Decimal("10000"),
        "strategy_class": "tests.support.fill_policy.BuyOnce",
        "market_data": BacktestMarketDataReference(config_path=Path("md.yaml"), catalog="research"),
        "instrument_ids": {"AAPL": _INSTRUMENT},
        "risk_config": BacktestRiskConfig(max_notional=Decimal("1000000")),
    }
    params.update(overrides)
    return BacktestRuntimeConfig(**params)  # type: ignore[arg-type]


def test_execution_timing_model_default_is_next_bar_open() -> None:
    model = ExecutionTimingModel()
    assert model.fill_policy is FillPolicy.NEXT_BAR_OPEN
    assert model.is_promotion_grade
    assert not model.is_optimistic


def test_backtest_runtime_config_default_fill_policy_is_next_bar_open() -> None:
    config = _config()
    assert config.fill_policy == "next_bar_open"
    assert config.optimistic_fill_waiver is False


def test_config_same_bar_close_requires_explicit_waiver() -> None:
    with pytest.raises(ValueError, match="optimistic_fill_waiver"):
        _config(fill_policy="same_bar_close")

    waived = _config(fill_policy="same_bar_close", optimistic_fill_waiver=True)
    assert waived.fill_policy == "same_bar_close"
    assert waived.optimistic_fill_waiver is True


def test_config_payload_always_records_fill_identity() -> None:
    payload = _config().to_payload()
    # Fill timing is part of run identity even at the default; never omitted.
    assert payload["fill_policy"] == "next_bar_open"
    assert payload["optimistic_fill_waiver"] is False
