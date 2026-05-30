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

from qts.core.ids import InstrumentId
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS
from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar
from qts.runtime.config import (
    BacktestCostModel,
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
)
from qts.strategy_sdk import Strategy

from tests.support.backtest_streaming import capture_stream_result, run_engine_streaming

# Multiplier/ledger/replay/roll tests assert single decision-bar fills, which is
# fill-policy independent. Pin the optimistic same-bar policy so the decision
# bar fills in place rather than deferring under the next_bar_open default.
_SAME_BAR = ExecutionTimingModel.research_only()


def _config(*, warmup_bars: int = 0) -> BacktestRuntimeConfig:
    return BacktestRuntimeConfig(
        market_data=BacktestMarketDataReference(
            config_path=Path("configs/data/historical.local.yaml"),
            catalog="research_futures",
        ),
        roots=("GC",),
        symbols=("GCQ0",),
        start=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        end=datetime(2026, 1, 2, 14, 35, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("1000000"),
        strategy_class="tests.integration.test_backtest_gc_si:BuyOneGcStrategy",
        strategy_params={},
        cost_model=BacktestCostModel(),
        risk_config=BacktestRiskConfig(max_notional=Decimal("100000000")),
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


class RollingGcStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.future("GC")

    def on_bar(self, ctx: Any, bar: object) -> None:
        ctx.target_quantity(self.asset, Decimal("1"))


def test_backtest_engine_runs_from_config_with_deterministic_run_id(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestEngine

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start), _bar(start + timedelta(minutes=1), "2001.0")]

    left = run_engine_streaming(
        BacktestEngine.from_config(_config(), bars=bars, strategy=BuyOneGcStrategy()),
        tmp_path / "left",
    )
    right = run_engine_streaming(
        BacktestEngine.from_config(_config(), bars=bars, strategy=BuyOneGcStrategy()),
        tmp_path / "right",
    )

    assert left.result.config_hash == _config().config_hash
    assert left.result.run_id == right.result.run_id
    assert left.manifest["config_hash"] == _config().config_hash
    assert left.manifest["runtime_topology"]["mode"] == "backtest"
    assert left.manifest["runtime_topology"]["topology_hash"].startswith("sha256:")


def test_backtest_engine_from_config_does_not_require_chain_for_static_instrument_ids(
    tmp_path: Path,
) -> None:
    from qts.backtest.engine import BacktestEngine

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    config = BacktestRuntimeConfig(
        market_data=BacktestMarketDataReference(
            config_path=Path("configs/data/historical.local.yaml"),
            catalog="research_futures",
        ),
        roots=("EQUITY",),
        symbols=("AAPL",),
        instrument_ids={"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")},
        start=start,
        end=start + timedelta(minutes=1),
        timeframe="1m",
        initial_cash=Decimal("100000"),
        strategy_class="tests.integration.test_backtest_gc_si:BuyOneAaplStrategy",
        risk_config=BacktestRiskConfig(max_notional=Decimal("100000000")),
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

    captured = run_engine_streaming(
        BacktestEngine.from_config(
            config,
            bars=[bar],
            strategy=BuyOneAaplStrategy(),
            execution_timing=_SAME_BAR,
        ),
        tmp_path / "static-instrument",
    )

    assert captured.fills[0]["instrument_id"] == "EQUITY.US.NASDAQ.AAPL"
    assert captured.result.final_account.cash["USD"] == Decimal("99850")


def test_warmup_bars_call_strategy_but_do_not_place_orders(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestEngine

    class WarmupTargetStrategy(BuyOneGcStrategy):
        pass

    captured = run_engine_streaming(
        BacktestEngine.from_config(
            _config(warmup_bars=1),
            bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))],
            strategy=WarmupTargetStrategy(),
        ),
        tmp_path / "warmup",
    )
    result = captured.result

    assert captured.orders == ()
    assert result.warmup_bars == 1
    assert result.trading_bars == 0
    assert captured.manifest["warmup_bars"] == 1


