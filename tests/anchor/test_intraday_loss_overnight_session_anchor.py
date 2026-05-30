"""Anchor: the intraday-loss window is keyed on the exchange-local session, not UTC date.

Overnight futures sessions (e.g. COMEX GC/SI ``[18:00 ET, 17:00 ET)``) span two
UTC calendar dates within a single trading session. The intraday-loss window
must persist across the UTC-midnight boundary inside one session, and reset only
when the exchange-local ``session_id`` actually changes.

Regression guard for C4: ``TargetIntentProcessor._session_id_for`` previously
derived the key from ``bar.end_time.date()`` (UTC), which reset the realized-PnL
baseline mid-session and mis-scoped the loss window for overnight instruments.
``docs/domain/market_calendar_and_sessions.md`` forbids deriving the session key
from a UTC date.

The harness instrument is incidental; the behaviour under test (session-key
derivation in the shared runtime intent path) is instrument-agnostic, so the two
bars below carry explicit overnight ``session_id`` values that straddle UTC
midnight.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.risk.intraday_pnl import IntradayPnlCalculator
from qts.risk.rules.intraday_loss_limit import IntradayLossLimitRule

from tests.support.risk_runtime_harness import RiskRuntimeHarness

# One COMEX-style overnight session, labelled by its trade date, with two bars on
# different UTC dates: 18:00 ET (23:00 UTC, prior calendar day) and 20:00 ET
# (01:00 UTC, next calendar day).
_SESSION = "2026-01-06"
_BAR1 = datetime(2026, 1, 5, 23, 0, tzinfo=UTC)
_BAR2_SAME_SESSION = datetime(2026, 1, 6, 1, 0, tzinfo=UTC)


def test_intraday_loss_window_persists_across_utc_midnight_within_one_session() -> None:
    """A loss opened pre-midnight still blocks new orders post-midnight, same session."""
    harness = RiskRuntimeHarness(
        rules=[IntradayLossLimitRule(max_loss=Decimal("50"))],
        multiplier=Decimal("1"),
        initial_cash=Decimal("100000"),
        intraday_pnl_calculator=IntradayPnlCalculator(),
    )

    # 18:00 ET: open a 10-lot long at 100 (flat session start -> intraday pnl 0).
    opened = harness.submit(
        target_quantity="10", when=_BAR1, price="100", session_id=_SESSION
    )
    assert opened.fills

    # 20:00 ET (next UTC date, SAME session): price 90 -> unrealized 10*(90-100)
    # = -100 < -50. The window must NOT have reset across UTC midnight.
    blocked = harness.submit(
        target_quantity="11", when=_BAR2_SAME_SESSION, price="90", session_id=_SESSION
    )
    assert blocked.orders == ()
    assert blocked.risk_decisions[0].reason_code == "INTRADAY_LOSS_LIMIT_EXCEEDED"


def test_intraday_loss_window_resets_only_on_new_session() -> None:
    """A genuinely new session resets the window even on the same UTC date region."""
    harness = RiskRuntimeHarness(
        rules=[IntradayLossLimitRule(max_loss=Decimal("50"))],
        multiplier=Decimal("1"),
        initial_cash=Decimal("100000"),
        intraday_pnl_calculator=IntradayPnlCalculator(),
    )

    harness.submit(target_quantity="10", when=_BAR1, price="100", session_id=_SESSION)
    # Next session at the recovered price 100 -> unrealized 0 -> allowed again.
    recovered = harness.submit(
        target_quantity="11",
        when=_BAR2_SAME_SESSION,
        price="100",
        session_id="2026-01-07",
    )
    assert recovered.orders
