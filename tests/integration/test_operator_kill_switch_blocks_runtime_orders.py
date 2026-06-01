"""Operator kill-switch via the control plane blocks real runtime orders.

QTS-FINAL-001: an operator kill-switch issued through ``OperationsService`` must
reach the bound ``RuntimeSession`` (via ``RuntimeCommandExecutor``) and actually
halt order submission — not return a 200 no-op. This drives the full operator
path (OperationsService -> RuntimeCommandExecutor -> RuntimeSession) against a
real actor-backed session and asserts subsequent bars submit no new orders.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.application.dto import KillSwitchCommandDTO
from qts.application.services import OperationsService
from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.runtime.actors.account_actor import AccountActor
from qts.runtime.control_plane import (
    RuntimeCommandExecutor,
    RuntimeSessionKey,
    RuntimeSessionRegistry,
)
from qts.runtime.dependencies import RuntimeSessionDependencies
from qts.runtime.session import RuntimeSession

from tests.integration.test_live_kill_switch_flow import (
    _AcceptedThenCancelledExecutionAdapter,
    _bar,
    _BuyEveryBarStrategy,
)
from tests.integration.test_paper_runtime_full_chain import _InstrumentContext, _portfolio_view


def build_operator_runtime() -> tuple[
    OperationsService, RuntimeSession, _AcceptedThenCancelledExecutionAdapter
]:
    """Build a real RuntimeSession bound to an OperationsService via the control plane."""
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    registry = InstrumentRegistry()
    registry.register(
        "AAPL",
        Instrument(
            instrument_id=instrument_id,
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
    adapter = _AcceptedThenCancelledExecutionAdapter()
    account_id = AccountId("acct-ops")
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategy=_BuyEveryBarStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
        )
    )
    session_registry = RuntimeSessionRegistry()
    session_registry.register(RuntimeSessionKey(runtime_instance_id="ops-rt"), session)
    service = OperationsService(command_executor=RuntimeCommandExecutor(session_registry))
    return service, session, adapter


def test_operator_kill_switch_blocks_and_cancels_real_runtime_orders() -> None:
    service, session, adapter = build_operator_runtime()
    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    state = service.activate_kill_switch(
        KillSwitchCommandDTO(scope="global", reason="operator halt"),
        operator_id="ops-a",
        runtime_instance_id="ops-rt",
    )
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC)))

    assert state.active is True
    # Only the pre-kill bar submitted; the kill-switch cancelled it and blocked the next.
    assert adapter.submitted_order_ids == [OrderId("live-000001")]
    assert adapter.cancelled_order_ids == [OrderId("live-000001")]
    assert blocked.reason_code == "KILL_SWITCH_ACTIVE"