def test_strategy_finalize_runs_once_and_finalize_intents_are_ignored(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestEngine

    class FinalizeStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("GCQ0")
            self.finalized = 0

        def finalize(self, ctx: Any) -> None:
            self.finalized += 1
            ctx.target_quantity(self.asset, Decimal("1"))

    strategy = FinalizeStrategy()
    captured = run_engine_streaming(
        BacktestEngine.from_config(
            _config(),
            bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))],
            strategy=strategy,
        ),
        tmp_path / "finalize",
    )

    assert strategy.finalized == 1
    assert captured.orders == ()


def test_futures_multiplier_affects_backtest_fill_cash(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestEngine

    result = run_engine_streaming(
        BacktestEngine.from_config(
            _config(),
            bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "2000.0")],
            strategy=BuyOneGcStrategy(),
            contract_multipliers={
                InstrumentId("FUTURE.CME.GC.GCQ0"): Decimal("100"),
            },
            execution_timing=_SAME_BAR,
        ),
        tmp_path / "multiplier",
    ).result

    assert result.final_account.cash["USD"] == Decimal("800000.0")


def test_one_order_strategy_populates_trade_ledger(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestEngine

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        BacktestEngine.from_config(
            _config(),
            bars=[_bar(start)],
            strategy=BuyOneGcStrategy(),
            execution_timing=_SAME_BAR,
        ),
        tmp_path / "trade-ledger",
    )

    assert len(captured.trade_ledger) == 1
    row = captured.trade_ledger[0]
    assert row["order_id"] == "bt-000001"
    assert row["instrument_id"] == "FUTURE.CME.GC.GCQ0"
    assert row["side"] == "buy"
    assert Decimal(row["quantity"]) == Decimal("1")
    assert Decimal(row["fill_price"]) == Decimal("2000.0")
    assert datetime.fromisoformat(row["fill_time"]) == start + timedelta(minutes=1)
    assert datetime.fromisoformat(row["source_bar_time"]) == start


def test_warmup_updates_indicators_before_trading_starts(tmp_path: Path) -> None:
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
    run_engine_streaming(
        BacktestEngine.from_config(
            replace(_config(warmup_bars=2), end=start + timedelta(minutes=3)),
            bars=[
                _bar(start, "2000.0"),
                _bar(start + timedelta(minutes=1), "2001.0"),
                _bar(start + timedelta(minutes=2), "2002.0"),
            ],
            strategy=strategy,
        ),
        tmp_path / "indicator-warmup",
    )

    assert strategy.ready_on_first_trading_bar is True


def _load_runner_script() -> ModuleType:
    module_path = Path("scripts/run_backtest.py")
    spec = importlib.util.spec_from_file_location("run_backtest_script", module_path)
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


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _fixture_row(
    ts_event: str,
    symbol: str,
    close: str,
    *,
    volume: str,
) -> dict[str, str]:
    return {
        "ts_event": ts_event,
        "rtype": "33",
        "publisher_id": "1",
        "instrument_id": symbol,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": volume,
        "symbol": symbol,
    }


def _write_fixture_config(path: Path, historical_root: Path) -> None:
    data_config_path = path.with_name("historical.local.yaml")
    _write_project_historical_config(data_config_path, historical_root)
    path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research_futures
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


