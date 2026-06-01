from __future__ import annotations


def test_context_module_exports_only_strategy_context() -> None:
    import qts.strategy_sdk.context as context_module

    assert context_module.__all__ == ["StrategyContext"]


def test_canonical_strategy_sdk_import_modules() -> None:
    from qts.strategy_sdk.orders import BracketSpec, OrderSpec, OrderType
    from qts.strategy_sdk.subscriptions import DataSubscription
    from qts.strategy_sdk.timers import TimerEvent, TimerSubscription

    assert BracketSpec.__name__ == "BracketSpec"
    assert OrderSpec.__name__ == "OrderSpec"
    assert OrderType.__name__ == "OrderType"
    assert DataSubscription.__name__ == "DataSubscription"
    assert TimerEvent.__name__ == "TimerEvent"
    assert TimerSubscription.__name__ == "TimerSubscription"
