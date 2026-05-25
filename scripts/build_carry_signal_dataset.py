"""Build a calendar-spread carry signal CSV from configured historical futures."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.carry_signal import (
    calendar_spread_carry_signal_rows,
    write_carry_signal_csv,
)
from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig
from qts.registry.providers.exchange_calendar_provider import ExchangeCalendarProvider


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-config", required=True, type=Path)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--symbol-template", default="{root}_CARRY")
    parser.add_argument("--instrument-template", default="RESEARCH.CARRY.{root}")
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args()

    catalog = HistoricalCatalog.load(
        HistoricalCatalogLoadConfig.from_historical_market_data_config(
            args.data_config,
            catalog=args.catalog,
            roots=tuple(args.roots),
        )
    )
    rows = []
    for root in catalog.roots:
        dataset = catalog.datasets[root]
        if dataset.chain is None:
            raise ValueError(f"carry signal generation requires chain metadata for root: {root}")
        output_symbol = args.symbol_template.format(root=root)
        output_instrument = InstrumentId(args.instrument_template.format(root=root))
        rows.extend(
            calendar_spread_carry_signal_rows(
                root=root,
                csv_path=dataset.csv_path,
                chain=dataset.chain,
                output_symbol=output_symbol,
                output_instrument_id=output_instrument,
                session_offset=ExchangeCalendarProvider(
                    dataset.chain.trading_calendar
                ).session_offset,
                start=_parse_datetime(args.start),
                end=_parse_datetime(args.end),
            )
        )
    rows_written = write_carry_signal_csv(args.output, rows)
    print(f"wrote {rows_written} carry signal rows to {args.output}")
    return 0


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


if __name__ == "__main__":
    raise SystemExit(main())
