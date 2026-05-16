from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from qts.core.hashing import stable_json_hash
from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, RuntimeRunId, StrategyId
from qts.domain.market_data import Bar
from qts.execution.order_manager import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
)
from qts.reporting.base import (
    PLATFORM_BASELINE_VERSION,
    RUNTIME_ARTIFACT_SCHEMA_VERSION,
    RuntimeManifest,
)
from qts.runtime.broker_startup import (
    BrokerRuntimeStartupCheck,
    BrokerRuntimeStartupChecklist,
    BrokerRuntimeStartupDecision,
    BrokerRuntimeStartupDecisionStatus,
)
from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
from qts.runtime.permissions import OrderSubmissionPermission
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.sinks.broker_runtime import BrokerRuntimeEventSink
from qts.runtime.topology import (
    AccountRuntimeSpec,
    MarketDataRouteSpec,
    RuntimeTopology,
    StrategyRuntimeSpec,
)
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy, TargetIntent

from tests.support.backtest_streaming import run_engine_streaming

LOCAL_SMOKES = (
    "backtest_minimal_single_strategy_single_account",
    "backtest_multi_strategy_one_account_conflict_reject",
    "backtest_two_accounts_isolation",
    "paper_simulated_market_data_to_fill",
    "live_observation_market_data_no_orders",
    "live_permission_off_blocks_order",
    "broker_disconnect_blocks_order",
    "reconnect_requires_reconciliation",
)

EXTERNAL_SMOKES = (
    "paper_broker_gateway_market_data_anchor",
    "paper_broker_submit_cancel_drill",
)


@dataclass(frozen=True, slots=True)
class SmokeEvidence:
    smoke_name: str
    run_id: str
    manifest_path: Path
    event_path: Path
    manifest: dict[str, Any]
    events: tuple[dict[str, Any], ...]
    expected_correlation: bool = True


@pytest.mark.integration
@pytest.mark.parametrize(
    ("smoke_name", "smoke"),
    [
        (
            "backtest_minimal_single_strategy_single_account",
            lambda tmp_path: _backtest_minimal(tmp_path),
        ),
        (
            "backtest_multi_strategy_one_account_conflict_reject",
            lambda tmp_path: _runtime_conflict_reject(tmp_path, RuntimeMode.PAPER_SIMULATED),
        ),
        (
            "backtest_two_accounts_isolation",
            lambda tmp_path: _runtime_two_accounts_isolation(tmp_path, RuntimeMode.PAPER_SIMULATED),
        ),
        (
            "paper_simulated_market_data_to_fill",
            lambda tmp_path: _runtime_paper_simulated_fill(tmp_path),
        ),
        (
            "live_observation_market_data_no_orders",
            lambda tmp_path: _runtime_live_observation_no_orders(tmp_path),
        ),
        (
            "live_permission_off_blocks_order",
            lambda tmp_path: _runtime_live_permission_off(tmp_path),
        ),
        (
            "broker_disconnect_blocks_order",
            lambda tmp_path: _runtime_broker_disconnect_blocks(tmp_path),
        ),
        (
            "reconnect_requires_reconciliation",
            lambda tmp_path: _runtime_reconnect_requires_reconciliation(tmp_path),
        ),
    ],
)
def test_local_readiness_smoke_matrix_emits_manifest_and_event_evidence(
    tmp_path: Path,
    smoke_name: str,
    smoke: Callable[[Path], SmokeEvidence],
) -> None:
    evidence = smoke(tmp_path / smoke_name)

    assert evidence.smoke_name == smoke_name
    _assert_smoke_evidence(evidence)


def test_readiness_smoke_matrix_is_documented_with_local_and_external_gates() -> None:
    doc = Path("docs/testing/readiness_smoke_matrix.md")
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert doc.exists(), "M6-4 readiness smoke matrix document is missing"
    text = doc.read_text(encoding="utf-8")

    for smoke_name in LOCAL_SMOKES:
        assert smoke_name in text, f"local smoke missing from matrix docs: {smoke_name}"
    for smoke_name in EXTERNAL_SMOKES:
        assert smoke_name in text, f"external smoke missing from matrix docs: {smoke_name}"
    assert "readiness-smoke-local" in text
    assert "readiness-smoke-external" in text
    assert "readiness-smoke-local:" in makefile
    assert "readiness-smoke-external:" in makefile
    assert "-m external" in makefile


