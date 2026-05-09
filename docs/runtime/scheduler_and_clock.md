# Scheduler and Clock

Use explicit clock abstractions.

- Backtest uses replay clock.
- Paper/live uses wall-clock-backed runtime clock.
- Strategy schedules must be evaluated in the correct exchange/calendar context.
- Tests should use fake clocks, not wall-clock sleeps.
