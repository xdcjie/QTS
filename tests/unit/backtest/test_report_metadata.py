from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.core.ids import InstrumentId
from qts.data.provenance import DatasetMetadata
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy

from tests.support.backtest_streaming import run_engine_streaming


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
        row_count=10,
    )


class BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.has_ordered = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.has_ordered:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.has_ordered = True


def test_backtest_report_includes_run_identity_dataset_and_cost_assumptions(
    tmp_path: Path,
) -> None:
    result = run_engine_streaming(
        BacktestEngine(
            strategy=BuyOnceStrategy(),
            bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "100")],
            initial_cash=Decimal("10000"),
            dataset_metadata=(_metadata("dataset-a"),),
            config={"mode": "unit", "seed": 7},
            strategy_version="buy-once-v1",
        ),
        tmp_path / "metadata",
    ).result

    assert result.run_id.value.startswith("bt-")
    assert result.strategy_version == "buy-once-v1"
    assert result.config_hash.startswith("sha256:")
    assert result.dataset_metadata[0].dataset_id == "dataset-a"
    assert result.cost_model.slippage_model == "zero"
    assert result.cost_model.commission_model == "zero"
    assert result.report_hash.startswith("sha256:")


def test_backtest_manifest_includes_simulated_execution_assumptions(
    tmp_path: Path,
) -> None:
    from qts.runtime.config import BacktestCostModel

    stream = run_engine_streaming(
        BacktestEngine(
            strategy=BuyOnceStrategy(),
            bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "100")],
            initial_cash=Decimal("10000"),
            cost_model=BacktestCostModel(
                fixed_commission_per_contract=Decimal("2.50"),
                slippage_bps=Decimal("5"),
            ),
        ),
        tmp_path / "execution-assumptions",
    )

    assumptions = stream.manifest["execution_assumptions"]

    assert assumptions["fill_model_name"] == "immediate_market_fill"
    assert assumptions["fill_model_version"] == "1"
    assert assumptions["slippage_model_name"] == "basis_points"
    assert assumptions["slippage_model_version"] == "1"
    assert assumptions["commission_model_name"] == "fixed_per_contract"
    assert assumptions["commission_model_version"] == "1"
    assert assumptions["volume_participation_limit"] is None
    assert assumptions["partial_fill_policy"] == "none"
    assert assumptions["unsupported_order_rejection_policy"] == "reject_and_emit_runtime_event"
    assert assumptions["market_data_latency_model"] == "zero_latency_replay"
    assert assumptions["broker_capability_model"]["broker_id"] == "custom"
    assert assumptions["broker_capability_model"]["supports_market_orders"] is True


def test_backtest_report_hash_changes_with_execution_assumptions(tmp_path: Path) -> None:
    from qts.runtime.config import BacktestCostModel

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)

    zero_cost = run_engine_streaming(
        BacktestEngine(
            strategy=BuyOnceStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
            cost_model=BacktestCostModel(),
        ),
        tmp_path / "zero-cost",
    )
    nonzero_cost = run_engine_streaming(
        BacktestEngine(
            strategy=BuyOnceStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
            cost_model=BacktestCostModel(
                fixed_commission_per_contract=Decimal("1"),
                slippage_bps=Decimal("10"),
            ),
        ),
        tmp_path / "nonzero-cost",
    )

    assert (
        zero_cost.manifest["execution_assumptions"]
        != nonzero_cost.manifest["execution_assumptions"]
    )
    assert zero_cost.result.report_hash != nonzero_cost.result.report_hash


def test_backtest_report_hash_changes_when_dataset_changes(tmp_path: Path) -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)

    left = run_engine_streaming(
        BacktestEngine(
            strategy=BuyOnceStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
            dataset_metadata=(_metadata("dataset-a"),),
        ),
        tmp_path / "dataset-a",
    ).result
    right = run_engine_streaming(
        BacktestEngine(
            strategy=BuyOnceStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
            dataset_metadata=(_metadata("dataset-b"),),
        ),
        tmp_path / "dataset-b",
    ).result

    assert left.report_hash != right.report_hash
