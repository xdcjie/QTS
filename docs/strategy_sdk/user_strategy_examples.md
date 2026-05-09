# User Strategy Examples

Example minimal strategy:

```python
from qts.strategy_sdk import Strategy

class MovingAverageCross(Strategy):
    def initialize(self, ctx):
        self.asset = ctx.symbol("AAPL")
        self.fast = ctx.indicator.sma(self.asset, 20)
        self.slow = ctx.indicator.sma(self.asset, 60)

    def on_bar(self, ctx, data):
        if not (self.fast.ready and self.slow.ready):
            return
        if self.fast.value > self.slow.value:
            ctx.target_percent(self.asset, 1.0)
        else:
            ctx.close(self.asset)
```
