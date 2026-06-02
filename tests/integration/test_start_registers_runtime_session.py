"""Integration: verified runtime start registers the real session."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.application.services import RuntimeSessionBuilder, RuntimeStartConfig
from qts.core.ids import AccountId, InstrumentId
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.control_plane import RuntimeSessionKey, RuntimeSessionRegistry
from qts.runtime.mode import RuntimeMode
from qts.strategy_sdk import Strategy, StrategyContext

from tests.support.runtime_launch import runtime_launch_fixture


class _NoopStrategy(Strategy):
    def initialize(self, ctx: StrategyContext) -> None:
        self.asset = ctx.symbol("AAPL")


def test_start_registers_runtime_session(tmp_path: Path) -> None:
    fixture = runtime_launch_fixture(tmp_path)
    registry = RuntimeSessionRegistry()
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            account_id=AccountId("acct-test"),
            initial_cash={"USD": Decimal("100000")},
        ),
        strategy=_NoopStrategy(),
        instrument_registry=_instrument_registry(),
    )
    command = StartRuntimeCommand(
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        runtime_instance_id=fixture.runtime_instance_id,
        config_ref=fixture.config_ref,
        launch_plan_hash=fixture.launch_plan_hash,
        operator_id="ops",
        idempotency_key="start-registers-session",
        reason="registration gate",
    )

    result = start_runtime(
        command,
        session_builder=builder,
        session_registry=registry,
        launch_plan_store=fixture.store,
    )

    assert result.status == "started"
    assert result.evidence["launch_plan_verified"] is True
    assert result.evidence["session_registered"] is True
    assert (
        registry.resolve(RuntimeSessionKey(runtime_instance_id=fixture.runtime_instance_id))
        is result.session
    )


def _instrument_registry() -> InstrumentRegistry:
    registry = InstrumentRegistry()
    registry.register(
        "AAPL",
        Instrument(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
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
