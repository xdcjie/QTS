from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.indicators.session_regime import SessionRegimeGateConfig, TrailingSessionRegimeGate

_GC_INSTRUMENT = InstrumentId("FUTURE.CME.GC.GCG6")
_SI_INSTRUMENT = InstrumentId("FUTURE.CME.SI.SIH6")


def test_trailing_session_regime_gate_uses_completed_sessions_only() -> None:
    gate = TrailingSessionRegimeGate(
        SessionRegimeGateConfig(
            rule="hard_churn225",
            symbols=("GC", "SI"),
            lookback_sessions=1,
            min_history_sessions=1,
            unready_policy="allow",
        )
    )

    for symbol in ("GC", "SI"):
        _feed_session(
            gate,
            symbol,
            session="2026-05-20",
            open_="100",
            high="103",
            low="100",
            close="100.5",
        )
        _feed_session(
            gate,
            symbol,
            session="2026-05-21",
            open_="100.5",
            high="103.5",
            low="100.5",
            close="101.0",
        )

    assert gate.allows_new_entries()

    for symbol in ("GC", "SI"):
        _feed_session(
            gate,
            symbol,
            session="2026-05-22",
            open_="101.0",
            high="101.2",
            low="101.0",
            close="101.1",
        )

    assert not gate.allows_new_entries()


def test_hard14_ccvol17_allows_high_close_to_close_volatility() -> None:
    gate = TrailingSessionRegimeGate(
        SessionRegimeGateConfig(
            rule="hard14_ccvol17",
            symbols=("GC", "SI"),
            lookback_sessions=2,
            min_history_sessions=2,
        )
    )

    for symbol in ("GC", "SI"):
        _feed_session(
            gate, symbol, session="2026-05-20", open_="100", high="103", low="100", close="100"
        )
        _feed_session(
            gate, symbol, session="2026-05-21", open_="100", high="104", low="100", close="104"
        )
        _feed_session(
            gate, symbol, session="2026-05-22", open_="104", high="107.12", low="100", close="100"
        )
        _feed_session(
            gate, symbol, session="2026-05-23", open_="100", high="100", low="100", close="100"
        )

    assert gate.allows_new_entries()


def _feed_session(
    gate: TrailingSessionRegimeGate,
    symbol: str,
    *,
    session: str,
    open_: str,
    high: str,
    low: str,
    close: str,
) -> None:
    gate.update_bar(
        symbol,
        _bar(symbol, session=session, open_=open_, high=high, low=low, close=close),
    )


def _bar(
    symbol: str,
    *,
    session: str,
    open_: str,
    high: str,
    low: str,
    close: str,
) -> Bar:
    session_date = datetime.fromisoformat(session).date()
    start = datetime(
        session_date.year,
        session_date.month,
        session_date.day,
        14,
        0,
        tzinfo=UTC,
    )
    return Bar(
        instrument_id=_GC_INSTRUMENT if symbol == "GC" else _SI_INSTRUMENT,
        start_time=start,
        end_time=start + timedelta(minutes=15),
        timeframe="15m",
        session_id=session,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal("1000"),
        is_complete=True,
    )
