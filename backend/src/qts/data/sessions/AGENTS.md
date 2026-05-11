# Session Data Rules

This package owns reusable market session helpers.

Allowed here:

- Generic exchange-time session window definitions.
- Half-open session membership helpers.
- Session filtering for bars and market data.

Not allowed here:

- Product-specific session constants unless supplied by provider/config data.
- Historical CSV parsing.
- Backtest runtime orchestration.
- Broker adapter behavior.

Product-specific calendar/session providers belong in `qts.registry.providers`
or explicit configuration data.
