from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from qts.core.ids import InstrumentId
from qts.data.provenance import DatasetMetadata
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy

from tests.support.backtest_engine import backtest_engine_from_inputs
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
    stream = run_engine_streaming(
        backtest_engine_from_inputs(
            strategy=BuyOnceStrategy(),
            bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "100")],
            initial_cash=Decimal("10000"),
            dataset_metadata=(_metadata("dataset-a"),),
            config={"mode": "unit", "seed": 7},
            strategy_version="buy-once-v1",
        ),
        tmp_path / "metadata",
    )
    result = stream.result
    manifest_dataset = stream.manifest["dataset_metadata"][0]

    assert result.run_id.value.startswith("bt-")
    assert result.strategy_version == "buy-once-v1"
    assert result.config_hash.startswith("sha256:")
    assert result.dataset_metadata[0].dataset_id == "dataset-a"
    assert result.cost_model.slippage_model == "zero"
    assert result.cost_model.commission_model == "zero"
    assert result.report_hash.startswith("sha256:")
    assert stream.manifest["risk_config_hash"].startswith("sha256:")
    assert stream.manifest["topology_hash"].startswith("sha256:")
    assert manifest_dataset["dataset_id"] == "dataset-a"
    assert manifest_dataset["file_hash"] == "sha256:dataset-a"
    assert manifest_dataset["row_count"] == 10
    assert manifest_dataset["first_ts"] == "2026-01-02T14:30:00+00:00"
    assert manifest_dataset["last_ts"] == "2026-01-02T14:31:00+00:00"
    assert manifest_dataset["timezone"] == "exchange"
    assert manifest_dataset["adjustment_mode"] == "raw"


def test_backtest_manifest_includes_simulated_execution_assumptions(
    tmp_path: Path,
) -> None:
    from qts.runtime.config import BacktestCostModel

    stream = run_engine_streaming(
        backtest_engine_from_inputs(
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
    assert assumptions["slippage_model"] == "basis_points"
    assert assumptions["slippage_model_version"] == "1"
    assert assumptions["commission_model"] == "fixed_per_contract"
    assert assumptions["commission_model_version"] == "1"
    assert assumptions["volume_participation_limit"] is None
    assert assumptions["partial_fill_policy"] == "none"
    assert assumptions["unsupported_order_rejection_policy"] == "reject_and_emit_runtime_event"
    assert assumptions["market_data_latency_model"] == "zero_latency_replay"
    assert assumptions["broker_capability_model"]["broker_id"] == "custom"
    assert assumptions["broker_capability_model"]["supports_market_orders"] is True


def test_backtest_finalize_rejects_missing_required_m1_manifest_fields(
    tmp_path: Path,
) -> None:
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint

    cases = (
        "risk_config_hash",
        "dataset_metadata[0].file_hash",
        "execution_assumptions.fill_model_name",
    )
    for case in cases:
        writer = BacktestArtifactWriter(tmp_path / case.replace(".", "-").replace("[", "-"))
        writer.write_equity_point(
            EquityCurvePoint(
                time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
                equity=Decimal("10000"),
            )
        )
        dataset_metadata = {
            "dataset_id": "dataset-a",
            "file_hash": "sha256:dataset-a",
            "row_count": 1,
            "first_ts": "2026-01-02T14:30:00+00:00",
            "last_ts": "2026-01-02T14:31:00+00:00",
            "timezone": "UTC",
            "adjustment_mode": "raw",
        }
        execution_assumptions = {
            "fill_model_name": "immediate_market_fill",
            "fill_model_version": "1",
            "slippage_model": "zero",
            "commission_model": "zero",
            "partial_fill_policy": "none",
            "broker_capability_model": {"broker_id": "custom"},
        }
        risk_config_hash: str | None = "sha256:risk"
        if case == "risk_config_hash":
            risk_config_hash = None
        elif case == "dataset_metadata[0].file_hash":
            dataset_metadata.pop("file_hash")
        elif case == "execution_assumptions.fill_model_name":
            execution_assumptions.pop("fill_model_name")

        with pytest.raises(ValueError, match=case.replace("[0]", r"\[0\]")):
            writer.finalize(
                config_hash="sha256:cfg",
                dataset_metadata=(dataset_metadata,),
                cost_model={},
                processed_bars=1,
                warmup_bars=0,
                trading_bars=1,
                final_cash=Decimal("10000"),
                strategy_version="test",
                runtime_topology_payload={"topology_hash": "sha256:topology"},
                risk_config_hash=risk_config_hash,
                execution_assumptions=execution_assumptions,
            )


def test_backtest_finalize_rejects_missing_execution_assumptions_block(
    tmp_path: Path,
) -> None:
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint

    writer = BacktestArtifactWriter(tmp_path / "missing-execution-assumptions")
    writer.write_equity_point(
        EquityCurvePoint(
            time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            equity=Decimal("10000"),
        )
    )

    with pytest.raises(ValueError, match="execution_assumptions"):
        writer.finalize(
            config_hash="sha256:cfg",
            dataset_metadata=(
                {
                    "dataset_id": "dataset-a",
                    "file_hash": "sha256:dataset-a",
                    "row_count": 1,
                    "first_ts": "2026-01-02T14:30:00+00:00",
                    "last_ts": "2026-01-02T14:31:00+00:00",
                    "timezone": "UTC",
                    "adjustment_mode": "raw",
                },
            ),
            cost_model={},
            processed_bars=1,
            warmup_bars=0,
            trading_bars=1,
            final_cash=Decimal("10000"),
            strategy_version="test",
            runtime_topology_payload={"topology_hash": "sha256:topology"},
            risk_config_hash="sha256:risk",
            execution_assumptions=None,
        )


def test_backtest_report_hash_changes_with_execution_assumptions(tmp_path: Path) -> None:
    from qts.runtime.config import BacktestCostModel

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)

    zero_cost = run_engine_streaming(
        backtest_engine_from_inputs(
            strategy=BuyOnceStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
            cost_model=BacktestCostModel(),
        ),
        tmp_path / "zero-cost",
    )
    nonzero_cost = run_engine_streaming(
        backtest_engine_from_inputs(
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
        backtest_engine_from_inputs(
            strategy=BuyOnceStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
            dataset_metadata=(_metadata("dataset-a"),),
        ),
        tmp_path / "dataset-a",
    ).result
    right = run_engine_streaming(
        backtest_engine_from_inputs(
            strategy=BuyOnceStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
            dataset_metadata=(_metadata("dataset-b"),),
        ),
        tmp_path / "dataset-b",
    ).result

    assert left.report_hash != right.report_hash
