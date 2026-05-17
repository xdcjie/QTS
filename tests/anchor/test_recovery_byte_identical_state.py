"""Anchor: replaying persisted fill events reconstructs byte-identical account state.

Domain fact: deterministic replay underpins backtest/live parity. After a
crash mid-run, replaying persisted fills + applying the snapshot store must
yield exactly the same AccountSnapshot the original run produced; otherwise
parity is hypothetical and live recovery cannot be trusted.

Owner: existing ``qts.runtime.state_recovery`` (the implementation) plus
``AccountActor.restore`` and the manifest event stream.

Forbidden shortcut: comparing string representations rather than structural
snapshots; allowing "rounding" differences in cash or holdings PnL.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.market_data import Bar
from qts.domain.orders import OrderSide
from qts.execution.order_manager import OrderFill
from qts.runtime.actors.account_actor import AccountActor, ApplyFill

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


def test_replaying_fills_reproduces_byte_identical_account_state(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.strategy_sdk import Strategy

    class HoldAndCloseStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.opened = False
            self.closed = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            if not self.opened:
                ctx.target_quantity(self.asset, Decimal("5"))
                self.opened = True
            elif not self.closed:
                ctx.close(self.asset)
                self.closed = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        BacktestEngine(
            strategy=HoldAndCloseStrategy(),
            bars=[
                _bar(start, "100"),
                _bar(start + timedelta(minutes=1), "102"),
                _bar(start + timedelta(minutes=2), "104"),
            ],
            initial_cash=Decimal("100000"),
        ),
        tmp_path / "recovery-run",
    )
    original = captured.result.final_account

    # Replay only the fills from the manifest event stream through a fresh
    # AccountActor. Cash/holdings must match the original snapshot exactly.
    recovered = AccountActor(
        initial_cash={"USD": Decimal("100000")},
        account_id=AccountId("backtest-account"),
    )
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    for fill_event in (e for e in captured.fills if "fill_id" in e):
        recovered.handle(
            ApplyFill(
                fill=OrderFill(
                    fill_id=str(fill_event["fill_id"]),
                    order_id=OrderId(str(fill_event["order_id"])),
                    instrument_id=instrument_id,
                    side=OrderSide(fill_event["side"]),
                    quantity=Decimal(str(fill_event["quantity"])),
                    price=Decimal(str(fill_event["price"])),
                    commission=Decimal(str(fill_event["commission"])),
                    slippage=Decimal(str(fill_event["slippage"])),
                    account_id=AccountId("backtest-account"),
                ),
                currency="USD",
                multiplier=Decimal("1"),
            )
        )

    recovered_snapshot = recovered.snapshot()

    # Byte-identical: same cash, same holdings quantities, same realized PnL.
    assert dict(recovered_snapshot.cash) == dict(original.cash)
    assert set(recovered_snapshot.holdings.keys()) == set(original.holdings.keys())
    for instrument, original_holding in original.holdings.items():
        replayed_holding = recovered_snapshot.holdings[instrument]
        assert replayed_holding.quantity == original_holding.quantity
        assert replayed_holding.average_cost == original_holding.average_cost
        assert replayed_holding.realized_pnl == original_holding.realized_pnl


def test_account_actor_snapshot_restore_round_trip_is_byte_identical() -> None:
    """AccountActor.restore from its own snapshot reproduces the state."""
    actor = AccountActor(
        initial_cash={"USD": Decimal("50000")},
        account_id=AccountId("acct-1"),
    )
    instrument = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    for i, (side, price) in enumerate(
        [(OrderSide.BUY, Decimal("100")), (OrderSide.SELL, Decimal("105"))]
    ):
        actor.handle(
            ApplyFill(
                fill=OrderFill(
                    fill_id=f"f-{i}",
                    order_id=OrderId(f"ord-{i}"),
                    instrument_id=instrument,
                    side=side,
                    quantity=Decimal("3"),
                    price=price,
                    account_id=AccountId("acct-1"),
                ),
                currency="USD",
                multiplier=Decimal("1"),
            )
        )

    snapshot = actor.snapshot()
    restored = AccountActor.restore(snapshot)
    restored_snapshot = restored.snapshot()

    assert dict(restored_snapshot.cash) == dict(snapshot.cash)
    assert set(restored_snapshot.holdings.keys()) == set(snapshot.holdings.keys())
    for instrument_id, holding in snapshot.holdings.items():
        rh = restored_snapshot.holdings[instrument_id]
        assert rh.quantity == holding.quantity
        assert rh.average_cost == holding.average_cost
        assert rh.realized_pnl == holding.realized_pnl
    assert restored_snapshot.seen_fill_ids == snapshot.seen_fill_ids