def _assert_smoke_evidence(evidence: SmokeEvidence) -> None:
    smoke_name = evidence.smoke_name
    run_id = evidence.run_id

    assert evidence.manifest_path.exists(), f"{smoke_name} {run_id} missing manifest artifact"
    assert evidence.event_path.exists(), f"{smoke_name} {run_id} missing event artifact"
    RuntimeManifest.from_payload(evidence.manifest)
    assert evidence.manifest["run_id"] == run_id, f"{smoke_name} manifest run_id mismatch"
    assert evidence.manifest["artifacts"]["events"]["rows"] == len(evidence.events), (
        f"{smoke_name} {run_id} event row count mismatch"
    )
    assert len(evidence.events) > 0, f"{smoke_name} {run_id} emitted no events"
    assert {row["run_id"] for row in evidence.events} == {run_id}, (
        f"{smoke_name} {run_id} event run_id mismatch"
    )
    if evidence.expected_correlation:
        correlations = sorted(
            {str(row["correlation_id"]) for row in evidence.events if row.get("correlation_id")}
        )
        assert correlations, f"{smoke_name} {run_id} emitted no correlation_id"


def _backtest_minimal(output_dir: Path) -> SmokeEvidence:
    from qts.backtest.engine import BacktestEngine

    captured = run_engine_streaming(
        BacktestEngine(
            strategy=_BuyOnceStrategy(),
            bars=(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)),),
            initial_cash=Decimal("10000"),
        ),
        output_dir,
    )

    assert captured.result.final_account.positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("1")
    return SmokeEvidence(
        smoke_name="backtest_minimal_single_strategy_single_account",
        run_id=captured.manifest["run_id"],
        manifest_path=Path(captured.result.manifest_path),
        event_path=Path(captured.result.artifact_paths["events"]),
        manifest=captured.manifest,
        events=captured.events,
    )


