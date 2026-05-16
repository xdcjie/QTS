from __future__ import annotations

import json
import socket
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.domain.market_data import Bar
from qts.execution.order_manager import ExecutionReportStatus, OrderSide
from qts.registry.instrument_registry import InstrumentRegistry
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy, TargetIntent

from tests.support.ibkr_transports import (
    market_data_transport,
    order_execution_transport,
    require_ibkr_transport_sdk,
    wait_for_managed_accounts,
)


def test_ibkr_gateway_full_chain_anchor_requires_real_paper_evidence(
    request: pytest.FixtureRequest,
) -> None:
    gateway = request.config.getoption("--ibkr-paper-gateway")
    if gateway is None:
        pytest.skip("--ibkr-paper-gateway is required for the real full-chain paper anchor")
    if not request.config.getoption("--paper-only"):
        pytest.fail("--paper-only is required for the IBKR full-chain paper anchor")
    if not request.config.getoption("--operator-confirm-paper-order"):
        pytest.fail("--operator-confirm-paper-order is required before tiny paper fill tests")

    host, port_text = str(gateway).rsplit(":", maxsplit=1)
    port = int(port_text)
    with socket.create_connection((host, port), timeout=2):
        pass

    transport_name = request.config.getoption("--ibkr-transport")
    require_ibkr_transport_sdk(transport_name)

    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import (
        IbkrMarketDataContractSpec,
    )
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrOrderContractSpec,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping
    from qts.reporting.live import LiveReportWriter
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession
    from qts.runtime.sinks.base import RuntimeEvent
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    generated_at = datetime.now(UTC)
    evidence_dir = Path("evidence/ibkr")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    broker_id = BrokerId("IBKR")
    mapping = BrokerSymbolMapping(broker_id)
    mapping.register(instrument_id, "AAPL")

    market_adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host=host,
            port=port,
            client_id=102,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    market_transport = market_data_transport(
        transport_name=transport_name,
        host=host,
        port=port,
        client_id=102,
        sink=market_adapter,
    )

    order_callback_adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host=host,
            port=port,
            client_id=202,
            broker_id=broker_id,
            account_id="DU0000000",
        ),
        symbol_mapping=mapping,
    )
    order_transport = order_execution_transport(
        transport_name=transport_name,
        host=host,
        port=port,
        client_id=202,
        timeout_seconds=35,
        sink=order_callback_adapter,
    )

    event_sink = LiveRuntimeEventSink(
        evidence_dir,
        filename=f"paper-full-chain-events-{generated_at:%Y%m%dT%H%M%SZ}.ndjson",
    )
    session: RuntimeSession | None = None
    runtime_execution: _IbkrRuntimeExecutionAdapter | None = None
    account_id = ""
    config_account_id: str | None = None
    non_marketable_cancelled = False

    try:
        market_transport.connect()
        market_event = market_transport.collect_first_event(
            IbkrMarketDataContractSpec.stock("AAPL", primary_exchange="ISLAND"),
            timeout_seconds=25,
        )
        reference_price = _reference_price(market_event)
        event_sink.write(
            RuntimeEvent(
                kind="runtime.market_data",
                payload={
                    "instrument_id": instrument_id.value,
                    "event_type": type(market_event).__name__,
                    "reference_price": str(reference_price),
                },
            )
        )
    finally:
        market_transport.disconnect()

    try:
        order_transport.connect()
        account_id = _select_paper_account(wait_for_managed_accounts(order_transport))
        config_account_id = _validated_config_account(request, account_id)
        request_adapter = IbkrOrderExecutionAdapter(
            connection=IbkrOrderExecutionConnection(
                host=host,
                port=port,
                client_id=202,
                broker_id=broker_id,
                account_id=account_id,
            ),
            symbol_mapping=mapping,
        )
        contract = IbkrOrderContractSpec.stock("AAPL", primary_exchange="ISLAND")
        runtime_execution = _IbkrRuntimeExecutionAdapter(
            transport=order_transport,
            request_adapter=request_adapter,
            contract=contract,
        )
        session = RuntimeSession(
            RuntimeSessionDependencies(
                strategy=_RoundTripStrategy(),
                risk_engine=RiskEngine([]),
                instrument_context=_InstrumentContext(instrument_id),
                execution_adapter=runtime_execution,
                account_actor=AccountActor(initial_cash={"USD": Decimal("1000000")}),
                instrument_registry=_instrument_registry(instrument_id),
                portfolio_view=_portfolio_view,
                multiplier_for=lambda instrument_id: Decimal("1"),
                sink=event_sink,
                order_id_prefix="paper",
            )
        )
        session.start()
        first_result = session.on_market_data(_bar(instrument_id, generated_at, reference_price))
        second_result = session.on_market_data(
            _bar(instrument_id, generated_at + timedelta(minutes=1), reference_price)
        )
        reports = tuple(runtime_execution.fill_reports)
        orders = first_result.orders + second_result.orders
        fills = first_result.fills + second_result.fills
        non_marketable_cancelled = _submit_and_cancel_non_marketable_order(
            order_transport=order_transport,
            request_adapter=request_adapter,
            contract=contract,
            instrument_id=instrument_id,
            generated_at=generated_at,
        )
    finally:
        if runtime_execution is not None:
            runtime_execution.cancel_active_external_orders()
        order_transport.disconnect()
        event_sink.close()

    if session is None:
        raise AssertionError("runtime session was not created")
    account_snapshot = session.account_snapshot
    final_quantity = account_snapshot.positions.get(instrument_id)
    final_position = final_quantity.quantity if final_quantity is not None else Decimal("0")
    manifest = LiveReportWriter(evidence_dir).write_manifest(
        config_payload={
            "mode": "paper_broker",
            "gateway": gateway,
            "transport": transport_name,
            "client_ids": {"market_data": 102, "order_execution": 202},
            "account_id": account_id,
            "configured_account_id": config_account_id,
        },
        runtime_mode="paper_broker",
        account_id=account_id,
        connection_metadata={"host": host, "port": port},
        event_sink=event_sink,
    )
    evidence = {
        "schema_version": 1,
        "generated_at": generated_at.isoformat(),
        "gateway": gateway,
        "transport": transport_name,
        "paper_only": True,
        "account_id": account_id,
        "config_account_id": config_account_id,
        "account_config_matches_gateway": config_account_id == account_id,
        "observe_only": True,
        "market_data": True,
        "non_marketable_cancel": non_marketable_cancelled,
        "tiny_paper_fill": len(reports) == 2 and len(fills) == 2,
        "strategy_order": len(orders) == 2,
        "submitted_via_runtime_session": True,
        "reconciliation_clean": final_position == Decimal("0"),
        "kill_switch": "not_run",
        "rollback": "not_run",
        "reference_price": str(reference_price),
        "fills": [
            {
                "report_id": report.report_id,
                "runtime_broker_order_id": report.broker_order_id,
                "external_broker_order_id": runtime_execution.external_id_for(
                    report.broker_order_id
                )
                if runtime_execution is not None
                else None,
                "fill_id": report.fill_id,
                "status": report.status.value,
                "filled_quantity": str(report.filled_quantity),
                "fill_price": str(report.fill_price),
                "commission": str(report.commission),
            }
            for report in reports
        ],
        "final_internal_account": {
            "cash": {currency: str(balance) for currency, balance in account_snapshot.cash.items()},
            "positions": {
                item.value: str(position.quantity)
                for item, position in account_snapshot.positions.items()
            },
        },
        "report_manifest": str(manifest.manifest_path),
        "runtime_orders": [
            {
                "order_id": order.order_id.value,
                "broker_order_id": order.broker_order_id,
                "state": order.state.value,
            }
            for order in orders
        ],
    }
    evidence_path = evidence_dir / f"paper-full-chain-{generated_at:%Y%m%dT%H%M%SZ}.json"
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    assert len(reports) == 2
    assert len(orders) == 2
    assert len(fills) == 2
    assert final_position == Decimal("0")
    assert non_marketable_cancelled
    assert evidence_path.exists()


