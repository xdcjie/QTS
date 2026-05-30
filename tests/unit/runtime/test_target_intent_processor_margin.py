"""Wiring test: TargetIntentProcessor populates margin context from the calculator (DR-005)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision
from qts.risk.margin.calculator import MarginCalculator

from tests.support.risk_runtime_harness import RiskRuntimeHarness


class _CapturingRule:
    """Risk rule that records the request it receives and always approves."""

    rule_id = "capture"

    def __init__(self) -> None:
        self.last_request: OrderRiskRequest | None = None

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        self.last_request = request
        return RiskDecision.approve(rule_id=self.rule_id)


def test_processor_populates_signed_delta_and_margin_fields() -> None:
    capture = _CapturingRule()
    harness = RiskRuntimeHarness(
        rules=[capture],
        multiplier=Decimal("100"),
        initial_cash=Decimal("1000000"),
        margin_calculator=MarginCalculator(initial_margin_rate=Decimal("0.05")),
    )

    harness.submit(target_quantity="2", when=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), price="100")

    request = capture.last_request
    assert request is not None
    assert request.signed_quantity_delta == Decimal("2")
    assert request.current_position == Decimal("0")
    # No open positions -> available margin equals account equity (cash).
    assert request.available_margin == Decimal("1000000")
    # Incremental initial margin for 2 contracts: 2 * 100 * 100 * 0.05 = 1000.
    assert request.projected_initial_margin == Decimal("1000")
