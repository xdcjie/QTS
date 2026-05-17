# Getting Started

A 5-minute path from clone to first ranked backtest. If anything here
no longer matches the code, treat the failing anchor at
`tests/quality/test_getting_started_quickstart.py` as the source of
truth and update the doc.

## 1. Install

This repo uses [uv](https://github.com/astral-sh/uv) for environment
management.

```bash
git clone <repo-url>
cd QTS
uv sync
```

`uv sync` installs the project in editable mode plus dev dependencies.
After it finishes, the `qts` package is importable and the `scripts/`
CLIs run via `uv run python ...`.

## 2. Write a 5-line strategy

The full `examples/strategies/hello_world.py` strategy fits on one
screen:

```python
from decimal import Decimal
from qts.strategy_sdk import Strategy


class HelloWorldStrategy(Strategy):
    """Buy one share on the first bar and hold."""

    def initialize(self, ctx):
        self.asset = ctx.symbol("AAPL")
        self._opened = False

    def on_bar(self, ctx, bar):
        if self._opened:
            return
        ctx.target_quantity(self.asset, Decimal("1"))
        self._opened = True
```

Only the public Strategy SDK is in scope: `Strategy`, `ctx.symbol`,
`ctx.target_quantity`. The SDK boundary anchor
(`tests/anchor/test_strategy_sdk_boundaries.py`) blocks strategies
from reaching into actors, brokers, or risk internals.

## 3. Run a backtest

The shortest possible end-to-end backtest — load the strategy, feed
synthetic bars, write the manifest to a temp directory:

```python
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.backtest.engine import BacktestEngine
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from examples.strategies.hello_world import HelloWorldStrategy

instrument = InstrumentId("EQUITY.US.NASDAQ.AAPL")
start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
bars = [
    Bar(
        instrument_id=instrument,
        start_time=start + timedelta(minutes=i),
        end_time=start + timedelta(minutes=i + 1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(100 + i),
        high=Decimal(100 + i),
        low=Decimal(100 + i),
        close=Decimal(100 + i),
        volume=Decimal("100"),
        is_complete=True,
    )
    for i in range(6)
]

engine = BacktestEngine(
    strategy=HelloWorldStrategy(),
    bars=bars,
    initial_cash=Decimal("100000"),
)
result = engine.run_streaming(Path("runs/hello-world"))
print(result.manifest_path)
```

Run it with `uv run python` (after installing the example as a path
import via the repo root). The integration anchor
`tests/integration/test_hello_world_strategy_runs.py` exercises the
exact same path.

## 4. Read the manifest

`BacktestEngine.run_streaming(output_dir)` writes a manifest JSON file
under `output_dir`. Open it in any text editor — the `statistics`
block holds total return, Sharpe, max drawdown, etc., plus a stable
`manifest_hash` for reproducibility. Two runs of the same strategy on
the same bars must produce identical hashes; if they do not, suspect
non-determinism.

## 5. Sweep parameters with the optimizer

When a single strategy run is not enough, `scripts/run_optimizer.py`
sweeps a parameter grid through the same backtest path:

```bash
uv run python scripts/run_optimizer.py configs/optimizer/quickstart.yaml
```

This prints a ranked table of 4 runs over a 2×2 parameter grid. The
quickstart strategy lives at `examples/strategies/quickstart_optimizer.py`
and the config at `configs/optimizer/quickstart.yaml` — copy them as
a starting template.

## 6. Where to go next

- **Strategy SDK reference** — `docs/strategy_sdk/strategy_api.md`
  covers the full public surface: indicators, factors, target APIs.
- **Architecture** — `docs/architecture/system_overview.md` explains
  the actor + queue runtime that backtest, paper, and live all share.
- **Domain invariants** — `docs/testing/domain_invariants.md` lists
  the cross-cutting rules every strategy and adapter must respect.
- **Run a live-mode paper trade** — `configs/paper.yaml` and
  `scripts/run_paper.py` show the same strategy path through a paper
  broker once you are ready to leave backtest mode.

If you hit a wall, `make check` runs every gate the project enforces;
its output is the canonical "did I break something" signal.