@dataclass(slots=True)
class _IbkrRuntimeExecutionAdapter:
    transport: Any
    request_adapter: Any
    contract: Any
    fill_reports: list[Any] = field(default_factory=list)
    _external_by_runtime: dict[str, str] = field(default_factory=dict)
    _active_external_ids: set[str] = field(default_factory=set)

    def execute_market_order(
        self,
        intent: Any,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> Any:
        from qts.execution.broker import BrokerOrderType

        _ = account_id, strategy_id, correlation_id
        limit_price = _marketable_limit(intent.side, market_price)
        request = self.request_adapter.to_order_request(
            intent,
            client_order_id=client_order_id,
            order_type=BrokerOrderType.LIMIT,
            limit_price=limit_price,
            outside_regular_trading_hours=True,
            contract=self.contract,
        )
        external_broker_order_id = self.transport.submit_order_with_broker_id(request)
        self._external_by_runtime[broker_order_id] = external_broker_order_id
        self._active_external_ids.add(external_broker_order_id)
        try:
            report = self.transport.wait_for_fill_report(
                external_broker_order_id,
                timeout_seconds=45,
            )
        finally:
            self._active_external_ids.discard(external_broker_order_id)
        runtime_report = replace(report, broker_order_id=broker_order_id)
        self.fill_reports.append(runtime_report)
        return runtime_report

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> Any:
        del order_id
        _ = account_id, strategy_id, client_order_id, correlation_id
        external_broker_order_id = self._external_by_runtime[broker_order_id]
        self.transport.cancel_order(external_broker_order_id)
        report = self.transport.wait_for_order_status(
            external_broker_order_id,
            statuses={ExecutionReportStatus.CANCELLED},
            timeout_seconds=25,
        )
        self._active_external_ids.discard(external_broker_order_id)
        return replace(report, broker_order_id=broker_order_id)

    def external_id_for(self, runtime_broker_order_id: str) -> str | None:
        return self._external_by_runtime.get(runtime_broker_order_id)

    def cancel_active_external_orders(self) -> None:
        for broker_order_id in tuple(self._active_external_ids):
            with suppress(Exception):
                self.transport.cancel_order(broker_order_id)
        self._active_external_ids.clear()


class _RoundTripStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.step = 0

    def on_bar(self, ctx: Any, bar: object) -> None:
        del bar
        if self.step == 0:
            ctx.target_quantity(self.asset, Decimal("1"))
        elif self.step == 1:
            ctx.target_quantity(self.asset, Decimal("0"))
        self.step += 1


class _InstrumentContext:
    def __init__(self, instrument_id: InstrumentId) -> None:
        self._instrument_id = instrument_id

    def order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId:
        del bar
        return intent.asset.instrument_id

    def market_price_for_intent(
        self,
        intent: TargetIntent,
        *,
        instrument_id: InstrumentId,
        bar: Bar,
    ) -> Decimal:
        del intent, instrument_id
        return bar.close

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        del instrument_id
        return False

    def related_contracts_for(
        self,
        continuous_instrument_id: InstrumentId,
    ) -> frozenset[InstrumentId]:
        del continuous_instrument_id
        raise RuntimeError("continuous contracts are not configured")


def _instrument_registry(instrument_id: InstrumentId) -> InstrumentRegistry:
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry

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
    return registry


def _portfolio_view(
    snapshot: Any,
    *,
    latest_prices: Mapping[InstrumentId, Decimal],
) -> PortfolioView:
    positions = {
        instrument_id: PortfolioPosition(
            quantity=position.quantity,
            market_value=position.quantity * latest_prices.get(instrument_id, Decimal("0")),
        )
        for instrument_id, position in snapshot.positions.items()
    }
    cash = snapshot.cash["USD"]
    return PortfolioView(
        cash=cash,
        equity=cash + sum((position.market_value for position in positions.values()), Decimal("0")),
        positions=positions,
    )


def _bar(instrument_id: InstrumentId, start: datetime, price: Decimal) -> Bar:
    return Bar(
        instrument_id=instrument_id,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id=start.date().isoformat(),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal("100"),
        is_complete=True,
    )


def _marketable_limit(side: OrderSide, market_price: Decimal) -> Decimal:
    if side is OrderSide.BUY:
        return (market_price * Decimal("1.03")).quantize(Decimal("0.01"))
    return (market_price * Decimal("0.97")).quantize(Decimal("0.01"))


def _submit_and_cancel_non_marketable_order(
    *,
    order_transport: Any,
    request_adapter: Any,
    contract: Any,
    instrument_id: InstrumentId,
    generated_at: datetime,
) -> bool:
    from qts.core.ids import OrderId
    from qts.execution.broker import BrokerOrderType
    from qts.execution.order_manager import ExecutionReportStatus, OrderIntent, OrderSide

    cancel_intent = OrderIntent(
        order_id=OrderId(f"ibkr-paper-full-chain-cancel-{generated_at:%H%M%S}"),
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("1"),
    )
    cancel_request = request_adapter.to_order_request(
        cancel_intent,
        client_order_id=f"client-{cancel_intent.order_id.value}",
        order_type=BrokerOrderType.LIMIT,
        limit_price=Decimal("0.01"),
        outside_regular_trading_hours=True,
        contract=contract,
    )
    cancel_broker_order_id = order_transport.submit_order_with_broker_id(cancel_request)
    try:
        order_transport.cancel_order(cancel_broker_order_id)
        cancel_report = order_transport.wait_for_order_status(
            cancel_broker_order_id,
            statuses={ExecutionReportStatus.CANCELLED},
            timeout_seconds=25,
        )
        return cancel_report.status is ExecutionReportStatus.CANCELLED
    finally:
        with suppress(Exception):
            order_transport.cancel_order(cancel_broker_order_id)


def _validated_config_account(
    request: pytest.FixtureRequest, gateway_account_id: str
) -> str | None:
    from qts.config.ibkr import IbkrEnvironmentConfig

    config_path_option = request.config.getoption("--config")
    config_path = Path(str(config_path_option or "configs/paper.ibkr.local.yaml"))
    if not config_path.exists():
        return None
    config = IbkrEnvironmentConfig.from_yaml(config_path)
    config_account_id = config.order_execution.account_id
    if config_account_id != gateway_account_id:
        pytest.fail(
            "paper config account_id must match Gateway managed account: "
            f"{config_account_id} != {gateway_account_id}"
        )
    return config_account_id


def _reference_price(event: Any) -> Decimal:
    from qts.domain.market_data import Quote, Tick

    if isinstance(event, Quote):
        if event.ask_price > Decimal("0"):
            return event.ask_price
        return event.bid_price
    if isinstance(event, Tick):
        return event.price
    raise TypeError(f"unsupported market data event: {type(event).__name__}")


def _select_paper_account(accounts: tuple[str, ...]) -> str:
    paper_accounts = [account for account in accounts if account.upper().startswith("DU")]
    if not paper_accounts:
        pytest.fail("paper-only IBKR full-chain anchor requires a managed DU paper account")
    return paper_accounts[0]
