# Signal Model V1

Signals are optional Strategy SDK forecasts. They describe a strategy view on an
`AssetRef`; they are not orders, fills, risk decisions, or portfolio state.

## Contract

A `Signal` contains:

- `asset`: the strategy-facing `AssetRef`;
- `direction`: `up`, `down`, or `flat`;
- `generated_at`: timezone-aware timestamp;
- `horizon`: positive forecast horizon;
- `source_model`: non-empty model or rule name;
- optional confidence, magnitude, weight, and group metadata.

`Signal` is a value object. Emitting a signal does not mutate account or
portfolio state and does not submit an order.

## Portfolio Construction

`PortfolioConstructionModel` consumes the pending signal batch and emits existing
`TargetIntent` instances. V1 includes `EqualWeightSignalPortfolioConstruction`,
which maps directional signals to percent targets using equal gross exposure:

- `up` -> positive percent target;
- `down` -> negative percent target;
- `flat` -> close target.

Direct target APIs remain supported for simple strategies:

```python
ctx.target_percent(asset, Decimal("0.5"))
ctx.target_quantity(asset, Decimal("100"))
ctx.target_value(asset, Decimal("50000"))
ctx.close(asset)
```

Strategies may use the optional signal path when they want a separate forecast
step:

```python
ctx.emit_signal(
    Signal(
        asset=asset,
        direction=SignalDirection.UP,
        generated_at=bar.end_time,
        horizon=timedelta(days=1),
        source_model="momentum-v1",
    )
)
ctx.construct_targets(EqualWeightSignalPortfolioConstruction())
```

`construct_targets(...)` clears the pending signal batch after emitting targets.
Strategies that emit and construct on every bar therefore do not reconstruct or
re-emit prior bar signals.

## Runtime Ownership

The trading path remains:

```text
Signal -> PortfolioConstructionModel -> TargetIntent -> RiskEngine -> OrderManagerActor -> ExecutionActor -> AccountActor
```

Risk checks, order lifecycle, execution, fills, and account mutation stay owned
by their existing runtime boundaries. Signal and portfolio-construction modules
must not import execution, risk, runtime, broker adapters, `ContractSpec`, or
`BrokerSymbolMapping`.