def _runtime_conflict_reject(output_dir: Path, mode: RuntimeMode) -> SmokeEvidence:
    session, sink = _session(
        output_dir,
        smoke_name="backtest_multi_strategy_one_account_conflict_reject",
        mode=mode,
        strategies=(_SignedTargetStrategy(Decimal("1")), _SignedTargetStrategy(Decimal("-1"))),
        topology=_one_account_two_strategy_topology(
            run_id=RuntimeRunId("backtest-multi-strategy-one-account-conflict-reject"),
            mode=mode,
            signal_aggregation_policy="reject_conflict",
        ),
        execution_adapter=_FilledExecutionAdapter(),
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    sink.close()

    assert result.orders == ()
    assert result.fills == ()
    events = _read_events(sink.path)
    assert any(row["kind"] == "runtime.signal_rejected" for row in events)
    return _write_smoke_manifest(
        output_dir=output_dir,
        smoke_name="backtest_multi_strategy_one_account_conflict_reject",
        run_id="backtest-multi-strategy-one-account-conflict-reject",
        runtime_mode=mode,
        event_path=sink.path,
        events=events,
    )


def _runtime_two_accounts_isolation(output_dir: Path, mode: RuntimeMode) -> SmokeEvidence:
    account_a = AccountId("acct-smoke-a")
    account_b = AccountId("acct-smoke-b")
    session, sink = _session(
        output_dir,
        smoke_name="backtest_two_accounts_isolation",
        mode=mode,
        strategies=(_FixedTargetStrategy(Decimal("1")), _FixedTargetStrategy(Decimal("2"))),
        topology=_two_account_topology(
            run_id=RuntimeRunId("backtest-two-accounts-isolation"),
            mode=mode,
            account_a=account_a,
            account_b=account_b,
        ),
        execution_adapter=_FilledExecutionAdapter(),
        account_actors={
            account_a: _account_actor(account_a),
            account_b: _account_actor(account_b),
        },
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    sink.close()

    snapshot_by_account = {
        account_id: snapshot for account_id, snapshot in result.account_snapshots
    }
    assert snapshot_by_account[account_a].positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("1")
    assert snapshot_by_account[account_b].positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("2")
    events = _read_events(sink.path)
    assert {row["account_id"] for row in events if row["kind"] == "runtime.order_submitted"} == {
        account_a.value,
        account_b.value,
    }
    return _write_smoke_manifest(
        output_dir=output_dir,
        smoke_name="backtest_two_accounts_isolation",
        run_id="backtest-two-accounts-isolation",
        runtime_mode=mode,
        event_path=sink.path,
        events=events,
    )


def _runtime_paper_simulated_fill(output_dir: Path) -> SmokeEvidence:
    session, sink = _session(
        output_dir,
        smoke_name="paper_simulated_market_data_to_fill",
        mode=RuntimeMode.PAPER_SIMULATED,
        strategy=_BuyOnceStrategy(),
        execution_adapter=_FilledExecutionAdapter(),
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    sink.close()

    assert len(result.fills) == 1
    events = _read_events(sink.path)
    assert any(row["kind"] == "runtime.fill_applied" for row in events)
    return _write_smoke_manifest(
        output_dir=output_dir,
        smoke_name="paper_simulated_market_data_to_fill",
        run_id="paper-simulated-market-data-to-fill",
        runtime_mode=RuntimeMode.PAPER_SIMULATED,
        event_path=sink.path,
        events=events,
    )


def _runtime_live_observation_no_orders(output_dir: Path) -> SmokeEvidence:
    session, sink = _session(
        output_dir,
        smoke_name="live_observation_market_data_no_orders",
        mode=RuntimeMode.LIVE_OBSERVATION,
        execution_environment=ExecutionEnvironment.DISABLED,
        strategy=_BuyOnceStrategy(),
        execution_adapter=_FilledExecutionAdapter(),
        startup_decision=_startup_decision(
            mode=RuntimeMode.LIVE_OBSERVATION,
            status=BrokerRuntimeStartupDecisionStatus.ALLOW_OBSERVATION,
            permission=OrderSubmissionPermission.OBSERVATION_ONLY,
        ),
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    sink.close()

    assert result.orders == ()
    assert result.reason_code == "OBSERVATION_ONLY"
    events = _read_events(sink.path)
    assert any(row["kind"] == "order_blocked_by_permission" for row in events)
    return _write_smoke_manifest(
        output_dir=output_dir,
        smoke_name="live_observation_market_data_no_orders",
        run_id="live-observation-market-data-no-orders",
        runtime_mode=RuntimeMode.LIVE_OBSERVATION,
        event_path=sink.path,
        events=events,
    )


def _runtime_live_permission_off(output_dir: Path) -> SmokeEvidence:
    session, sink = _session(
        output_dir,
        smoke_name="live_permission_off_blocks_order",
        mode=RuntimeMode.LIVE,
        execution_environment=ExecutionEnvironment.BROKER,
        strategy=_BuyOnceStrategy(),
        execution_adapter=_FilledExecutionAdapter(),
        startup_decision=_startup_decision(
            mode=RuntimeMode.LIVE,
            status=BrokerRuntimeStartupDecisionStatus.ALLOW_OBSERVATION,
            permission=OrderSubmissionPermission.OBSERVATION_ONLY,
        ),
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    sink.close()

    assert result.orders == ()
    assert result.reason_code == "OBSERVATION_ONLY"
    events = _read_events(sink.path)
    assert any(row["kind"] == "order_blocked_by_permission" for row in events)
    return _write_smoke_manifest(
        output_dir=output_dir,
        smoke_name="live_permission_off_blocks_order",
        run_id="live-permission-off-blocks-order",
        runtime_mode=RuntimeMode.LIVE,
        event_path=sink.path,
        events=events,
    )


def _runtime_broker_disconnect_blocks(output_dir: Path) -> SmokeEvidence:
    session, sink = _session(
        output_dir,
        smoke_name="broker_disconnect_blocks_order",
        mode=RuntimeMode.PAPER_BROKER,
        execution_environment=ExecutionEnvironment.BROKER,
        strategy=_BuyOnceStrategy(),
        execution_adapter=_FilledExecutionAdapter(),
        startup_decision=_startup_decision(
            mode=RuntimeMode.PAPER_BROKER,
            status=BrokerRuntimeStartupDecisionStatus.ALLOW_PAPER,
            permission=OrderSubmissionPermission.PAPER_ORDERS_ALLOWED,
        ),
    )

    session.start()
    session.on_broker_disconnect(reason="readiness smoke disconnect")
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    sink.close()

    assert result.orders == ()
    assert result.reason_code == "RUNTIME_DEGRADED"
    events = _read_events(sink.path)
    assert any(row["kind"] == "runtime.broker_disconnected" for row in events)
    assert any(row["kind"] == "order_blocked_by_permission" for row in events)
    return _write_smoke_manifest(
        output_dir=output_dir,
        smoke_name="broker_disconnect_blocks_order",
        run_id="broker-disconnect-blocks-order",
        runtime_mode=RuntimeMode.PAPER_BROKER,
        event_path=sink.path,
        events=events,
    )


def _runtime_reconnect_requires_reconciliation(output_dir: Path) -> SmokeEvidence:
    session, sink = _session(
        output_dir,
        smoke_name="reconnect_requires_reconciliation",
        mode=RuntimeMode.PAPER_BROKER,
        execution_environment=ExecutionEnvironment.BROKER,
        strategy=_BuyOnceStrategy(),
        execution_adapter=_FilledExecutionAdapter(),
        startup_decision=_startup_decision(
            mode=RuntimeMode.PAPER_BROKER,
            status=BrokerRuntimeStartupDecisionStatus.ALLOW_PAPER,
            permission=OrderSubmissionPermission.PAPER_ORDERS_ALLOWED,
        ),
        broker_reconnect_reconciliation=_RecordingReconnectReconciliation(
            passed=False,
            reason_code="UNRESOLVED_CALLBACKS",
            unresolved_callback_count=1,
        ),
    )

    session.start()
    session.on_broker_disconnect(reason="readiness smoke disconnect")
    session.on_broker_reconnect(reason="readiness smoke reconnect")
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    sink.close()

    assert result.orders == ()
    assert result.reason_code == "RUNTIME_DEGRADED"
    events = _read_events(sink.path)
    failure = next(row for row in events if row["kind"] == "runtime.reconciliation_failed")
    assert failure["payload"]["reason_code"] == "UNRESOLVED_CALLBACKS"
    return _write_smoke_manifest(
        output_dir=output_dir,
        smoke_name="reconnect_requires_reconciliation",
        run_id="reconnect-requires-reconciliation",
        runtime_mode=RuntimeMode.PAPER_BROKER,
        event_path=sink.path,
        events=events,
    )


def _session(
    output_dir: Path,
    *,
    smoke_name: str,
    mode: RuntimeMode,
    strategy: Strategy | None = None,
    strategies: tuple[Strategy, ...] | None = None,
    topology: RuntimeTopology | None = None,
    execution_adapter: Any,
    execution_environment: ExecutionEnvironment = ExecutionEnvironment.SIMULATED,
    account_actors: dict[AccountId, Any] | None = None,
    startup_decision: BrokerRuntimeStartupDecision | None = None,
    broker_reconnect_reconciliation: Any | None = None,
) -> tuple[Any, BrokerRuntimeEventSink]:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession
    from qts.runtime.sinks.base import RuntimeEventContext

    run_id = RuntimeRunId(smoke_name.replace("_", "-"))
    sink = BrokerRuntimeEventSink(
        output_dir,
        context=RuntimeEventContext(
            run_id=run_id,
            mode=mode,
            execution_environment=execution_environment,
        ),
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            run_id=run_id,
            mode=mode,
            execution_environment=execution_environment,
            strategy=strategy,
            strategies=strategies,
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=execution_adapter,
            account_id=None if topology is not None else AccountId("acct-smoke"),
            strategy_id=None if topology is not None else StrategyId("strategy-smoke"),
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=None if topology is not None else AccountId("acct-smoke"),
            ),
            account_actors=account_actors,
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            sink=sink,
            runtime_topology=topology,
            startup_decision=startup_decision,
            broker_reconnect_reconciliation=broker_reconnect_reconciliation,
        )
    )
    return session, sink


def _write_smoke_manifest(
    *,
    output_dir: Path,
    smoke_name: str,
    run_id: str,
    runtime_mode: RuntimeMode,
    event_path: Path,
    events: tuple[dict[str, Any], ...],
) -> SmokeEvidence:
    manifest_path = output_dir / "readiness-smoke.manifest.json"
    payload: dict[str, Any] = {
        "run_id": run_id,
        "runtime_instance_id": f"{run_id}-instance",
        "runtime_mode": runtime_mode.value,
        "market_data_environment": "realtime",
        "execution_environment": (
            "broker"
            if runtime_mode in {RuntimeMode.PAPER_BROKER, RuntimeMode.LIVE}
            else "simulated"
        ),
        "account_environment": (
            "live"
            if runtime_mode is RuntimeMode.LIVE
            else "paper"
            if runtime_mode is RuntimeMode.PAPER_BROKER
            else "simulated"
        ),
        "order_submission_permission": runtime_mode is RuntimeMode.LIVE,
        "event_schema_version": RuntimeEvent.SCHEMA_VERSION,
        "artifact_schema_version": RUNTIME_ARTIFACT_SCHEMA_VERSION,
        "config_hash": stable_json_hash({"smoke_name": smoke_name, "runtime_mode": runtime_mode}),
        "topology_hash": stable_json_hash({"smoke_name": smoke_name, "run_id": run_id}),
        "startup_checklist_hash": stable_json_hash({"smoke_name": smoke_name, "startup": "local"}),
        "created_at": datetime(2026, 1, 2, tzinfo=UTC).isoformat(),
        "finalized_at": datetime(2026, 1, 2, 0, 1, tzinfo=UTC).isoformat(),
        "platform_baseline_version": PLATFORM_BASELINE_VERSION,
        "source_commit": "not-applicable-readiness-smoke",
        "operator_identity_hash": "sha256:not-applicable-readiness-smoke",
        "artifacts": {
            "events": {
                "path": str(event_path),
                "rows": len(events),
                "sha256": stable_json_hash(event_path.read_text(encoding="utf-8")),
            }
        },
        "smoke_name": smoke_name,
    }
    payload["manifest_hash"] = RuntimeManifest.hash_payload(payload)
    RuntimeManifest.from_payload(payload)
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return SmokeEvidence(
        smoke_name=smoke_name,
        run_id=run_id,
        manifest_path=manifest_path,
        event_path=event_path,
        manifest=payload,
        events=events,
    )


def _read_events(path: Path) -> tuple[dict[str, Any], ...]:
    return tuple(
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    )


def _bar(start: datetime) -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("100"),
        is_complete=True,
    )


class _BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.placed = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.placed:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.placed = True


class _FixedTargetStrategy(Strategy):
    def __init__(self, target: Decimal) -> None:
        self._target = target

    def initialize(self, ctx: Any) -> None:
        self._asset = ctx.symbol("AAPL")

    def on_bar(self, ctx: Any, bar: object) -> None:
        ctx.target_quantity(self._asset, self._target)


class _SignedTargetStrategy(_FixedTargetStrategy):
    pass


class _InstrumentContext:
    def order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId:
        return intent.asset.instrument_id

    def market_price_for_intent(
        self,
        intent: TargetIntent,
        *,
        instrument_id: InstrumentId,
        bar: Bar,
    ) -> Decimal:
        return bar.close

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        return False

    def related_contracts_for(
        self,
        continuous_instrument_id: InstrumentId,
    ) -> frozenset[InstrumentId]:
        raise RuntimeError("continuous contracts are not configured")


@dataclass(slots=True)
class _FilledExecutionAdapter:
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
    ) -> ExecutionReport:
        _ = account_id, strategy_id, client_order_id, correlation_id
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


@dataclass(slots=True)
class _RecordingReconnectReconciliation:
    passed: bool
    reason_code: str | None = None
    drift_count: int = 0
    unresolved_callback_count: int = 0
    calls: list[str] = field(default_factory=list)

    def resubscribe_market_data(self) -> None:
        self.calls.append("market_data")

    def refresh_open_orders(self) -> None:
        self.calls.append("open_orders")

    def refresh_positions(self) -> None:
        self.calls.append("positions")

    def refresh_executions(self) -> None:
        self.calls.append("executions")

    def refresh_account_summary(self) -> None:
        self.calls.append("account_summary")

    def reconcile_after_reconnect(self) -> Any:
        from qts.runtime.broker_lifecycle import BrokerReconnectReconciliationResult

        self.calls.append("reconcile")
        return BrokerReconnectReconciliationResult(
            passed=self.passed,
            reason_code=self.reason_code,
            drift_count=self.drift_count,
            unresolved_callback_count=self.unresolved_callback_count,
        )


def _one_account_two_strategy_topology(
    *,
    run_id: RuntimeRunId,
    mode: RuntimeMode,
    signal_aggregation_policy: str,
) -> RuntimeTopology:
    account_id = AccountId("acct-smoke-shared")
    return RuntimeTopology(
        run_id=run_id,
        mode=mode,
        accounts=(AccountRuntimeSpec(account_id=account_id, initial_cash=Decimal("10000")),),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-smoke-a"),
                strategy_class="tests.integration.test_readiness_smoke_matrix._SignedTargetStrategy",
                account_id=account_id,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
                signal_aggregation_policy=signal_aggregation_policy,
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-smoke-b"),
                strategy_class="tests.integration.test_readiness_smoke_matrix._SignedTargetStrategy",
                account_id=account_id,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
                signal_aggregation_policy=signal_aggregation_policy,
            ),
        ),
        broker_routes=(),
        market_data_routes=(_market_data_route(),),
    )


