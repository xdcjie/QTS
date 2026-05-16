from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy


class BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.done = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.done:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.done = True


@dataclass(frozen=True, slots=True)
class FakePdfExporter:
    def export(self, html_path: Path, pdf_path: Path) -> Path:
        pdf_path.write_bytes(b"%PDF-1.4\n% fake integration pdf\n")
        return pdf_path


def test_analyst_report_generator_writes_html_and_pdf_from_completed_backtest(
    tmp_path: Path,
) -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.reporting.backtest_analyst import AnalystBacktestReportGenerator

    run_dir = tmp_path / "run"
    result = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=[
            _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "100"),
            _bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC), "101"),
        ],
        initial_cash=Decimal("100000"),
    ).run_streaming(run_dir)
    summary_path = run_dir / f"{result.run_id.value}.summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "run_id": result.run_id.value,
                "status": "completed",
                "manifest_path": str(result.manifest_path),
                "processed_bars": result.processed_bars,
                "warmup_bars": result.warmup_bars,
                "trading_bars": result.trading_bars,
                "report_hash": result.report_hash,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    generated = AnalystBacktestReportGenerator(pdf_exporter=FakePdfExporter()).generate(
        summary_path,
    )

    assert generated.html_path.exists()
    assert generated.pdf_path.exists()
    html = generated.html_path.read_text(encoding="utf-8")
    assert "VWAP Backtest Analyst Report" in html
    assert result.run_id.value in html
    assert result.report_hash in html


def _bar(start: datetime, close: str) -> Bar:
    from qts.core.ids import InstrumentId

    price = Decimal(close)
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal("100"),
        is_complete=True,
    )
