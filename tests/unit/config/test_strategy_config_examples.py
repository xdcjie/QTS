from __future__ import annotations

from decimal import Decimal

import yaml  # type: ignore[import-untyped]


def test_backtest_config_parses_two_strategy_instances() -> None:
    from qts.application.strategy_lifecycle import StrategyInstance
    from qts.core.ids import AccountId, StrategyId

    with open("configs/backtest.yaml", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    instances = tuple(
        StrategyInstance(
            strategy_id=StrategyId(item["strategy_id"]),
            class_path=item["class_path"],
            account_id=AccountId(item["account_id"]),
            allocation=Decimal(item["allocation"]),
            enabled=bool(item["enabled"]),
            params=item["params"],
        )
        for item in payload["strategies"]
    )

    assert len(instances) == 2
    assert {instance.params["symbol"] for instance in instances} == {"AAPL", "MSFT"}
