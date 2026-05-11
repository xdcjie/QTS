# Dependency Rules

## Allowed direction

See `module_boundaries.md` for ownership rules at the package and subpackage
level. Dependency direction alone is not enough: a module can import only
allowed dependencies and still be in the wrong owner package.

```text
core
  <- domain
  <- registry / data / portfolio / risk / execution
  <- runtime
  <- backtest / application
  <- api / workers
  <- frontend
```

More specifically:

- `domain` may depend on `core` only.
- `registry` may depend on `core` and `domain`.
- `data` may depend on `core`, `domain`, and `registry`.
- `portfolio` may depend on `core`, `domain`, and `registry`.
- `risk` may depend on `core`, `domain`, `portfolio`, and `registry`.
- `execution` may depend on `core`, `domain`, and `registry`.
- `runtime` may depend on domain services but must preserve actor boundaries.
- `backtest` may depend on runtime, data, execution, and strategy_sdk.
- `strategy_sdk` may depend on core/domain readonly types but not runtime/execution/risk internals.
- `application` orchestrates use cases.
- `api` calls application services.
- `frontend` calls API only.

Provider-specific market data adapters live behind the data layer boundary.
Provider-specific order execution adapters live behind the execution layer
boundary. If the same provider supplies both services, such as IBKR for paper
and live trading, the adapters still remain separate modules and do not share
mutable trading state.

## Forbidden dependencies

- `domain -> api`
- `domain -> runtime`
- `domain -> order execution adapter`
- `domain -> market data adapter`
- `strategy_sdk -> order execution adapter`
- `strategy_sdk -> market data adapter`
- `strategy_sdk -> actor internals`
- `api -> actor internals`
- `frontend -> trading logic`

## Automated guardrails

`make guardrails` enforces the high-risk subset of these rules with static
checks:

- `core` may not import any upper QTS layer.
- `domain` may import only `qts.core` and `qts.domain`.
- `strategy_sdk` may not import runtime, execution, risk, registry, data,
  backtest, application, API, or workers.
- API code may not import actor internals or `OrderManager` internals directly.
- Market-data adapters may not import execution, risk, portfolio, or runtime.
- Order-execution adapters may not import data.
- Shared roll/session/resolution modules may not live under source-specific
  packages such as `qts.backtest` or `qts.data.historical`.

When a new valid boundary is introduced, update this document, the guardrail
script, and the guardrail tests in the same change.

## Rationale

This prevents infrastructure concerns from contaminating financial domain semantics and keeps user strategy APIs stable.
