# Backtest Rules

This module owns historical simulation runtime.

Rules:

- Backtest must use the same Strategy SDK as paper/live trading.
- Backtest DataView must be time-sliced and must not expose future data.
- Simulated broker fills must go through the same OrderManager and portfolio update flow where practical.
- Fill models must be explicit and testable.
- Add integration tests for bar-to-fill-to-portfolio flows.
- Do not place shared session, instrument, or futures roll resolution rules here.
  Backtest may configure and call shared registry/session services, but live and
  paper must be able to use the same business semantics.
