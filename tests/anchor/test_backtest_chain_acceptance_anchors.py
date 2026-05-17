from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path


def test_real_gc_first_timestamp_roll_selects_highest_volume_outright_contract() -> None:
    from qts.core.ids import InstrumentId
    from qts.data.historical.chains import HistoricalChain
    from qts.data.historical.csv_dataset import iter_historical_bars
    from qts.registry.future_roll import HighestVolumeFutureContractSelector

    chain = HistoricalChain.load(Path("historical/chains/GC.json"))
    continuous_id = InstrumentId("CONTINUOUS_FUTURE.CME.GC")
    stream = iter_historical_bars(
        Path("historical/data/gc.csv"),
        chain,
        timeframe="1m",
        start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
        end=datetime(2010, 6, 6, 22, 1, tzinfo=UTC),
        contract_selector=HighestVolumeFutureContractSelector(),
        continuous_instrument_id=continuous_id,
    )

    bars = tuple(stream)

    assert len(bars) == 1
    assert bars[0].instrument_id == continuous_id
    assert bars[0].close == Decimal("1221.600000000")
    assert stream.roll_selections[0].source_symbol == "GCQ0"
    assert stream.roll_selections[0].concrete_instrument_id == InstrumentId("FUTURE.CME.GC.GCQ0")
    assert stream.roll_selections[0].prices_by_instrument[
        InstrumentId("FUTURE.CME.GC.GCQ0")
    ] == Decimal("1221.600000000")
    assert stream.stats.rows_seen >= 5
    assert stream.stats.spreads_excluded == 2
    assert stream.stats.contracts_excluded == 2


def test_strategy_runtime_receives_only_completed_requested_timeframe_bars() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Bar
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.market_data_actor import MarketDataActor, MarketDataEvent
    from qts.runtime.mailbox import Mailbox

    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    start = datetime(2026, 1, 6, 14, 30, tzinfo=UTC)
    subscriber = Mailbox()
    actor = MarketDataActor(
        subscribers=(ActorRef(mailbox=subscriber),),
        aggregate_timeframe="5m",
        exchange_timezone=UTC,
    )

    for offset in range(4):
        actor.handle(
            MarketDataEvent(
                payload=Bar(
                    instrument_id=instrument_id,
                    start_time=start + timedelta(minutes=offset),
                    end_time=start + timedelta(minutes=offset + 1),
                    timeframe="1m",
                    session_id="2026-01-06",
                    open=Decimal(str(2600 + offset)),
                    high=Decimal(str(2601 + offset)),
                    low=Decimal(str(2599 + offset)),
                    close=Decimal(str(2600 + offset)),
                    volume=Decimal("10"),
                    is_complete=True,
                )
            )
        )
        assert subscriber.empty()

    actor.handle(
        MarketDataEvent(
            payload=Bar(
                instrument_id=instrument_id,
                start_time=start + timedelta(minutes=4),
                end_time=start + timedelta(minutes=5),
                timeframe="1m",
                session_id="2026-01-06",
                open=Decimal("2604"),
                high=Decimal("2605"),
                low=Decimal("2603"),
                close=Decimal("2604"),
                volume=Decimal("10"),
                is_complete=True,
            )
        )
    )

    completed = subscriber.get()
    assert isinstance(completed, Bar)
    assert completed.start_time == start
    assert completed.end_time == start + timedelta(minutes=5)
    assert completed.timeframe == "5m"
    assert completed.open == Decimal("2600")
    assert completed.close == Decimal("2604")
    assert completed.volume == Decimal("50")
    assert completed.is_complete
    assert subscriber.empty()


def test_backtest_artifact_contract_contains_auditable_inputs_outputs_and_hashes(
    tmp_path: Path,
) -> None:
    from qts.backtest.runner import run_backtest
    from qts.reporting.base import NON_BROKER_HASH_SENTINEL, RuntimeManifest

    from tests.support.backtest_streaming import capture_stream_result

    run = run_backtest(
        Path("configs/backtest.gc_si.example.yaml"),
        output_dir=tmp_path / "runs",
    )
    captured = capture_stream_result(run.result)
    manifest = captured.manifest

    assert set(manifest) == {
        "artifacts",
        "artifact_schema_version",
        "brokerage_model",
        "account_environment",
        "config_hash",
        "cost_model",
        "created_at",
        "dataset_metadata",
        "event_schema_version",
        "execution_environment",
        "execution_assumptions",
        "finalized_at",
        "order_submission_permission",
        "manifest_hash",
        "market_data_environment",
        "metrics",
        "operator_identity_hash",
        "processed_bars",
        "report_hash",
        "risk_config_hash",
        "run_id",
        "runtime_instance_id",
        "runtime_mode",
        "statistics",
        "statistics_hash",
        "source_commit",
        "startup_checklist_hash",
        "platform_baseline_version",
        "topology_hash",
        "runtime_topology",
        "trading_bars",
        "warmup_bars",
    }
    runtime_manifest = RuntimeManifest.from_payload(manifest)
    assert set(manifest["artifacts"]) == {
        "events",
        "orders",
        "fills",
        "trade_ledger",
        "equity_curve",
        "statistics",
    }
    assert manifest["run_id"] == run.result.run_id.value
    assert runtime_manifest.run_id == run.result.run_id.value
    assert manifest["runtime_instance_id"] == manifest["run_id"]
    assert manifest["runtime_mode"] == "backtest"
    assert manifest["market_data_environment"] == "historical_replay"
    assert manifest["execution_environment"] == "simulated"
    assert manifest["account_environment"] == "simulated"
    assert manifest["order_submission_permission"] is False
    assert manifest["startup_checklist_hash"] == NON_BROKER_HASH_SENTINEL
    assert manifest["operator_identity_hash"] == NON_BROKER_HASH_SENTINEL
    assert manifest["event_schema_version"] == "1"
    assert manifest["artifact_schema_version"] == "1"
    assert manifest["manifest_hash"] == runtime_manifest.manifest_hash
    assert manifest["execution_assumptions"]["fill_model_name"] == "immediate_market_fill"
    assert manifest["execution_assumptions"]["broker_capability_model"]["broker_id"] == "custom"
    assert manifest["topology_hash"] == manifest["runtime_topology"]["topology_hash"]
    assert manifest["brokerage_model"] == "CUSTOM"
    assert manifest["config_hash"] == run.result.config_hash
    assert manifest["report_hash"] == run.result.report_hash
    assert manifest["processed_bars"] == len(captured.equity_curve)
    assert len(captured.orders) == len(captured.fills) == len(captured.trade_ledger)
    assert {item["source"] for item in manifest["dataset_metadata"]} == {
        "historical/data/gc.csv",
        "historical/data/si.csv",
    }
