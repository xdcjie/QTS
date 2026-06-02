"""Run a short, real paper-simulated runtime loop and report real evidence.

This drives the shared runtime chain end to end: it builds a real paper
``RuntimeSession`` via :class:`RuntimeSessionBuilder`, feeds deterministic fake
market-data bars through ``session.on_market_data``, and reports the fills and
account state actually produced — not a hardcoded ``started`` string.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.application.services import RuntimeSessionBuilder, RuntimeStartConfig
from qts.core.ids import AccountId, InstrumentId
from qts.data.events import MarketDataSubscription
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.control_plane import RuntimeSessionRegistry
from qts.runtime.launch_plan import RuntimeLaunchPlan, RuntimeLaunchPlanStore
from qts.runtime.mode import RuntimeMode
from qts.strategy_sdk import Strategy
from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

_INSTRUMENT_ID = InstrumentId("EQUITY.US.NASDAQ.AAPL")


class _BuyOnceStrategy(Strategy):
    """Open a single long AAPL position on the first bar and hold."""

    def initialize(self, ctx):  # type: ignore[no-untyped-def]
        self._asset = ctx.symbol("AAPL")
        self._opened = False

    def on_bar(self, ctx, bar):  # type: ignore[no-untyped-def]
        if self._opened:
            return
        ctx.target_quantity(self._asset, Decimal("1"))
        self._opened = True


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


def _bar(start: datetime, *, close: Decimal) -> Bar:
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


def main() -> None:
    """Build and run a short paper-simulated loop, reporting real fills."""
    account_id = AccountId("acct-paper-local")
    runtime_instance_id = "paper-local-runtime"
    launch_plan_store = RuntimeLaunchPlanStore(Path("runs") / "local_launch_plans")
    launch_plan = launch_plan_store.write(
        RuntimeLaunchPlan(
            promotion_candidate_id="local-paper-demo",
            target_mode=RuntimeMode.PAPER_SIMULATED.value,
            strategy_id="paper-demo-strategy",
            source_module="scripts.run_paper",
            target_module="scripts.run_paper",
            idea_id="local-paper-demo",
            evidence_bundle_id="local-paper-demo-evidence",
            runtime={
                "runtime_mode": RuntimeMode.PAPER_SIMULATED.value,
                "runtime_instance_id": runtime_instance_id,
                "account_id": account_id.value,
                "capital_limit": "100000",
                "risk_profile_id": "local-paper-risk",
            },
            operations={
                "rollback_plan": "stop local paper demo",
                "monitoring_plan": "observe local stdout evidence",
            },
        )
    )
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            account_id=account_id,
            initial_cash={"USD": Decimal("100000")},
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
    )
    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode="paper_simulated",
            runtime_instance_id=runtime_instance_id,
            config_ref=launch_plan.config_ref,
            launch_plan_hash=launch_plan.content_hash,
            operator_id="paper-local",
            idempotency_key="run-paper-local",
            reason="local paper runtime start",
        ),
        session_builder=builder,
        session_registry=RuntimeSessionRegistry(),
        launch_plan_store=launch_plan_store,
    )
    session = result.session
    if session is None:
        raise RuntimeError("paper runtime session was not constructed")

    source = FakeStreamingMarketDataAdapter(source_id="paper-local")
    source.subscribe(
        MarketDataSubscription(
            subscription_id="aapl-1m",
            instrument_id=_INSTRUMENT_ID,
            timeframe="1m",
        )
    )

    total_fills = 0
    start_time = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    for index in range(3):
        bar = _bar(start_time + timedelta(minutes=index), close=Decimal("100") + index)
        loop_result = session.on_market_data(bar)
        total_fills += len(loop_result.fills)

    snapshot = session.account_snapshot
    position = snapshot.positions.get(_INSTRUMENT_ID)
    quantity = position.quantity if position is not None else Decimal("0")

    print(f"status={result.status} session_constructed={result.evidence['session_constructed']}")
    print(f"bars=3 fills={total_fills} aapl_position={quantity} cash_usd={snapshot.cash['USD']}")


if __name__ == "__main__":
    main()
