# Historical Data Rules

This package owns historical data source boundaries only.

Allowed here:

- Historical data config and catalog resolution.
- Historical chain file parsing.
- Historical CSV schema, timestamp parsing, and row-to-bar conversion.
- Historical market data replay service and historical source validation.

Not allowed here:

- Generic exchange session definitions or session membership rules.
- Continuous future roll selection or roll resolution shared by live/backtest.
- Runtime order, risk, portfolio, or strategy behavior.
- Test/anchor fixture generation helpers.

Shared session behavior belongs in `qts.data.sessions`.
Shared futures roll behavior belongs in `qts.registry.future_roll`.
