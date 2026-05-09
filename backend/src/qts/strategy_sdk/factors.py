"""Strategy-facing factor factory."""

from __future__ import annotations

from dataclasses import dataclass

from qts.factors.momentum import MomentumFactor


@dataclass(frozen=True, slots=True)
class FactorFactory:
    """Factory for user-created factors."""

    def momentum(self, *, window: int) -> MomentumFactor:
        return MomentumFactor(window=window)


__all__ = ["FactorFactory"]
