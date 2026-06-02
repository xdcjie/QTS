"""Shared execution cost assumptions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SimulatedExecutionCostModel:
    """Execution fee and slippage assumptions for simulated adapters."""

    fixed_commission_per_contract: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Validate and normalize decimal inputs."""

        object.__setattr__(
            self,
            "fixed_commission_per_contract",
            Decimal(str(self.fixed_commission_per_contract)),
        )
        object.__setattr__(self, "slippage_bps", Decimal(str(self.slippage_bps)))
        if self.fixed_commission_per_contract < Decimal("0"):
            raise ValueError("fixed_commission_per_contract must be non-negative")
        if self.slippage_bps < Decimal("0"):
            raise ValueError("slippage_bps must be non-negative")

    def to_payload(self) -> dict[str, str]:
        """Serialize cost assumptions for hashing and reporting."""

        return {
            "fixed_commission_per_contract": str(self.fixed_commission_per_contract),
            "slippage_bps": str(self.slippage_bps),
        }

    @property
    def slippage_model(self) -> str:
        """Describe whether slippage is modeled."""

        return "zero" if self.slippage_bps == Decimal("0") else "basis_points"

    @property
    def commission_model(self) -> str:
        """Describe commission handling for reports."""

        if self.fixed_commission_per_contract == Decimal("0"):
            return "zero"
        return "fixed_per_contract"


BacktestCostModel = SimulatedExecutionCostModel


__all__ = ["BacktestCostModel", "SimulatedExecutionCostModel"]
