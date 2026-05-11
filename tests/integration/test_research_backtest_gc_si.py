from __future__ import annotations

import csv
import importlib.util
import json
import shutil
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from qts.backtest.config import BacktestRunConfig, CostModelConfig, RiskConfig
from qts.core.ids import InstrumentId
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy


def _config(*, warmup_bars: int = 0) -> BacktestRunConfig:
    return BacktestRunConfig(
        dataset_root=Path("historical"),
        roots=("GC",),
        symbols=("GCQ0",),
        start=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        end=datetime(2026, 1, 2, 14, 35, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("1000000"),
        strategy_class="tests.integration.test_research_backtest_gc_si:BuyOneGcStrategy",
        strategy_params={},
        cost_model=CostModelConfig(),
        risk_config=RiskConfig(max_notional=Decimal("100000000")),
        warmup_bars=warmup_bars,
    )


def _bar(start: datetime, close: str = "2000.0") -> Bar:
    price = Decimal(close)
    return Bar(
        instrument_id=InstrumentId("FUTURE.CME.GC.GCQ0"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal("1"),
        is_complete=True,
    )


class BuyOneGcStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("GCQ0")
        self.done = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.done:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.done = True


class BuyOneAaplStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.done = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.done:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.done = True


def test_backtest_engine_runs_from_config_with_deterministic_run_id() -> None:
    from qts.backtest.engine import BacktestEngine

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start), _bar(start + timedelta(minutes=1), "2001.0")]

    left = BacktestEngine.from_config(_config(), bars=bars, strategy=BuyOneGcStrategy()).run()
    right = BacktestEngine.from_config(_config(), bars=bars, strategy=BuyOneGcStrategy()).run()

    assert left.config_hash == _config().config_hash
    assert left.run_id == right.run_id
    assert left.report.config_hash == _config().config_hash


def test_backtest_engine_from_config_does_not_require_chain_for_static_instrument_ids() -> None:
    from qts.backtest.engine import BacktestEngine

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    config = BacktestRunConfig(
        dataset_root=Path("historical"),
        roots=("EQUITY",),
        symbols=("AAPL",),
        instrument_ids={"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")},
        start=start,
        end=start + timedelta(minutes=1),
        timeframe="1m",
        initial_cash=Decimal("100000"),
        strategy_class="tests.integration.test_research_backtest_gc_si:BuyOneAaplStrategy",
        risk_config=RiskConfig(max_notional=Decimal("100000000")),
    )
    bar = Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("150"),
        high=Decimal("150"),
        low=Decimal("150"),
        close=Decimal("150"),
        volume=Decimal("100"),
        is_complete=True,
    )

    result = BacktestEngine.from_config(
        config,
        bars=[bar],
        strategy=BuyOneAaplStrategy(),
    ).run()

    assert result.fills[0].instrument_id == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert result.final_account.cash["USD"] == Decimal("99850")


def test_warmup_bars_call_strategy_but_do_not_place_orders() -> None:
    from qts.backtest.engine import BacktestEngine

    class WarmupTargetStrategy(BuyOneGcStrategy):
        pass

    result = BacktestEngine.from_config(
        _config(warmup_bars=1),
        bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))],
        strategy=WarmupTargetStrategy(),
    ).run()

    assert result.orders == ()
    assert result.warmup_bars == 1
    assert result.trading_bars == 0
    assert result.report.warmup_bars == 1


def test_strategy_finalize_runs_once_and_finalize_intents_are_ignored() -> None:
    from qts.backtest.engine import BacktestEngine

    class FinalizeStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("GCQ0")
            self.finalized = 0

        def finalize(self, ctx: Any) -> None:
            self.finalized += 1
            ctx.target_quantity(self.asset, Decimal("1"))

    strategy = FinalizeStrategy()
    result = BacktestEngine.from_config(
        _config(),
        bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))],
        strategy=strategy,
    ).run()

    assert strategy.finalized == 1
    assert result.orders == ()


def test_futures_multiplier_affects_backtest_fill_cash() -> None:
    from qts.backtest.engine import BacktestEngine

    result = BacktestEngine.from_config(
        _config(),
        bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "2000.0")],
        strategy=BuyOneGcStrategy(),
    ).run()

    assert result.final_account.cash["USD"] == Decimal("800000.0")


def test_one_order_strategy_populates_trade_ledger() -> None:
    from qts.backtest.engine import BacktestEngine

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    result = BacktestEngine.from_config(
        _config(),
        bars=[_bar(start)],
        strategy=BuyOneGcStrategy(),
    ).run()

    assert len(result.report.trade_ledger) == 1
    row = result.report.trade_ledger[0]
    assert row.order_id == "bt-000001"
    assert row.instrument_id == "FUTURE.CME.GC.GCQ0"
    assert row.side == "buy"
    assert row.quantity == Decimal("1")
    assert row.fill_price == Decimal("2000.0")
    assert row.fill_time == start + timedelta(minutes=1)
    assert row.source_bar_time == start