def _write_project_historical_config(path: Path, historical_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {historical_root}
      bars_dir: data
      chains_dir: chains
      bars_file_template: "{{root_lower}}.csv"
      chain_file_template: "{{root}}.json"
      defaults:
        exchange_timezone: US/Eastern
        timezone_policy: source_utc_exchange_sessions
        normalization: raw
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          bars:
            - timeframe: 1m
        SI:
          asset_class: future
          exchange: CME
          bars:
            - timeframe: 1m
""",
        encoding="utf-8",
    )


def _write_catalog_backtest_config(path: Path, data_config_path: Path) -> None:
    path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research_futures
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


def test_backtest_runner_supports_non_chain_static_symbol_dataset(
    tmp_path: Path,
) -> None:
    from qts.backtest.runner import run_backtest

    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    _write_fixture_csv(historical_root / "data" / "equity.csv", "AAPL", ["150.0"])
    data_config_path = tmp_path / "historical.local.yaml"
    data_config_path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {historical_root}
      bars_dir: data
      chains_dir: chains
  catalogs:
    research:
      store: local_csv
      datasets:
        EQUITY:
          asset_class: equity
          bars:
            - file: equity.csv
              timeframe: 1m
""",
        encoding="utf-8",
    )
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research
roots: [EQUITY]
symbols: [AAPL]
instrument_ids:
  AAPL: EQUITY.US.NASDAQ.AAPL
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:01:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_backtest_gc_si:BuyOneAaplStrategy"
fill_policy: same_bar_close
optimistic_fill_waiver: true
risk_config:
  max_notional: "100000000"
""",
        encoding="utf-8",
    )

    run = run_backtest(config_path, output_dir=tmp_path / "runs")
    captured = capture_stream_result(run.result)

    assert captured.fills[0]["instrument_id"] == "EQUITY.US.NASDAQ.AAPL"
    assert run.result.dataset_metadata[0].instrument_id == InstrumentId("DATASET.EQUITY")
    assert run.dataset_stats["EQUITY"]["bars_emitted"] == 1


def test_backtest_runner_uses_project_historical_data_catalog(
    tmp_path: Path,
) -> None:
    from qts.backtest.runner import run_backtest

    historical_root = tmp_path / "historical"
    data_config_path = tmp_path / "configs" / "data" / "historical.local.yaml"
    config_path = tmp_path / "backtest.yaml"
    _write_fixture_historical(historical_root)
    _write_project_historical_config(data_config_path, historical_root)
    _write_catalog_backtest_config(config_path, data_config_path)

    run = run_backtest(config_path, output_dir=tmp_path / "runs")

    assert run.dataset_stats["GC"]["bars_emitted"] == 3
    assert run.dataset_stats["SI"]["bars_emitted"] == 3
    assert json.loads(run.manifest_path.read_text(encoding="utf-8"))["dataset_metadata"][0][
        "source"
    ] == str(historical_root / "data" / "gc.csv")


def test_backtest_replays_historical_bars_through_market_data_actor(
    tmp_path: Path,
) -> None:
    from qts.backtest.runner import run_backtest

    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    (historical_root / "chains").mkdir()
    shutil.copyfile(Path("historical/chains/GC.json"), historical_root / "chains" / "GC.json")
    _write_fixture_csv(
        historical_root / "data" / "gc.csv",
        "GCQ0",
        ["2000.0", "2001.0", "2002.0", "2003.0", "2004.0"],
    )
    data_config_path = tmp_path / "configs" / "data" / "historical.local.yaml"
    _write_project_historical_config(data_config_path, historical_root)
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research_futures
roots: [GC]
symbols: [GCQ0]
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:05:00Z"
timeframe: 5m
initial_cash: "1000000"
strategy_class: "tests.integration.test_backtest_gc_si:BuyOneGcStrategy"
fill_policy: same_bar_close
optimistic_fill_waiver: true
risk_config:
  max_notional: "100000000"
""",
        encoding="utf-8",
    )

    run = run_backtest(config_path, output_dir=tmp_path / "runs")
    captured = capture_stream_result(run.result)

    assert run.dataset_stats["GC"]["bars_emitted"] == 5
    assert run.result.processed_bars == 1
    assert captured.manifest["processed_bars"] == 1
    assert datetime.fromisoformat(captured.trade_ledger[0]["source_bar_time"]) == datetime(
        2010, 6, 6, 22, 0, tzinfo=UTC
    )
    assert Decimal(captured.fills[0]["price"]) == Decimal("2004.0")


