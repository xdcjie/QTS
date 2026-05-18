# ResearchBook API v1

`ResearchBook` is a read-only research facade for notebooks and scripts.

It may:
- load a configured `HistoricalCatalog`;
- request bounded historical bars through QTS historical data boundaries;
- return deterministic row-like research frames;
- expose dataset IDs for experiment manifests.

It must not:
- mutate portfolio, account, order, runtime, or broker state;
- parse source CSV rows directly;
- create orders or target intents;
- redefine sessions, roll rules, or bar intervals.