def test_warmup_updates_indicators_before_trading_starts() -> None:
    from qts.backtest.engine import BacktestEngine

    class SmaStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("GCQ0")
            self.sma = ctx.indicator.sma(self.asset, window=2)
            self.ready_on_first_trading_bar = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            if isinstance(bar, Bar) and bar.end_time >= datetime(2026, 1, 2, 14, 33, tzinfo=UTC):
                self.ready_on_first_trading_bar = self.sma.ready

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    strategy = SmaStrategy()
    BacktestEngine.from_config(
        replace(_config(warmup_bars=2), end=start + timedelta(minutes=3)),
        bars=[
            _bar(start, "2000.0"),
            _bar(start + timedelta(minutes=1), "2001.0"),
            _bar(start + timedelta(minutes=2), "2002.0"),
        ],
        strategy=strategy,
    ).run()

    assert strategy.ready_on_first_trading_bar is True


def _load_runner_script() -> ModuleType:
    module_path = Path("scripts/run_research_backtest.py")
    spec = importlib.util.spec_from_file_location("run_research_backtest_script", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fixture_historical(root: Path) -> None:
    (root / "chains").mkdir(parents=True)
    (root / "data").mkdir(parents=True)
    shutil.copyfile(Path("historical/chains/GC.json"), root / "chains" / "GC.json")
    shutil.copyfile(Path("historical/chains/SI.json"), root / "chains" / "SI.json")
    _write_fixture_csv(root / "data" / "gc.csv", "GCQ0", ["2000.0", "2001.0", "2002.0"])
    _write_fixture_csv(root / "data" / "si.csv", "SIN0", ["20.0", "19.0", "18.0"])


def _write_fixture_csv(path: Path, symbol: str, closes: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        for index, close in enumerate(closes):
            writer.writerow(
                {
                    "ts_event": f"2010-06-06T22:0{index}:00.000000000Z",
                    "rtype": "33",
                    "publisher_id": "1",
                    "instrument_id": str(index + 1),
                    "open": close,
                    "high": close,
                    "low": close,
                    "close": close,
                    "volume": "1",
                    "symbol": symbol,
                }
            )


def _write_fixture_config(path: Path, historical_root: Path) -> None:
    path.write_text(
        f"""
dataset_root: {historical_root}
roots: [GC, SI]
symbols: [GCQ0, SIN0]
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:03:00Z"
timeframe: 1m
initial_cash: "1000000"
strategy_class: "examples.strategies.gc_si_momentum:GcSiMomentumStrategy"
strategy_params:
  symbols: [GCQ0, SIN0]
  short_window: 1
  long_window: 2
cost_model:
  fixed_commission_per_contract: "0"
  slippage_bps: "0"
risk_config:
  max_notional: "100000000"
warmup_bars: 0
""",
        encoding="utf-8",
    )


def test_research_backtest_runner_supports_non_chain_static_symbol_dataset(
    tmp_path: Path,
) -> None:
    from qts.backtest.research_runner import run_research_backtest

    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    _write_fixture_csv(historical_root / "data" / "equity.csv", "AAPL", ["150.0"])
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        f"""
dataset_root: {historical_root}
roots: [EQUITY]
symbols: [AAPL]
instrument_ids:
  AAPL: EQUITY.US.NASDAQ.AAPL
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:01:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_research_backtest_gc_si:BuyOneAaplStrategy"
risk_config:
  max_notional: "100000000"
""",
        encoding="utf-8",
    )

    run = run_research_backtest(config_path, output_dir=tmp_path / "runs")

    assert run.result.fills[0].instrument_id == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert run.dataset_stats["EQUITY"]["bars_emitted"] == 1


def test_research_backtest_runner_writes_report_from_fixture_config(tmp_path: Path) -> None:
    from qts.backtest.research_runner import run_research_backtest

    historical_root = tmp_path / "historical"
    config_path = tmp_path / "backtest.yaml"
    output_dir = tmp_path / "runs"
    _write_fixture_historical(historical_root)
    _write_fixture_config(config_path, historical_root)

    run = run_research_backtest(config_path, output_dir=output_dir)

    payload = json.loads(run.report_path.read_text(encoding="utf-8"))
    assert run.report_path.parent == output_dir
    assert payload["report_hash"] == run.result.report_hash
    assert payload["processed_bars"] == 6
    assert payload["trade_ledger"]


def test_research_backtest_cli_runs_fixture_config(tmp_path: Path) -> None:
    historical_root = tmp_path / "historical"
    config_path = tmp_path / "backtest.yaml"
    output_dir = tmp_path / "runs"
    _write_fixture_historical(historical_root)
    _write_fixture_config(config_path, historical_root)
    module = _load_runner_script()
    main = cast(Any, module).main

    exit_code = main(["--config", str(config_path), "--output-dir", str(output_dir)])

    assert exit_code == 0
    json_files = list(output_dir.glob("bt-*.json"))
    assert len([path for path in json_files if not path.name.endswith(".summary.json")]) == 1
    assert len([path for path in json_files if path.name.endswith(".summary.json")]) == 1
