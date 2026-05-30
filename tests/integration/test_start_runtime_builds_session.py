"""start_runtime builds and starts a real RuntimeSession via the builder."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.application.services import RuntimeSessionBuilder, RuntimeStartConfig
from qts.core.ids import AccountId, InstrumentId
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.mode import RuntimeMode
from qts.runtime.session import RuntimeSession
from qts.runtime.state import RuntimeSessionState
from qts.strategy_sdk import Strategy

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


def test_start_runtime_builds_real_session_when_builder_supplied() -> None:
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            account_id=AccountId("acct-paper"),
            initial_cash={"USD": Decimal("100000")},
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
    )

    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            config_ref="configs/paper_simulated.yaml",
            operator_id="ops",
            idempotency_key="start-paper-1",
            reason="build session",
        ),
        session_builder=builder,
    )

    assert result.status == "started"
    assert result.evidence["session_constructed"] is True
    assert isinstance(result.session, RuntimeSession)
    # The session was actually started through the shared lifecycle, not faked.
    assert result.session.state is RuntimeSessionState.RUNNING


def test_start_runtime_without_builder_reports_unconstructed_session() -> None:
    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            config_ref="configs/paper_simulated.yaml",
            operator_id="ops",
            idempotency_key="start-paper-2",
            reason="accept only",
        )
    )

    assert result.status == "started"
    assert result.evidence["session_constructed"] is False
    assert result.session is None
