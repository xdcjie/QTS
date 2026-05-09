from __future__ import annotations

from decimal import Decimal


def test_strategy_registry_resolves_same_class_for_multiple_instances() -> None:
    from qts.application.strategy_lifecycle import StrategyInstance, StrategyRegistry
    from qts.core.ids import AccountId, StrategyId
    from qts.strategy_sdk import Strategy

    class DemoStrategy(Strategy):
        pass

    registry = StrategyRegistry()
    registry.register("examples.DemoStrategy", DemoStrategy)
    first = StrategyInstance(
        strategy_id=StrategyId("strategy-001"),
        class_path="examples.DemoStrategy",
        account_id=AccountId("acct-001"),
        allocation=Decimal("0.5"),
    )
    second = StrategyInstance(
        strategy_id=StrategyId("strategy-002"),
        class_path="examples.DemoStrategy",
        account_id=AccountId("acct-002"),
        allocation=Decimal("0.5"),
    )

    assert registry.resolve(first.class_path) is DemoStrategy
    assert registry.resolve(second.class_path) is DemoStrategy


def test_strategy_lifecycle_service_start_stop_status_are_deterministic() -> None:
    from qts.application.services import StrategyLifecycleService
    from qts.application.strategy_lifecycle import StrategyInstance, StrategyStatus
    from qts.core.ids import AccountId, StrategyId

    strategy_id = StrategyId("strategy-001")
    service = StrategyLifecycleService(
        (
            StrategyInstance(
                strategy_id=strategy_id,
                class_path="examples.DemoStrategy",
                account_id=AccountId("acct-001"),
            ),
        )
    )

    assert service.status(strategy_id) is StrategyStatus.STOPPED
    assert service.start(strategy_id) is StrategyStatus.RUNNING
    assert service.stop(strategy_id) is StrategyStatus.STOPPED