def test_backtest_catalog_chain_resolution_ignores_unneeded_bar_choices(
    tmp_path: Path,
) -> None:
    from qts.backtest.runner import run_backtest

    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    (historical_root / "chains").mkdir()
    shutil.copyfile(Path("historical/chains/GC.json"), historical_root / "chains" / "GC.json")
    _write_fixture_csv(
        historical_root / "data" / "gc.csv",
        "GCQ0",
        ["2000.0", "2001.0", "2002.0", "2003.0", "2004.0"],
    )
    data_config_path = tmp_path / "configs" / "data" / "historical.local.yaml"
    data_config_path.parent.mkdir(parents=True)
    data_config_path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {historical_root}
      bars_dir: data
      chains_dir: chains
      defaults:
        exchange_timezone: US/Eastern
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          chain_file: GC.json
          bars:
            - file: gc.csv
              timeframe: 1m
            - file: gc_daily.csv
              timeframe: 1d
""",
        encoding="utf-8",
    )
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research_futures
roots: [GC]
symbols: [GCQ0]
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:05:00Z"
timeframe: 5m
initial_cash: "1000000"
strategy_class: "tests.integration.test_backtest_gc_si:BuyOneGcStrategy"
fill_policy: same_bar_close
optimistic_fill_waiver: true
risk_config:
  max_notional: "100000000"
""",
        encoding="utf-8",
    )

    run = run_backtest(config_path, output_dir=tmp_path / "runs")

    assert run.dataset_stats["GC"]["bars_emitted"] == 5
    assert run.result.processed_bars == 1


def test_backtest_runner_leaves_market_data_aggregation_to_engine(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    from qts.backtest import runner
    from qts.backtest.runner import run_backtest

    class ForbiddenRunnerMarketDataActor:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("runner must not aggregate market data")

    monkeypatch.setattr(
        runner,
        "MarketDataActor",
        ForbiddenRunnerMarketDataActor,
        raising=False,
    )

    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    (historical_root / "chains").mkdir()
    shutil.copyfile(Path("historical/chains/GC.json"), historical_root / "chains" / "GC.json")
    _write_fixture_csv(
        historical_root / "data" / "gc.csv",
        "GCQ0",
        ["2000.0", "2001.0", "2002.0", "2003.0", "2004.0"],
    )
    data_config_path = tmp_path / "configs" / "data" / "historical.local.yaml"
    _write_project_historical_config(data_config_path, historical_root)
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research_futures
roots: [GC]
symbols: [GCQ0]
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:05:00Z"
timeframe: 5m
initial_cash: "1000000"
strategy_class: "tests.integration.test_backtest_gc_si:BuyOneGcStrategy"
fill_policy: same_bar_close
optimistic_fill_waiver: true
risk_config:
  max_notional: "100000000"
""",
        encoding="utf-8",
    )

    run = run_backtest(config_path, output_dir=tmp_path / "runs")

    assert run.dataset_stats["GC"]["bars_emitted"] == 5
    assert run.result.processed_bars == 1


def test_backtest_runner_resolves_continuous_future_with_first_notice_policy(
    tmp_path: Path,
) -> None:
    from qts.backtest.runner import run_backtest

    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    (historical_root / "chains").mkdir()
    shutil.copyfile(Path("historical/chains/GC.json"), historical_root / "chains" / "GC.json")
    _write_rows(
        historical_root / "data" / "gc.csv",
        [
            _fixture_row("2010-06-06T22:00:00.000000000Z", "GCN0", "100", volume="100"),
            _fixture_row("2010-06-06T22:00:00.000000000Z", "GCQ0", "110", volume="1"),
            _fixture_row("2010-06-06T22:01:00.000000000Z", "GCN0", "101", volume="1"),
            _fixture_row("2010-06-06T22:01:00.000000000Z", "GCQ0", "111", volume="100"),
        ],
    )
    data_config_path = tmp_path / "historical.local.yaml"
    _write_project_historical_config(data_config_path, historical_root)
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research_futures
roots: [GC]
symbols: [GC]
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:02:00Z"
timeframe: 1m
initial_cash: "1000000"
strategy_class: "tests.integration.test_backtest_gc_si:RollingGcStrategy"
fill_policy: same_bar_close
optimistic_fill_waiver: true
roll_policy:
  enabled: true
  method: first_notice_date
  roll_sessions_before_first_notice: 3
risk_config:
  max_notional: "100000000"
""",
        encoding="utf-8",
    )

    run = run_backtest(config_path, output_dir=tmp_path / "runs")
    captured = capture_stream_result(run.result)

    assert [fill["instrument_id"] for fill in captured.fills] == [
        "FUTURE.CME.GC.GCQ0",
    ]
    assert [fill["side"] for fill in captured.fills] == [
        "buy",
    ]
    assert [Decimal(fill["price"]) for fill in captured.fills] == [
        Decimal("110"),
    ]
    assert run.result.final_account.positions[
        InstrumentId("FUTURE.CME.GC.GCQ0")
    ].quantity == Decimal("1")
    assert run.dataset_stats["GC"]["bars_emitted"] == 2
    assert run.dataset_stats["GC"]["contracts_excluded"] == 2


