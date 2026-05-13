# IBKR Adapter Decision

## Status

Selected integration scope: IBKR TWS/Gateway adapter boundary for paper trading, observation mode, and controlled live-readiness validation.

Current live-capital status: No-Go until the required external evidence is recorded.

## TWS API Client Implementation

Selected Python client: the official Interactive Brokers TWS API Python client
distributed with the IBKR TWS API download, exposed to this codebase only from
IBKR transport modules.

Rationale:

- IBKR documents TWS API as a TCP socket API for TWS or IB Gateway and lists a
  maintained Python offering among the official language implementations:
  <https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/>.
- IBKR's download page is the authoritative source for current TWS API Stable
  and Latest releases, including Python support in the current Latest package:
  <https://interactivebrokers.github.io/>.
- IBKR states that third-party wrappers such as `ib_insync` and `ib_async` are
  not the official support surface, and that IBKR advises use of its direct TWS
  API implementation when possible:
  <https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/>.

Dependency decision for this milestone: install the official IBKR TWS API Python
client from the IBKR API ZIP into the runtime environment for real Gateway
anchors and deployments. Do not add the PyPI `ibapi` package to
`project.dependencies`, because PyPI currently exposes an older non-current
package while IBKR documents the official distribution as the direct TWS API
download. The official source URL, version, ZIP subdirectory, and SHA256 are
recorded in `pyproject.toml` under `tool.qts.ibkr_api`; deployments install it
with `make install-ibkr-api`. The actual `ibapi` import must stay isolated
inside `qts.data.adapters` or `qts.execution.adapters` transport modules when
enabled, so core domain, runtime, strategy, risk, portfolio, and reconciliation
code never imports IBKR client objects.

## Selected Scope

IBKR is the selected first broker integration target for paper and live execution hardening. The integration is bounded by the existing architecture: market data and order execution remain separate adapters, separate configuration sections, separate client IDs, separate actor-facing boundaries, and separate event streams.

The selected scope includes:

- IBKR TWS/Gateway connectivity through internal adapter interfaces, not direct broker access from domain, runtime, strategy, risk, portfolio, or API code.
- A market-data adapter boundary that converts IBKR ticks, quotes, and bars into normalized internal market-data events.
- An order-execution adapter boundary that converts approved internal order requests into IBKR broker requests and converts broker callbacks into normalized execution reports.
- Broker symbol mapping only at adapter boundaries, with `InstrumentId` preserved internally.
- Account and broker identifiers confined to live configuration, adapter boundaries, reconciliation snapshots, and operational evidence.
- Separate market-data and order-execution client IDs.
- Observation mode that can connect and observe broker/account/market state without submitting live orders.
- Paper trading validation before any real-capital order submission.
- Submit, cancel, and replace behavior only for order types, time-in-force values, fractional behavior, shorting behavior, and instrument classes explicitly supported by recorded broker capabilities.
- Startup and periodic reconciliation of broker open orders, fills, positions, and account state against internal snapshots.
- Fail-closed behavior for unknown broker state, stale market data, unclassified reconciliation drift, missing permissions, incomplete configuration, or unsupported broker capabilities.

## Out Of Scope

The IBKR adapter decision does not approve or require:

- Direct use of IBKR objects or broker symbols in core domain models, Strategy SDK APIs, risk logic, portfolio accounting, or actor-owned state.
- A single combined IBKR adapter that mixes market data and order execution state.
- Live order submission before paper or observation evidence, reconciliation evidence, rollback evidence, and owner signoff are recorded.
- FIX connectivity, TWS UI automation, or non-IBKR broker integrations.
- Broker-specific strategy APIs or user strategy access to IBKR clients.
- High-frequency or latency-sensitive execution guarantees.
- Advanced IBKR algorithmic orders, basket orders, multi-leg option combos, option exercise workflows, securities lending workflows, or portfolio margin optimization.
- Automatic account mutation from broker callbacks. Broker callbacks must become normalized internal events and pass through `OrderManagerActor` and `AccountActor`.
- Automatic flattening or cancellation outside the approved order path.
- Secret storage in committed configuration.
- Production readiness approval. This document selects an adapter scope; it does not change the S4 No-Go decision.

## Required Evidence Before Live Trading

Live trading remains blocked until the following evidence is recorded and reviewed:

| Evidence area | Required record |
|---|---|
| Local verification | Latest `make check` result and S4 readiness lanes recorded. |
| IBKR environment | Target TWS/Gateway version, host, port, account, market-data subscriptions, account permissions, and separate client IDs validated. |
| Configuration safety | Live config validates broker, account, risk, calendar, kill-switch, market-data, order-execution, and secret references without committed credentials. |
| Market data | IBKR market-data adapter produces normalized ticks, quotes, and bars for target instruments with stale-data monitoring. |
| Order execution | IBKR execution adapter submits, cancels, replaces, and rejects only capability-supported orders through the approved internal order path. |
| Callback normalization | IBKR order status, execution, commission, error, disconnect, and reconnect callbacks are normalized before affecting internal state. |
| Risk gate | Evidence shows every live order request passes risk before broker submission and rejected orders are never submitted. |
| Reconciliation | Startup and periodic reconciliation compare broker open orders, fills, positions, and account state against internal snapshots, with no unclassified drift. |
| Observation or paper soak | At least one full regular trading session is recorded for the target strategy and instrument set, including event lag, queue depth, broker status, stale data, rejected orders, memory growth, restarts, and drift checks. |
| Paper-vs-live comparison | Paper decisions are compared against live market and broker state, and unexplained differences are resolved or formally accepted. |
| Kill switch | Kill-switch drill shows new orders are blocked and active orders are cancelled only through the approved order path. |
| Rollback | Rollback procedure is reviewed and a rollback drill records preserved event store, snapshots, logs, and broker reports. |
| Operations | Incident runbooks for broker disconnect, market-data outage, reconciliation mismatch, and kill switch activation are reviewed by operators. |
| Signoff | Engineering owner, operations owner, and risk owner approve the rollout checklist and capital limits. |

## Decision Rule

IBKR integration work may proceed inside this scope, but real order submission remains disabled until every required evidence record is complete. Any missing, stale, or conflicting evidence keeps the system in No-Go for live trading.
