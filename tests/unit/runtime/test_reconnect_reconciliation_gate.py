from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from qts.core.ids import AccountId
from qts.runtime.state import RuntimeSessionState

if TYPE_CHECKING:
    from qts.runtime.session import RuntimeSession

from tests.unit.runtime.test_runtime_session import (
    _bar,
    _BuyOnceStrategy,
    _InstrumentContext,
    _portfolio_view,
    _RecordingExecutionAdapter,
    _RecordingReconnectReconciliation,
    _registry,
)


def test_disconnect_degrades_runtime_and_blocks_new_orders() -> None:
    session, adapter, _reconciliation = _session_with_reconciliation(
        _RecordingReconnectReconciliation(passed=True)
    )

    session.start()
    disconnected_state = session.on_broker_disconnect(reason="socket closed")
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert disconnected_state is RuntimeSessionState.DEGRADED
    assert result.reason_code == "RUNTIME_DEGRADED"
    assert adapter.seen == []


def test_reconnect_does_not_resume_orders_before_reconciliation() -> None:
    reconciliation = _RecordingReconnectReconciliation(passed=False, reason_code="DRIFT")
    session, adapter, _reconciliation = _session_with_reconciliation(reconciliation)

    session.start()
    session.on_broker_disconnect(reason="socket closed")
    reconnect_state = session.on_broker_reconnect(reason="socket restored")
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert reconnect_state is RuntimeSessionState.DEGRADED
    assert result.reason_code == "RUNTIME_DEGRADED"
    assert adapter.seen == []


def test_reconnect_resubscribes_market_data() -> None:
    reconciliation = _RecordingReconnectReconciliation(passed=True)
    session, _adapter, _reconciliation = _session_with_reconciliation(reconciliation)

    session.start()
    session.on_broker_disconnect(reason="socket closed")
    session.on_broker_reconnect(reason="socket restored")

    assert reconciliation.calls[0] == "market_data"


def test_reconnect_reconciles_open_orders_positions_cash() -> None:
    reconciliation = _RecordingReconnectReconciliation(passed=True)
    session, _adapter, _reconciliation = _session_with_reconciliation(reconciliation)

    session.start()
    session.on_broker_disconnect(reason="socket closed")
    session.on_broker_reconnect(reason="socket restored")

    assert reconciliation.calls == [
        "market_data",
        "open_orders",
        "positions",
        "executions",
        "account_summary",
        "reconcile",
    ]


def test_reconnect_with_drift_stays_degraded() -> None:
    reconciliation = _RecordingReconnectReconciliation(
        passed=False,
        reason_code="RECONCILIATION_DRIFT",
        drift_count=1,
    )
    session, adapter, _reconciliation = _session_with_reconciliation(reconciliation)

    session.start()
    session.on_broker_disconnect(reason="socket closed")
    reconnect_state = session.on_broker_reconnect(reason="socket restored")
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert reconnect_state is RuntimeSessionState.DEGRADED
    assert result.reason_code == "RUNTIME_DEGRADED"
    assert adapter.seen == []


def _session_with_reconciliation(
    reconciliation: _RecordingReconnectReconciliation,
) -> tuple[RuntimeSession, _RecordingExecutionAdapter, _RecordingReconnectReconciliation]:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.broker_startup import validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    account_id = AccountId("acct-reconnect-m4")
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.PAPER_BROKER,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DUP1234567",
        )
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.PAPER_BROKER,
            execution_environment=ExecutionEnvironment.BROKER,
            startup_decision=startup_decision,
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
            broker_reconnect_reconciliation=reconciliation,
        )
    )
    return session, adapter, reconciliation
