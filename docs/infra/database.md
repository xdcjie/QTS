# Database

MVP can use memory or local files. Future persistence may include:

- Event store
- Account snapshots
- Order history
- Fills
- Market data cache
- Backtest results

Domain models should not depend on database ORM classes.
