"""Kill-switch scope model and risk enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from qts.core.ids import AccountId, BrokerId, StrategyId
from qts.domain.risk import OrderRiskRequest, RiskDecision


class KillSwitchScopeType(StrEnum):
    """Supported kill-switch scopes."""

    GLOBAL = "global"
    ACCOUNT = "account"
    STRATEGY = "strategy"
    BROKER = "broker"


@dataclass(frozen=True, slots=True)
class KillSwitchScope:
    """Kill-switch scope identity."""

    scope_type: KillSwitchScopeType
    scope_id: str | None = None

    @classmethod
    def global_scope(cls) -> KillSwitchScope:
        """Perform global_scope."""
        return cls(KillSwitchScopeType.GLOBAL)

    @classmethod
    def account(cls, account_id: AccountId) -> KillSwitchScope:
        """Perform account."""
        return cls(KillSwitchScopeType.ACCOUNT, account_id.value)

    @classmethod
    def strategy(cls, strategy_id: StrategyId) -> KillSwitchScope:
        """Perform strategy."""
        return cls(KillSwitchScopeType.STRATEGY, strategy_id.value)

    @classmethod
    def broker(cls, broker_id: BrokerId) -> KillSwitchScope:
        """Perform broker."""
        return cls(KillSwitchScopeType.BROKER, broker_id.value)

    def reason_code(self) -> str:
        """Perform reason_code."""
        return f"KILL_SWITCH_{self.scope_type.value.upper()}"


@dataclass(frozen=True, slots=True)
class KillSwitchState:
    """Kill-switch activation state."""

    scope: KillSwitchScope
    active: bool
    reason: str


class KillSwitchRegistry:
    """Auditable in-memory kill-switch registry."""

    def __init__(self) -> None:
        self._states: dict[KillSwitchScope, KillSwitchState] = {}

    def activate(self, scope: KillSwitchScope, *, reason: str) -> KillSwitchState:
        """Perform activate."""
        if not reason.strip():
            raise ValueError("reason must not be empty")
        state = KillSwitchState(scope=scope, active=True, reason=reason)
        self._states[scope] = state
        return state

    def deactivate(self, scope: KillSwitchScope, *, reason: str) -> KillSwitchState:
        """Perform deactivate."""
        if not reason.strip():
            raise ValueError("reason must not be empty")
        state = KillSwitchState(scope=scope, active=False, reason=reason)
        self._states[scope] = state
        return state

    def check_order(
        self,
        request: OrderRiskRequest,
        *,
        account_id: AccountId,
        strategy_id: StrategyId | None,
        broker_id: BrokerId,
    ) -> RiskDecision:
        """Perform check_order."""
        del request
        for scope in self._matching_scopes(account_id, strategy_id, broker_id):
            state = self._states.get(scope)
            if state is not None and state.active:
                return RiskDecision.rejected(
                    state.scope.reason_code(),
                    state.reason,
                    rule_id="kill_switch",
                )
        return RiskDecision.approve(rule_id="kill_switch")

    @staticmethod
    def _matching_scopes(
        account_id: AccountId,
        strategy_id: StrategyId | None,
        broker_id: BrokerId,
    ) -> tuple[KillSwitchScope, ...]:
        scopes = [
            KillSwitchScope.global_scope(),
            KillSwitchScope.account(account_id),
            KillSwitchScope.broker(broker_id),
        ]
        if strategy_id is not None:
            scopes.append(KillSwitchScope.strategy(strategy_id))
        return tuple(scopes)


__all__ = [
    "KillSwitchRegistry",
    "KillSwitchScope",
    "KillSwitchScopeType",
    "KillSwitchState",
]
