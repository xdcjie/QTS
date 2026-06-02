# Reporting Boundary

## Machine artifacts

Machine-readable artifacts own deterministic evidence, manifests, and hashes.
`BacktestArtifactWriter` writes promotion-facing backtest evidence, including
contract economics and margin policy hashes.

## Human reports

Report writers own human/operator summaries derived from completed artifacts.
`BacktestReportWriter` is a compatibility report writer over the backtest
artifact boundary. `BrokerRuntimeReportWriter` and
`BrokerRuntimeEventReporter` own broker runtime evidence reports and event-log
summaries. Reporting code is read-only: it must not mutate runtime, order,
account, risk, or strategy state.