def _two_account_topology(
    *,
    run_id: RuntimeRunId,
    mode: RuntimeMode,
    account_a: AccountId,
    account_b: AccountId,
) -> RuntimeTopology:
    return RuntimeTopology(
        run_id=run_id,
        mode=mode,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("10000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-smoke-a"),
                strategy_class="tests.integration.test_readiness_smoke_matrix._FixedTargetStrategy",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-smoke-b"),
                strategy_class="tests.integration.test_readiness_smoke_matrix._FixedTargetStrategy",
                account_id=account_b,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(_market_data_route(),),
    )


def _market_data_route() -> MarketDataRouteSpec:
    return MarketDataRouteSpec(
        source_id="streaming",
        source_type="streaming",
        provider="streaming",
        subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
    )


def _startup_decision(
    *,
    mode: RuntimeMode,
    status: BrokerRuntimeStartupDecisionStatus,
    permission: OrderSubmissionPermission,
) -> BrokerRuntimeStartupDecision:
    return BrokerRuntimeStartupDecision(
        status=status,
        mode=mode,
        order_permission=permission,
        real_order_submission_enabled=False,
        checklist=BrokerRuntimeStartupChecklist(
            checks=(
                BrokerRuntimeStartupCheck(
                    check_name="readiness_smoke_startup_gate",
                    status="PASS",
                    severity="INFO",
                    evidence=f"mode={mode.value};permission={permission.value}",
                    remediation="none",
                ),
            )
        ),
    )


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


def _registry() -> Any:
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry

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
    return registry


def _account_actor(account_id: AccountId) -> Any:
    from qts.runtime.actors.account_actor import AccountActor

    return AccountActor(initial_cash={"USD": Decimal("10000")}, account_id=account_id)
