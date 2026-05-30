"""Backtest runtime-topology manifest construction.

Owns resolving a backtest run's runtime topology (account/strategy identity +
manifest payload) from its ``BacktestRuntimeConfig``, with a deterministic
single-account/single-strategy default when no config-driven topology exists, so
the engine does not own runtime-topology presentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.core.ids import AccountId, RuntimeRunId, StrategyId
from qts.runtime.config import BacktestRuntimeConfig
from qts.runtime.topology import RuntimeTopologyBuilder, StrategyRuntimeSpec


@dataclass(frozen=True, slots=True)
class ResolvedBacktestTopology:
    """Resolved topology manifest payload + identity for a backtest run."""

    payload: dict[str, Any]
    account_id: AccountId
    strategy_id: StrategyId | None
    strategy_specs: tuple[StrategyRuntimeSpec, ...] | None


class BacktestRuntimeTopologyManifestBuilder:
    """Resolve the runtime-topology manifest payload + identity for a backtest run."""

    def resolve(
        self,
        *,
        backtest_runtime_config: BacktestRuntimeConfig | None,
        runtime_run_id: RuntimeRunId,
        default_account_id: AccountId,
        default_strategy_id: StrategyId,
    ) -> ResolvedBacktestTopology:
        """Return the topology payload + account/strategy identity for the run."""
        if backtest_runtime_config is None:
            return ResolvedBacktestTopology(
                payload=self._default_payload(
                    runtime_run_id=runtime_run_id,
                    account_id=default_account_id,
                    strategy_id=default_strategy_id,
                ),
                account_id=default_account_id,
                strategy_id=default_strategy_id,
                strategy_specs=None,
            )
        topology = RuntimeTopologyBuilder.from_backtest_config(
            backtest_runtime_config, runtime_run_id
        )
        account_id = topology.accounts[0].account_id if topology.accounts else default_account_id
        if len(topology.strategies) == 1:
            strategy_id: StrategyId | None = topology.strategies[0].strategy_id
        elif topology.strategies:
            strategy_id = None
        else:
            strategy_id = default_strategy_id
        return ResolvedBacktestTopology(
            payload=topology.to_manifest_payload(),
            account_id=account_id,
            strategy_id=strategy_id,
            strategy_specs=topology.strategies,
        )

    @staticmethod
    def _default_payload(
        *,
        runtime_run_id: RuntimeRunId,
        account_id: AccountId,
        strategy_id: StrategyId,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "run_id": runtime_run_id.value,
            "mode": "backtest",
            "accounts": [{"account_id": account_id.value}],
            "strategies": [{"strategy_id": strategy_id.value, "account_id": account_id.value}],
            "broker_routes": [],
            "market_data_routes": [],
        }
        payload["topology_hash"] = stable_json_hash(payload)
        return payload


__all__ = ["BacktestRuntimeTopologyManifestBuilder", "ResolvedBacktestTopology"]
