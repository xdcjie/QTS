"""Integration: futures order exceeding available margin is rejected pre-trade (DR-005)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from qts.backtest.engine import BacktestEngine
from qts.core.ids import InstrumentId
from qts.domain.instruments import AssetClass, ContractSpec, FutureSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.margin.calculator import MarginCalculator
from qts.risk.rules.margin_limit import MarginRule
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
)
from qts.strategy_sdk import Strategy

from tests.support.backtest_streaming import run_engine_streaming
from tests.support.risk_runtime_harness import RiskRuntimeHarness


def _harness(initial_cash: str) -> RiskRuntimeHarness:
    return RiskRuntimeHarness(
        rules=[MarginRule()],
        multiplier=Decimal("100"),
        initial_cash=Decimal(initial_cash),
        margin_calculator=MarginCalculator(initial_margin_rate=Decimal("0.05")),
    )


def test_runtime_rejects_order_exceeding_available_margin() -> None:
    # Equity 10000; a 30-lot needs 30*100*100*0.05 = 15000 initial margin > 10000.
    harness = _harness("10000")
    result = harness.submit(
        target_quantity="30", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100"
    )
    assert result.orders == ()
    assert result.fills == ()
    assert len(result.risk_decisions) == 1
    decision = result.risk_decisions[0]
    assert decision.reason_code == "MARGIN_LIMIT_EXCEEDED"
    assert decision.evidence["available_margin"] == Decimal("10000")
    assert decision.evidence["projected_margin"] == Decimal("15000")


def test_runtime_approves_order_within_available_margin() -> None:
    # Equity 1,000,000; a 2-lot needs only 1000 margin -> approved and filled.
    harness = _harness("1000000")
    result = harness.submit(
        target_quantity="2", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100"
    )
    assert result.orders
    assert all(d.approved for d in result.risk_decisions)


# --- Config-driven backtest: per-contract margin rate flows from ContractSpec ---

_FUTURE_ID = InstrumentId("FUTURE.CMES.GC.202606")
_START = datetime(2026, 1, 2, 18, 0, tzinfo=UTC)


class _BuyThirtyLotsOnce(Strategy):
    """Target thirty lots on the first bar; sizing is over-margin at 0.05."""

    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("GC")
        self._submitted = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self._submitted:
            ctx.target_quantity(self.asset, Decimal("30"))
            self._submitted = True


def _future_instrument(*, initial_margin_rate: Decimal | None) -> Instrument:
    from datetime import date

    return Instrument(
        instrument_id=_FUTURE_ID,
        asset_class=AssetClass.FUTURE,
        exchange="CMES",
        currency="USD",
        contract_spec=ContractSpec(
            tick_size=Decimal("0.1"),
            lot_size=Decimal("1"),
            multiplier=Decimal("100"),
            settlement=SettlementType.PHYSICAL,
            calendar_id="CMES",
            initial_margin_rate=initial_margin_rate,
        ),
        derivative=FutureSpec(
            expiry=date(2026, 6, 26),
            underlying=InstrumentId("FUTURE_ROOT.CMES.GC"),
            root_symbol="GC",
        ),
    )


def _registry(*, initial_margin_rate: Decimal | None) -> InstrumentRegistry:
    registry = InstrumentRegistry()
    registry.register("GC", _future_instrument(initial_margin_rate=initial_margin_rate))
    return registry


def _gc_bar(start: datetime, close: str) -> Bar:
    return Bar(
        instrument_id=_FUTURE_ID,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def _config(tmp_path: Path) -> BacktestRuntimeConfig:
    # Equity 10,000; thirty 100-multiplier lots at price 100 = 300,000 notional.
    # Projected initial margin = 30 * 100 * 100 * 0.05 = 15,000 > 10,000 equity,
    # so the order must be rejected pre-trade by the margin gate.
    return BacktestRuntimeConfig(
        roots=("GC",),
        symbols=("GC",),
        start=_START,
        end=_START + timedelta(minutes=2),
        timeframe="1m",
        initial_cash=Decimal("10000"),
        instrument_ids={"GC": _FUTURE_ID},
        market_data=BacktestMarketDataReference(
            config_path=tmp_path / "historical.yaml",
            catalog="unit",
        ),
        # Large notional ceiling so MaxNotionalRule never fires; this isolates the
        # margin gate as the only rule that can reject the 300,000-notional order.
        risk_config=BacktestRiskConfig(max_notional=Decimal("100000000")),
        strategy_class=f"{__name__}:_BuyThirtyLotsOnce",
    )


def _run(tmp_path: Path, *, initial_margin_rate: Decimal | None) -> Any:
    bars = [_gc_bar(_START, "100"), _gc_bar(_START + timedelta(minutes=1), "100")]
    engine = BacktestEngine.from_config(
        _config(tmp_path),
        bars=bars,
        strategy=_BuyThirtyLotsOnce(),
        instrument_registry=_registry(initial_margin_rate=initial_margin_rate),
        contract_multipliers={_FUTURE_ID: Decimal("100")},
    )
    return run_engine_streaming(engine, tmp_path / "run").result


def test_config_driven_backtest_rejects_over_margin_future_order(tmp_path: Path) -> None:
    # With a configured 0.05 margin rate, MarginRule is wired and the over-margin
    # order is rejected pre-trade on the real runtime path: no position, no fill.
    result = _run(tmp_path, initial_margin_rate=Decimal("0.05"))
    assert _FUTURE_ID not in result.final_account.positions
    assert result.final_account.cash["USD"] == Decimal("10000")


def test_config_driven_backtest_without_margin_rate_fails_closed(tmp_path: Path) -> None:
    # Tradable futures must carry product-owned margin economics. Missing margin
    # data now rejects the run before orders can bypass the margin gate.
    with pytest.raises(
        ValueError,
        match="futures instruments missing initial_margin_rate: FUTURE\\.CMES\\.GC\\.202606",
    ):
        _run(tmp_path, initial_margin_rate=None)
