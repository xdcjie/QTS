from __future__ import annotations


def test_strategy_default_hooks_are_noops() -> None:
    from qts.strategy_sdk.strategy import Strategy

    strategy = Strategy()

    strategy.initialize(None)
    strategy.on_bar(None, None)
    strategy.on_tick(None, None)
    strategy.on_timer(None, None)
    strategy.on_order_update(None, None)
    strategy.on_fill(None, None)


def test_strategy_hooks_can_be_overridden() -> None:
    from qts.strategy_sdk.strategy import Strategy

    class RecordingStrategy(Strategy):
        def __init__(self) -> None:
            self.seen = False

        def on_bar(self, ctx: object, bar: object) -> None:
            self.seen = True

    strategy = RecordingStrategy()
    strategy.on_bar(None, None)

    assert strategy.seen
