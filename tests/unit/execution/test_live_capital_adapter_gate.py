from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

import pytest
from qts.core.ids import AccountId, StrategyId
from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
from qts.execution.order_manager import OrderIntent
from qts.runtime.live_capital import LiveCapitalOrderDecision


def test_live_order_blocked_when_account_code_is_dup() -> None:
    adapter = _broker_execution_adapter(
        live_capital_decision=_live_capital_decision(broker_account_code="DUP1234567")
    )

    with pytest.raises(PermissionError, match="LIVE_ACCOUNT_CODE_REQUIRED"):
        adapter.execute_market_order(
            _order_intent(),
            broker_order_id="runtime-broker-001",
            market_price=Decimal("101.25"),
            account_id=_account_id(),
            strategy_id=_strategy_id(),
            client_order_id="client-001",
        )


def test_live_order_blocked_when_gateway_port_is_paper() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
        live_capital_decision=_live_capital_decision(gateway_port=4002),
    )

    with pytest.raises(PermissionError, match="LIVE_GATEWAY_PORT_REQUIRED"):
        adapter.to_order_request(
            OrderIntent(
                order_id=OrderId("ord-ibkr-port"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("1"),
            ),
            client_order_id="client-ibkr-port",
        )


def _broker_execution_adapter(
    *,
    live_capital_decision: object,
) -> BrokerExecutionAdapter:
    from qts.core.ids import BrokerId
    from qts.simulation.broker import SimulatedBrokerAdapter

    return BrokerExecutionAdapter(
        broker=SimulatedBrokerAdapter(broker_id=BrokerId("IBKR")),
        account_id=_account_id(),
        strategy_id=_strategy_id(),
        live_capital_decision=live_capital_decision,
    )


def _order_intent() -> OrderIntent:
    from qts.core.ids import InstrumentId, OrderId
    from qts.execution.order_manager import OrderIntent, OrderSide

    return OrderIntent(
        order_id=OrderId("ord-adapter-gate"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        account_id=_account_id(),
    )


def _account_id() -> AccountId:
    from qts.core.ids import AccountId

    return AccountId("acct-live")


def _strategy_id() -> StrategyId:
    from qts.core.ids import StrategyId

    return StrategyId("strategy-live")


def _live_capital_decision(**overrides: object) -> LiveCapitalOrderDecision:
    from qts.runtime.broker_startup import BrokerRuntimeStartupDecisionStatus
    from qts.runtime.live_capital import LiveCapitalOrderDecision
    from qts.runtime.mode import RuntimeMode
    from qts.runtime.permissions import OrderSubmissionPermission

    values = {
        "runtime_mode": RuntimeMode.LIVE,
        "order_submission_permission": OrderSubmissionPermission.LIVE_ORDERS_ALLOWED,
        "startup_decision_status": BrokerRuntimeStartupDecisionStatus.ALLOW_LIVE,
        "operator_signoff_valid": True,
        "market_data_permission": "live",
        "market_data_freshness": "fresh",
        "reconciliation_status": "clean",
        "kill_switch_active": False,
        "broker_account_kind": "live",
        "broker_account_code": "DU1234567",
        "gateway_port": 4001,
    }
    values.update(overrides)
    return LiveCapitalOrderDecision(**cast(Any, values))
