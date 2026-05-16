from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from qts.core.ids import AccountId, InstrumentId
from qts.data.permissions import MarketDataPermissionEvent, MarketDataPermissionState
from qts.data.sources.streaming_market_data_source import StreamingMarketDataDegradation
from qts.data.subscriptions import LogicalSubscriptionKey

if TYPE_CHECKING:
    from qts.runtime.session import RuntimeSession, RuntimeSessionResult

from tests.unit.runtime.test_runtime_session import (
    _bar,
    _BuyOnceStrategy,
    _InstrumentContext,
    _live_capital_request,
    _portfolio_view,
    _RecordingExecutionAdapter,
    _RecordingSink,
    _registry,
)


def _live_session(
    *,
    account_id: str = "acct-md-acceptance",
) -> tuple[RuntimeSession, _RecordingExecutionAdapter, _RecordingSink]:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.broker_startup import validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    resolved_account_id = AccountId(account_id)
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="DU1234567",
            operator_signoff_id=f"ops-{account_id}",
        ),
        live_capital_request=_live_capital_request(account_id=resolved_account_id),
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.LIVE,
            execution_environment=ExecutionEnvironment.BROKER,
            startup_decision=startup_decision,
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=resolved_account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=resolved_account_id,
            sink=sink,
        )
    )
    session.start()
    return session, adapter, sink


def _permission_event(permission_state: MarketDataPermissionState) -> MarketDataPermissionEvent:
    return MarketDataPermissionEvent(
        source_id="ibkr-live-md",
        permission_state=permission_state,
        provider_market_data_type=1,
        request_id=11,
    )


def _stale_event() -> StreamingMarketDataDegradation:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    return StreamingMarketDataDegradation(
        instrument_id=instrument_id,
        subscription=LogicalSubscriptionKey(
            instrument_id=instrument_id,
            requested_timeframe="1m",
        ),
        observed_at=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        age=timedelta(seconds=61),
        max_age=timedelta(seconds=30),
    )


def _run_order_after_permission(
    permission_state: MarketDataPermissionState,
    *,
    account_id: str,
) -> tuple[RuntimeSessionResult, RuntimeSessionResult, _RecordingExecutionAdapter, _RecordingSink]:
    session, adapter, sink = _live_session(account_id=account_id)
    permission_result = session.on_market_data_source_event(_permission_event(permission_state))
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    return permission_result, result, adapter, sink


def _risk_rejection(sink: _RecordingSink) -> dict[str, object]:
    return next(
        event.to_envelope()["payload"]
        for event in sink.events
        if event.kind == "runtime.risk_rejected"
    )


def _runtime_degraded(sink: _RecordingSink) -> dict[str, object]:
    return next(
        event.to_envelope()["payload"] for event in sink.events if event.kind == "runtime.degraded"
    )


def test_live_market_data_permission_allows_order_when_fresh() -> None:
    permission_result, result, adapter, sink = _run_order_after_permission(
        MarketDataPermissionState.LIVE,
        account_id="acct-md-live-fresh",
    )

    assert permission_result.reason_code is None
    assert result.reason_code is None
    assert len(result.orders) == 1
    assert len(adapter.seen) == 1
    assert not [event for event in sink.events if event.kind == "runtime.risk_rejected"]


def test_delayed_market_data_rejects_live_order() -> None:
    permission_result, result, adapter, sink = _run_order_after_permission(
        MarketDataPermissionState.DELAYED,
        account_id="acct-md-delayed",
    )
    degraded = _runtime_degraded(sink)

    assert permission_result.reason_code == "RUNTIME_DEGRADED"
    assert result.reason_code == "RUNTIME_DEGRADED"
    assert result.orders == ()
    assert adapter.seen == []
    assert degraded["reason_code"] == "MARKET_DATA_PERMISSION_ERROR"
    assert degraded["permission_state"] == "delayed"


def test_delayed_frozen_market_data_rejects_live_order() -> None:
    permission_result, result, adapter, sink = _run_order_after_permission(
        MarketDataPermissionState.DELAYED_FROZEN,
        account_id="acct-md-delayed-frozen",
    )
    degraded = _runtime_degraded(sink)

    assert permission_result.reason_code == "RUNTIME_DEGRADED"
    assert result.reason_code == "RUNTIME_DEGRADED"
    assert result.orders == ()
    assert adapter.seen == []
    assert degraded["reason_code"] == "MARKET_DATA_PERMISSION_ERROR"
    assert degraded["permission_state"] == "delayed_frozen"


def test_frozen_market_data_rejects_live_order() -> None:
    permission_result, result, adapter, sink = _run_order_after_permission(
        MarketDataPermissionState.FROZEN,
        account_id="acct-md-frozen",
    )
    degraded = _runtime_degraded(sink)

    assert permission_result.reason_code == "RUNTIME_DEGRADED"
    assert result.reason_code == "RUNTIME_DEGRADED"
    assert result.orders == ()
    assert adapter.seen == []
    assert degraded["reason_code"] == "MARKET_DATA_PERMISSION_ERROR"
    assert degraded["permission_state"] == "frozen"


def test_unavailable_market_data_rejects_order() -> None:
    permission_result, result, adapter, sink = _run_order_after_permission(
        MarketDataPermissionState.UNAVAILABLE,
        account_id="acct-md-unavailable",
    )
    degraded = _runtime_degraded(sink)

    assert permission_result.reason_code == "RUNTIME_DEGRADED"
    assert result.reason_code == "RUNTIME_DEGRADED"
    assert result.orders == ()
    assert adapter.seen == []
    assert degraded["reason_code"] == "MARKET_DATA_PERMISSION_ERROR"
    assert degraded["permission_state"] == "unavailable"


def test_stale_market_data_rejects_order() -> None:
    session, adapter, sink = _live_session(account_id="acct-md-stale")
    session.on_market_data_source_event(_permission_event(MarketDataPermissionState.LIVE))
    session.on_market_data_source_event(_stale_event())

    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    degraded = _runtime_degraded(sink)

    assert result.reason_code == "RUNTIME_DEGRADED"
    assert result.orders == ()
    assert adapter.seen == []
    assert degraded["reason_code"] == "MARKET_DATA_STALE"


def test_market_data_rejection_emits_runtime_event_with_reason_code() -> None:
    session, adapter, sink = _live_session(account_id="acct-md-event-evidence")
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    risk_rejection = _risk_rejection(sink)
    evidence = risk_rejection["evidence"]

    assert result.reason_code is None
    assert result.orders == ()
    assert adapter.seen == []
    assert risk_rejection["reason_code"] == "MARKET_DATA_PERMISSION_UNKNOWN"
    assert isinstance(evidence, dict)
    assert evidence["market_data"] == {"permission_state": None, "stale": False}
