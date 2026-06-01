"""Approved promotion packet -> runtime config -> start_runtime builds a session.

This proves the M2 ownership boundary: PromotionPacketV2 stays validation-only,
PromotionRuntimeConfigBuilder converts an approved paper packet's runtime mapping
into a StartRuntimeCommand, and that command drives a real RuntimeSession build.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.application.services import (
    PromotionRuntimeConfigBuilder,
    RuntimeSessionBuilder,
    RuntimeStartConfig,
)
from qts.core.ids import AccountId, InstrumentId
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.registry.instrument_registry import InstrumentRegistry
from qts.research.audit_log import ResearchAuditLog
from qts.research.promotion_packet import PromotionPacketV2
from qts.runtime.broker_startup import validate_live_startup
from qts.runtime.config import BrokerRuntimeConfig
from qts.runtime.mode import RuntimeMode
from qts.runtime.session import RuntimeSession
from qts.strategy_sdk import Strategy

from tests.unit.research.test_promotion_packet import (
    _packet_payload,
    _write_verifiable_bundle,
)

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


def _approved_paper_packet(tmp_path: Path) -> PromotionPacketV2:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    packet = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, target_mode="paper_simulated")
    )
    machine = packet.validate_machine(evidence_registry=registry, audit_log=audit_log)
    assert machine.accepted is True
    human = packet.human_review(
        audit_log=audit_log,
        decision="approved",
        reviewer="risk",
        reviewed_at=datetime(2026, 5, 28, tzinfo=UTC),
        expected_packet_hash=machine.packet_hash,
    )
    assert human.status == "human_approved"
    return packet


def _approved_live_observation_packet(tmp_path: Path) -> PromotionPacketV2:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit-live.jsonl")
    packet = PromotionPacketV2.from_payload(
        _packet_payload(
            bundle_id,
            target_mode="live_observation",
            artifact_root=tmp_path,
        )
    )
    machine = packet.validate_machine(evidence_registry=registry, audit_log=audit_log)
    assert machine.accepted is True
    human = packet.human_review(
        audit_log=audit_log,
        decision="approved",
        reviewer="risk",
        reviewed_at=datetime(2026, 5, 28, tzinfo=UTC),
        expected_packet_hash=machine.packet_hash,
    )
    assert human.status == "human_approved"
    return packet


def test_approved_packet_runtime_config_builds_session(tmp_path: Path) -> None:
    packet = _approved_paper_packet(tmp_path)

    launch_plan_dir = tmp_path / "launch-plans"
    command = PromotionRuntimeConfigBuilder(launch_plan_dir=launch_plan_dir).paper_start_command(
        packet,
        operator_id="ops",
        idempotency_key="promotion-paper-1",
        reason="promotion to paper",
    )

    assert isinstance(command, StartRuntimeCommand)
    assert command.runtime_mode is RuntimeMode.PAPER_SIMULATED
    assert command.config_ref.startswith("launch-plan://")
    assert packet.promotion_candidate_id in command.config_ref
    launch_plans = tuple(launch_plan_dir.glob("*.json"))
    assert len(launch_plans) == 1
    plan_payload = json.loads(launch_plans[0].read_text(encoding="utf-8"))
    assert plan_payload["promotion_candidate_id"] == packet.promotion_candidate_id
    assert plan_payload["target_module"] == packet.target_module
    assert plan_payload["runtime"]["runtime_mode"] == RuntimeMode.PAPER_SIMULATED.value

    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=command.runtime_mode,
            account_id=AccountId(str(packet.runtime["account_id"])),
            initial_cash={"USD": Decimal("100000")},
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
    )

    result = start_runtime(command, session_builder=builder)

    assert result.status == "started"
    assert result.evidence["session_constructed"] is True
    assert isinstance(result.session, RuntimeSession)


def test_approved_live_observation_packet_builds_start_command_with_startup_decision(
    tmp_path: Path,
) -> None:
    packet = _approved_live_observation_packet(tmp_path)
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

    launch_plan_dir = tmp_path / "live-launch-plans"
    command = PromotionRuntimeConfigBuilder(launch_plan_dir=launch_plan_dir).live_start_command(
        packet,
        operator_id="ops",
        idempotency_key="promotion-live-observation-1",
        reason="promotion to live observation",
        startup_decision=startup_decision,
    )

    assert isinstance(command, StartRuntimeCommand)
    assert command.runtime_mode is RuntimeMode.LIVE_OBSERVATION
    assert command.startup_decision == startup_decision
    assert command.config_ref.startswith("launch-plan://")
    assert tuple(launch_plan_dir.glob("*.json"))
