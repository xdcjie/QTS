from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from qts.core.ids import InstrumentId
from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar

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


def test_backtest_core_chain_smoke(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.strategy_sdk import Strategy

    class SmokeBuyStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.ordered = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            if not self.ordered:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.ordered = True

    bars = [
        _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "100"),
        _bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC), "101"),
    ]
    captured = run_engine_streaming(
        BacktestEngine(
            strategy=SmokeBuyStrategy(),
            bars=bars,
            initial_cash=Decimal("10000"),
            # Core-chain smoke is fill-policy independent; pin same-bar fills.
            execution_timing=ExecutionTimingModel.research_only(),
        ),
        tmp_path / "backtest-smoke",
    )

    assert captured.result.final_account.positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("1")
    assert captured.result.final_account.cash["USD"] == Decimal("9900")
    assert captured.result.processed_bars == 2


def test_paper_runtime_chain_smoke_with_fake_boundary() -> None:
    import importlib

    import pytest
    import qts.runtime as runtime_package
    from qts.runtime.session import RuntimeSession

    assert not hasattr(runtime_package, "LiveRuntime")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("qts.runtime.live")
    assert not hasattr(RuntimeSession, "submit_order")


def test_runtime_event_sink_smoke(tmp_path: Path) -> None:
    from qts.core.ids import CorrelationId, RuntimeRunId
    from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext
    from qts.runtime.sinks.broker_runtime import BrokerRuntimeEventSink

    sink = BrokerRuntimeEventSink(
        tmp_path,
        context=RuntimeEventContext(run_id=RuntimeRunId("run-smoke"), mode="paper_broker"),
    )
    event = RuntimeEvent(
        kind="runtime.market_data",
        payload={"instrument_id": "EQUITY.US.NASDAQ.AAPL"},
        correlation_id=CorrelationId("corr-smoke"),
    )
    written = sink.write(event)
    sink.close()

    rows = [json.loads(line) for line in sink.path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["event_hash"] == written.event_hash
    assert rows[0]["sequence_no"] == 1
    assert rows[0]["payload_schema_version"] == RuntimeEvent.SCHEMA_VERSION


def _run_architecture_script(script: Path, output: Path) -> list[Any]:
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--source",
            "backend/src",
            "--output",
            str(output),
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    with output.open("r", encoding="utf-8") as handle:
        return cast(list[Any], json.load(handle))


def test_architecture_inventory_snapshot_smoke(tmp_path: Path) -> None:
    expected_keys = {
        "name",
        "module",
        "file",
        "lineno",
        "public",
        "docstring_first_line",
        "direct_imports",
        "method_count",
    }
    payload = _run_architecture_script(
        script=Path("tools/architecture/export_inventory.py"),
        output=tmp_path / "class_inventory_smoke.json",
    )
    assert isinstance(payload, list)
    assert payload and expected_keys <= payload[0].keys()


def test_architecture_import_graph_snapshot_smoke(tmp_path: Path) -> None:
    payload = _run_architecture_script(
        script=Path("tools/architecture/export_import_graph.py"),
        output=tmp_path / "import_graph_smoke.json",
    )
    assert isinstance(payload, dict)
    assert payload
    assert all(isinstance(key, str) for key in payload)


def test_runtime_topology_private_builder_is_not_canonical() -> None:
    import ast

    topology_tree = ast.parse(
        Path("backend/src/qts/runtime/broker_runtime_topology.py").read_text(encoding="utf-8")
    )
    session_source = Path("backend/src/qts/runtime/session.py").read_text(encoding="utf-8")
    class_names = {node.name for node in topology_tree.body if isinstance(node, ast.ClassDef)}

    assert "_LiveRuntimeTopologyBuilder" not in class_names
    assert "_ResolvedLiveRuntimeTopology" not in class_names
    assert "_StrategyRuntimeBinding" not in class_names
    assert "_LiveRuntimeTopologyBuilder" not in session_source
    assert "_StrategyRuntimeBinding" not in session_source
    assert "BrokerRuntimeTopologyResolver" in class_names
    assert "ResolvedRuntimeTopology" in class_names
    assert "StrategyRuntimeBinding" in class_names
