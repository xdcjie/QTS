"""Anchor tests for target_percent account-equity semantics (P0-1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import AccountId, InstrumentId
from qts.domain.market_data import Bar
from qts.runtime.intent_processing import OrderPlanBuilder
from qts.strategy_sdk import TargetIntent, TargetIntentType
from qts.strategy_sdk.asset_ref import AssetRef


def _bar(start: datetime, close: str = "100") -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
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


def _asset() -> AssetRef:
    return AssetRef(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        symbol="AAPL",
    )


class TestDesiredQuantityPercent:
    """Verify _desired_quantity for PERCENT intent uses account_equity * weight."""

    def test_flat_account_50_percent(self) -> None:
        """cash=100000, price=100, multiplier=1, target_percent=0.5 → qty=500."""
        qty = OrderPlanBuilder._desired_quantity(
            TargetIntent(
                intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0.5")
            ),
            current_quantity=Decimal("0"),
            market_price=Decimal("100"),
            account_equity=Decimal("100000"),
            multiplier=Decimal("1"),
        )
        assert qty == Decimal("500")

    def test_existing_position_delta(self) -> None:
        """Existing 100 shares, account_equity=100000, target 50% → order delta=400."""
        qty = OrderPlanBuilder._desired_quantity(
            TargetIntent(
                intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0.5")
            ),
            current_quantity=Decimal("100"),
            market_price=Decimal("100"),
            account_equity=Decimal("100000"),
            multiplier=Decimal("1"),
        )
        assert qty == Decimal("500")

    def test_target_zero_closes_position(self) -> None:
        """target_percent=0 returns zero quantity (close)."""
        qty = OrderPlanBuilder._desired_quantity(
            TargetIntent(intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0")),
            current_quantity=Decimal("100"),
            market_price=Decimal("100"),
            account_equity=Decimal("100000"),
            multiplier=Decimal("1"),
        )
        assert qty == Decimal("0")

    def test_account_equity_missing_raises(self) -> None:
        """PERCENT intent without account_equity raises ValueError."""
        with pytest.raises(ValueError, match="account_equity is required"):
            OrderPlanBuilder._desired_quantity(
                TargetIntent(
                    intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0.5")
                ),
                current_quantity=Decimal("0"),
                market_price=Decimal("100"),
                account_equity=None,
            )

    def test_account_equity_zero_raises(self) -> None:
        """PERCENT intent with zero account_equity raises ValueError."""
        with pytest.raises(ValueError, match="account_equity must be positive"):
            OrderPlanBuilder._desired_quantity(
                TargetIntent(
                    intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0.5")
                ),
                current_quantity=Decimal("0"),
                market_price=Decimal("100"),
                account_equity=Decimal("0"),
            )

    def test_futures_multiplier_adjusts_quantity(self) -> None:
        """Futures with multiplier=100: equity=100000, price=2000, 50% → qty=0.25."""
        qty = OrderPlanBuilder._desired_quantity(
            TargetIntent(
                intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0.5")
            ),
            current_quantity=Decimal("0"),
            market_price=Decimal("2000"),
            account_equity=Decimal("100000"),
            multiplier=Decimal("100"),
        )
        assert qty == Decimal("0.25")

    def test_old_formula_would_fail(self) -> None:
        """Verify old max(current_value, market_price) formula is gone.

        Old: max(0, 100) * 0.5 / 100 = 0.5
        New: 100000 * 0.5 / (100 * 1) = 500
        """
        qty = OrderPlanBuilder._desired_quantity(
            TargetIntent(
                intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0.5")
            ),
            current_quantity=Decimal("0"),
            market_price=Decimal("100"),
            account_equity=Decimal("100000"),
            multiplier=Decimal("1"),
        )
        assert qty != Decimal("0.5"), "old formula still in use"
        assert qty == Decimal("500")


class TestOrderPlanBuilderPercent:
    """Integration-level: OrderPlanBuilder.build() with account_equity."""

    def test_percent_plan_with_equity(self) -> None:
        from qts.backtest.instrument_context import BacktestInstrumentContext

        bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
        builder = OrderPlanBuilder(
            instrument_context=BacktestInstrumentContext(registry_bars=(bar,))
        )

        plans = builder.build(
            TargetIntent(
                intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0.5")
            ),
            account_id=AccountId("acct-backtest"),
            bar=bar,
            positions={},
            account_equity=Decimal("100000"),
            multiplier=Decimal("1"),
        )
        assert len(plans) == 1
        assert plans[0].quantity_delta == Decimal("500")

    def test_percent_plan_without_equity_raises(self) -> None:
        from qts.backtest.instrument_context import BacktestInstrumentContext

        bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
        builder = OrderPlanBuilder(
            instrument_context=BacktestInstrumentContext(registry_bars=(bar,))
        )

        with pytest.raises(ValueError, match="account_equity is required"):
            builder.build(
                TargetIntent(
                    intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0.5")
                ),
                account_id=AccountId("acct-backtest"),
                bar=bar,
                positions={},
            )
