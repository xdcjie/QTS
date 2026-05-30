"""``BacktestArtifactService`` owns sink creation and manifest finalization.

These tests lock the artifact-ownership boundary extracted from the backtest
engine: the service builds the normalized runtime-event sink, records the
bootstrap equity point for an empty run, and finalizes a manifest with the
artifact paths/hashes the engine reports back.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from qts.backtest.artifacts import BacktestArtifactService
from qts.backtest.runtime_manifest import BacktestRuntimeTopologyManifestBuilder
from qts.core.ids import AccountId, RuntimeRunId, StrategyId
from qts.runtime.sinks.backtest import BacktestRuntimeEventSink


def _service(output_dir: Path) -> BacktestArtifactService:
    return BacktestArtifactService(
        output_dir,
        run_id=RuntimeRunId("bt-test"),
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strategy"),
    )


def test_service_exposes_runtime_event_sink(tmp_path: Path) -> None:
    service = _service(tmp_path)
    assert isinstance(service.sink, BacktestRuntimeEventSink)


def test_finalize_returns_run_id_and_manifest(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.record_empty_run_equity(equity=Decimal("100000"), last_bar_end_time=None)
    topology = BacktestRuntimeTopologyManifestBuilder().resolve(
        backtest_runtime_config=None,
        runtime_run_id=RuntimeRunId("bt-test"),
        default_account_id=AccountId("acct-backtest"),
        default_strategy_id=StrategyId("strategy"),
    )

    dataset_row = {
        "dataset_id": "ds-1",
        "file_hash": "sha256:data",
        "row_count": 1,
        "first_ts": "2024-01-02T14:30:00+00:00",
        "last_ts": "2024-01-02T21:00:00+00:00",
        "timezone": "America/New_York",
        "adjustment_mode": "raw",
    }

    run_id_value, report_hash, _report, artifacts = service.finalize(
        config_hash="sha256:cafe",
        dataset_metadata=(dataset_row,),
        cost_model={},
        processed_bars=0,
        warmup_bars=0,
        trading_bars=0,
        final_cash=Decimal("100000"),
        strategy_version="v1",
        runtime_topology_payload=topology.payload,
        brokerage_model="CUSTOM",
        execution_assumptions={
            "fill_model_name": "next_bar_open",
            "fill_model_version": "1",
            "slippage_model": "none",
            "commission_model": "none",
            "partial_fill_policy": "all_or_none",
            "broker_capability_model": "CUSTOM",
        },
        risk_config_hash="sha256:risk",
    )

    assert run_id_value == "bt-test"
    assert report_hash.startswith("sha256:")
    assert Path(artifacts.manifest_path).exists()
    assert "equity_curve" in artifacts.artifact_rows
    assert artifacts.artifact_rows["equity_curve"] == 1
