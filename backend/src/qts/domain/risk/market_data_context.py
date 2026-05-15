"""Market-data context carried into pre-trade risk checks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MarketDataRiskContext:
    """Provider permission and freshness state visible to order risk rules."""

    permission_state: str | None = None
    stale: bool = False
    evidence: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        """Return normalized market-data evidence for RiskDecision payloads."""
        payload = dict(self.evidence)
        payload.setdefault("permission_state", self.permission_state)
        payload.setdefault("stale", self.stale)
        return payload


__all__ = ["MarketDataRiskContext"]
