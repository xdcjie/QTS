# Reviewed Factor to Strategy Implementation Gate

Accepted factor review is not executable promotion. A reviewed `FactorSpec`
may create only a non-executable implementation task packet until a developer
implements code, writes tests, and passes review.

## Scaffold an implementation task

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml implementation task --factor-spec runs/research/quickstart/reviewed_factor.yaml --output-dir runs/research/quickstart/implementation_task
```

The packet contains:

1. `implementation_task.json` with review status, intended module names, and
   `runtime_promotion_allowed: false`.
2. `ai_prompt.md` describing the implementation contract.
3. `factor_template.py` for a `qts.factors.*` implementation.
4. `strategy_template.py` for a Strategy SDK strategy.
5. `test_no_lookahead_template.py` for the first regression test.

## Boundary rules

Implementation work must preserve these boundaries:

1. Factor code belongs under `qts.factors.*` and must not import broker,
   execution, order, account, or runtime actor internals.
2. Strategy code must use the Strategy SDK surface: `Strategy`,
   `StrategyContext`, `AssetRef`, data views, and target intent APIs.
3. Direct paper/live promotion is forbidden by this gate.
4. No-lookahead tests are required before executable strategy promotion.
