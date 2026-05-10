from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.core.ids import InstrumentId
from qts.data.provenance import DatasetMetadata
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy


def _bar(start: datetime, close: str) -> Bar:
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


def _metadata(dataset_id: str) -> DatasetMetadata:
    return DatasetMetadata(
        dataset_id=dataset_id,
        source="vendor-x",
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        timeframe="1m",
        timezone_policy="exchange",
        adjustment_policy="raw",
        normalization_version="bars-v1",
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        content_hash=f"sha256:{dataset_id}",
    )


class BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.has_ordered = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.has_ordered:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.has_ordered = True


def test_backtest_report_includes_run_identity_dataset_and_cost_assumptions() -> None:
    result = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "100")],
        initial_cash=Decimal("10000"),
        dataset_metadata=(_metadata("dataset-a"),),
        config={"mode": "unit", "seed": 7},
        strategy_version="buy-once-v1",
    ).run()

    assert result.run_id.value.startswith("bt-")
    assert result.strategy_version == "buy-once-v1"
    assert result.config_hash.startswith("sha256:")
    assert result.dataset_metadata[0].dataset_id == "dataset-a"
    assert result.cost_model.slippage_model == "zero"
    assert result.cost_model.commission_model == "zero"
    assert result.report_hash.startswith("sha256:")


def test_backtest_report_hash_changes_when_dataset_changes() -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)

    left = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=[_bar(start, "100")],
        initial_cash=Decimal("10000"),
        dataset_metadata=(_metadata("dataset-a"),),
    ).run()
    right = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=[_bar(start, "100")],
        initial_cash=Decimal("10000"),
        dataset_metadata=(_metadata("dataset-b"),),
    ).run()

    assert left.report_hash != right.report_hash