def test_backtest_runner_writes_artifacts_from_fixture_config(tmp_path: Path) -> None:
    from qts.backtest.runner import run_backtest

    historical_root = tmp_path / "historical"
    config_path = tmp_path / "backtest.yaml"
    output_dir = tmp_path / "runs"
    _write_fixture_historical(historical_root)
    _write_fixture_config(config_path, historical_root)

    run = run_backtest(config_path, output_dir=output_dir)
    captured = capture_stream_result(run.result)

    assert run.manifest_path.parent == output_dir
    assert captured.manifest["report_hash"] == run.result.report_hash
    assert captured.manifest["processed_bars"] == 6
    assert captured.trade_ledger


def test_backtest_cli_runs_fixture_config(tmp_path: Path) -> None:
    historical_root = tmp_path / "historical"
    config_path = tmp_path / "backtest.yaml"
    output_dir = tmp_path / "runs"
    _write_fixture_historical(historical_root)
    _write_fixture_config(config_path, historical_root)
    module = _load_runner_script()
    main = cast(Any, module).main

    exit_code = main(["--config", str(config_path), "--output-dir", str(output_dir)])

    assert exit_code == 0
    assert len(list(output_dir.glob("bt-*.manifest.json"))) == 1
    assert len(list(output_dir.glob("bt-*.summary.json"))) == 1
    assert len(list(output_dir.glob("bt-*.equity_curve.ndjson"))) == 1


def test_backtest_writes_partitioned_artifacts(tmp_path: Path) -> None:
    from qts.backtest.runner import run_backtest

    historical_root = tmp_path / "historical"
    config_path = tmp_path / "backtest.yaml"
    output_dir = tmp_path / "runs"
    _write_fixture_historical(historical_root)
    _write_fixture_config(config_path, historical_root)

    run = run_backtest(config_path, output_dir=output_dir)

    manifest = json.loads(run.manifest_path.read_text(encoding="utf-8"))
    summary = json.loads(run.summary_path.read_text(encoding="utf-8"))
    assert run.processed_bars == 6
    assert manifest["processed_bars"] == 6
    assert summary["processed_bars"] == 6
    assert manifest["report_hash"] == run.report_hash
    assert summary["report_hash"] == run.report_hash
    assert set(run.artifact_paths) == {
        "events",
        "orders",
        "fills",
        "trade_ledger",
        "equity_curve",
        "statistics",
    }
    assert manifest["artifacts"]["equity_curve"]["rows"] == 6
    assert manifest["artifacts"]["orders"]["rows"] == manifest["artifacts"]["fills"]["rows"]
    assert manifest["artifacts"]["fills"]["rows"] == manifest["artifacts"]["trade_ledger"]["rows"]
    for artifact in manifest["artifacts"].values():
        assert Path(artifact["path"]).exists()
        assert artifact["sha256"].startswith("sha256:")
