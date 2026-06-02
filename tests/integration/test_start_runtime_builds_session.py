"""start_runtime builds and starts a real RuntimeSession via the builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.application.services import RuntimeSessionBuilder, RuntimeStartConfig
from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.data.permissions import MarketDataPermissionEvent, MarketDataPermissionState
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderIntent
from qts.domain.risk import OrderRiskRequest
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.broker_startup import validate_live_startup
from qts.runtime.config import BrokerRuntimeConfig
from qts.runtime.control_plane import RuntimeSessionKey, RuntimeSessionRegistry
from qts.runtime.live_capital import (
    LiveCapitalEnablementRequest,
    LiveCapitalOrderDecision,
    OperatorSignoff,
)
from qts.runtime.mode import RuntimeMode
from qts.runtime.session import RuntimeSession
from qts.runtime.state import RuntimeSessionState
from qts.strategy_sdk import Strategy

from tests.support.runtime_launch import runtime_launch_fixture

_INSTRUMENT_ID = InstrumentId("EQUITY.US.NASDAQ.AAPL")


class _BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.done = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.done:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.done = True


def _instrument_registry() -> InstrumentRegistry:
    registry = InstrumentRegistry()
    registry.register(
        "AAPL",
        Instrument(
            instrument_id=_INSTRUMENT_ID,
            asset_class=AssetClass.EQUITY,
            exchange="NASDAQ",
            currency="USD",
            contract_spec=ContractSpec(
                tick_size=Decimal("0.01"),
                lot_size=Decimal("1"),
                multiplier=Decimal("1"),
                settlement=SettlementType.CASH,
                calendar_id="NASDAQ",
            ),
        ),
    )
    return registry


def _bar(start: datetime, *, close: Decimal = Decimal("100")) -> Bar:
    return Bar(
        instrument_id=_INSTRUMENT_ID,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=close,
        high=close,
        low=close,
        close=close,
        volume=Decimal("100"),
        is_complete=True,
    )


def _live_capital_request(*, account_id: AccountId) -> LiveCapitalEnablementRequest:
    return LiveCapitalEnablementRequest(
        operator_signoff=OperatorSignoff(
            operator_id="operator-live",
            reason="integration test live-capital gate",
            risk_approver_id="risk-live",
            engineering_approver_id="engineering-live",
            expires_at=datetime(2099, 12, 31, tzinfo=UTC),
            strategy_ids=("strategy",),
            account_ids=(account_id.value,),
            max_notional_limit=Decimal("100000"),
            allowed_instruments=(_INSTRUMENT_ID.value,),
        ),
        strategy_id="strategy",
        account_id=account_id.value,
        instrument_id=_INSTRUMENT_ID.value,
        requested_notional=Decimal("100"),
    )


def _live_capital_order_decision(
    *,
    startup_decision: Any,
    account_id: AccountId,
) -> LiveCapitalOrderDecision:
    return LiveCapitalOrderDecision(
        runtime_mode=RuntimeMode.LIVE,
        order_submission_permission=startup_decision.order_permission,
        startup_decision_status=startup_decision.status,
        operator_signoff_valid=True,
        market_data_permission="live",
        market_data_freshness="fresh",
        reconciliation_status="clean",
        kill_switch_active=False,
        broker_account_kind="live",
        broker_account_code=account_id.value,
        gateway_port=4001,
    )


@dataclass(slots=True)
class _FillingExecutionAdapter:
    seen: list[OrderIntent] = field(default_factory=list)

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
        bar_time: object | None = None,
    ) -> ExecutionReport:
        _ = account_id, strategy_id, client_order_id, correlation_id, bar_time
        self.seen.append(intent)
        return ExecutionReport(
            report_id=f"{broker_order_id}-filled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=market_price,
            fill_id=f"{broker_order_id}-fill",
        )

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        _ = order_id, account_id, strategy_id, client_order_id, correlation_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancelled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )

    def replace_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        new_quantity: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        _ = order_id, new_quantity, account_id, strategy_id, client_order_id, correlation_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-replaced",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.ACCEPTED,
        )


def test_start_runtime_builds_real_session_when_builder_supplied(tmp_path: Path) -> None:
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            account_id=AccountId("acct-paper"),
            initial_cash={"USD": Decimal("100000")},
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
    )

    # The paper builder wires the mandatory baseline risk floor, never an empty
    # (all-orders-approved) engine: with 100k capital the notional ceiling is 10M.
    risk_engine = builder.dependencies.risk_engine
    over_limit = OrderRiskRequest(
        instrument_id=_INSTRUMENT_ID,
        quantity=Decimal("10000001"),
        price=Decimal("1"),
        multiplier=Decimal("1"),
    )
    assert risk_engine.check(over_limit).approved is False

    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="paper-runtime-1",
    )
    registry = RuntimeSessionRegistry()
    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="start-paper-1",
            reason="build session",
        ),
        session_builder=builder,
        session_registry=registry,
        launch_plan_store=launch.store,
    )

    assert result.status == "started"
    assert result.evidence["launch_plan_verified"] is True
    assert result.evidence["session_constructed"] is True
    assert result.evidence["session_registered"] is True
    assert isinstance(result.session, RuntimeSession)
    assert (
        registry.resolve(RuntimeSessionKey(runtime_instance_id=launch.runtime_instance_id))
        is result.session
    )
    # The session was actually started through the shared lifecycle, not faked.
    assert result.session.state is RuntimeSessionState.RUNNING


def test_start_runtime_builds_paper_broker_session_with_boundary_adapter(tmp_path: Path) -> None:
    account_id = AccountId("acct-paper-broker")
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
    execution_adapter = _FillingExecutionAdapter()
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.PAPER_BROKER,
            account_id=account_id,
            initial_cash={"USD": Decimal("100000")},
            startup_decision=startup_decision,
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
        execution_adapter=execution_adapter,
    )

    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_BROKER,
        runtime_instance_id="paper-broker-runtime-1",
    )
    registry = RuntimeSessionRegistry()
    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_BROKER,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="start-paper-broker-1",
            reason="build broker paper session",
            startup_decision=startup_decision,
        ),
        session_builder=builder,
        session_registry=registry,
        launch_plan_store=launch.store,
    )
    assert result.session is not None

    loop_result = result.session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert result.status == "started"
    assert result.runtime_mode is RuntimeMode.PAPER_BROKER
    assert result.order_submission_enabled is True
    assert result.evidence["launch_plan_verified"] is True
    assert result.evidence["session_constructed"] is True
    assert result.evidence["session_registered"] is True
    assert result.session.state is RuntimeSessionState.RUNNING
    assert len(execution_adapter.seen) == 1
    assert len(loop_result.fills) == 1
    assert result.session.account_snapshot.cash["USD"] == Decimal("99900")


def test_start_runtime_rejects_builder_mode_that_does_not_match_command(tmp_path: Path) -> None:
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
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            account_id=AccountId("acct-paper-sim-mismatch"),
            initial_cash={"USD": Decimal("100000")},
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
    )

    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_BROKER,
        runtime_instance_id="paper-broker-mismatch",
    )
    with pytest.raises(ValueError, match="session builder mode must match command runtime_mode"):
        start_runtime(
            StartRuntimeCommand(
                runtime_mode=RuntimeMode.PAPER_BROKER,
                runtime_instance_id=launch.runtime_instance_id,
                config_ref=launch.config_ref,
                launch_plan_hash=launch.launch_plan_hash,
                operator_id="ops",
                idempotency_key="start-paper-broker-mismatch",
                reason="reject mismatched builder",
                startup_decision=startup_decision,
            ),
            session_builder=builder,
            session_registry=RuntimeSessionRegistry(),
            launch_plan_store=launch.store,
        )


def test_start_runtime_builds_live_observation_session_without_order_submission(
    tmp_path: Path,
) -> None:
    account_id = AccountId("acct-live-observation")
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE_OBSERVATION,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
        )
    )
    execution_adapter = _FillingExecutionAdapter()
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.LIVE_OBSERVATION,
            account_id=account_id,
            initial_cash={"USD": Decimal("100000")},
            startup_decision=startup_decision,
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
        execution_adapter=execution_adapter,
    )

    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.LIVE_OBSERVATION,
        runtime_instance_id="live-observation-runtime-1",
    )
    registry = RuntimeSessionRegistry()
    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.LIVE_OBSERVATION,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="start-live-observation-1",
            reason="build observation session",
            startup_decision=startup_decision,
        ),
        session_builder=builder,
        session_registry=registry,
        launch_plan_store=launch.store,
    )
    assert result.session is not None

    loop_result = result.session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert result.order_submission_enabled is False
    assert result.live_order_submission_enabled is False
    assert result.session.state is RuntimeSessionState.DEGRADED
    assert loop_result.reason_code == "OBSERVATION_ONLY"
    assert loop_result.orders == ()
    assert loop_result.fills == ()
    assert execution_adapter.seen == []


def test_start_runtime_builds_live_session_after_startup_and_market_data_permission(
    tmp_path: Path,
) -> None:
    account_id = AccountId("DU1234567")
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
            operator_signoff_id="ops-approval-1",
        ),
        live_capital_request=_live_capital_request(account_id=account_id),
    )
    execution_adapter = _FillingExecutionAdapter()
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.LIVE,
            account_id=account_id,
            initial_cash={"USD": Decimal("100000")},
            startup_decision=startup_decision,
            live_capital_decision=_live_capital_order_decision(
                startup_decision=startup_decision,
                account_id=account_id,
            ),
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
        execution_adapter=execution_adapter,
    )

    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.LIVE,
        runtime_instance_id="live-runtime-1",
    )
    registry = RuntimeSessionRegistry()
    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.LIVE,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="start-live-1",
            reason="build live session",
            startup_decision=startup_decision,
        ),
        session_builder=builder,
        session_registry=registry,
        launch_plan_store=launch.store,
    )
    assert result.session is not None
    result.session.on_market_data_source_event(
        MarketDataPermissionEvent(
            source_id="ibkr-live-md",
            permission_state=MarketDataPermissionState.LIVE,
            provider_market_data_type=1,
            request_id=11,
        )
    )

    loop_result = result.session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert result.order_submission_enabled is True
    assert result.live_order_submission_enabled is True
    assert result.session.state is RuntimeSessionState.RUNNING
    assert loop_result.reason_code is None
    assert len(execution_adapter.seen) == 1
    assert len(loop_result.fills) == 1
    assert result.session.account_snapshot.cash["USD"] == Decimal("99900")


def test_runtime_builder_requires_last_mile_live_capital_decision_before_live_orders() -> None:
    account_id = AccountId("DU7654321")
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="DU7654321",
            operator_signoff_id="ops-approval-2",
        ),
        live_capital_request=_live_capital_request(account_id=account_id),
    )

    with pytest.raises(ValueError, match="live runtime requires live_capital_decision"):
        RuntimeSessionBuilder.from_runtime_config(
            RuntimeStartConfig(
                runtime_mode=RuntimeMode.LIVE,
                account_id=account_id,
                initial_cash={"USD": Decimal("100000")},
                startup_decision=startup_decision,
            ),
            strategy=_BuyOnceStrategy(),
            instrument_registry=_instrument_registry(),
            execution_adapter=_FillingExecutionAdapter(),
        )


def test_start_runtime_without_builder_reports_unconstructed_session(tmp_path: Path) -> None:
    launch = runtime_launch_fixture(
        tmp_path,
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id="paper-runtime-unbuilt",
    )
    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            runtime_instance_id=launch.runtime_instance_id,
            config_ref=launch.config_ref,
            launch_plan_hash=launch.launch_plan_hash,
            operator_id="ops",
            idempotency_key="start-paper-2",
            reason="accept only",
        ),
        launch_plan_store=launch.store,
    )

    assert result.status == "rejected"
    assert result.evidence["session_constructed"] is False
    assert result.evidence["reason_code"] == "RUNTIME_SESSION_BUILDER_REQUIRED"
    assert result.order_submission_enabled is False
    assert result.live_order_submission_enabled is False
    assert result.session is None
