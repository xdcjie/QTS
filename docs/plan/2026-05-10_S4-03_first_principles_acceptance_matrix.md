# 2026-05-10 S4-03 First-Principles Acceptance Matrix

This matrix defines correctness anchors that S4 tasks must preserve.

## Time and Calendar

| Area | First-principles truth | Acceptance test |
|---|---|---|
| Session | Exchange session is a domain fact | Calendar tests use exchange-defined opens/closes |
| Timezone | Timezone is representation, not truth | UTC/ET/CST conversion does not change session count |
| Interval | Bars and sessions use `[start, end)` | Boundary timestamp belongs to next bucket |
| Intraday bars | `<1d` bars are clock-aligned in exchange time | `1m -> 5m` creates `[00,05)`, `[05,10)` buckets |
| Daily bars | `1d` means trading session, not 24h | COMEX daily bar uses `[ET 18:00, ET 17:00)` |
| COMEX Gold | Normal 23h session has 1380 1m bars | Anchor test asserts 1380 excluding special sessions |
| Partial bars | Partial bars must be explicit | Session close flush marks partial intraday bar |

## Identity and Instruments

| Area | First-principles truth | Acceptance test |
|---|---|---|
| Internal identity | Internal systems use `InstrumentId` | Domain objects reject raw broker symbol identity |
| Broker symbol | Broker symbols are boundary mapping | Adapter tests verify mapping isolation |
| Continuous futures | Continuous contracts are not directly tradable | Order creation rejects continuous future references |
| Options | Option identity requires underlying, expiry, strike, right | Contract construction validates required fields |
| Contract spec | Multiplier/tick/lot are contract facts | PnL and order rounding use ContractSpec |

## Backtest Correctness

| Area | First-principles truth | Acceptance test |
|---|---|---|
| Time slicing | Backtest cannot see future data | DataView historical reads end at current clock |
| Determinism | Same inputs produce same outputs | Replay test compares event stream/report hash |
| Costs | Fill assumptions are explicit model inputs | Report includes commission/slippage/latency model |
| Provenance | Result is tied to dataset | Report includes dataset ID/version/normalization policy |
| Strategy parity | Same strategy semantics across modes | Reference strategy runs unchanged in backtest and paper |

## Accounting Correctness

| Area | First-principles truth | Acceptance test |
|---|---|---|
| Stock value | `qty * price` | Accounting anchor test |
| Futures PnL | `contracts * price_diff * multiplier` | Accounting anchor test |
| Option premium | `contracts * option_price * multiplier` | Accounting anchor test |
| Duplicate fills | Fill processing is idempotent | Duplicate fill does not double count |
| Cash reservation | Pending orders reserve available funds | Reservation lifecycle test |
| Realized vs unrealized | Realized PnL changes only through closing/fill events | Accounting state transition test |

## Order and Broker Correctness

| Area | First-principles truth | Acceptance test |
|---|---|---|
| Order state | State machine controls lifecycle | Invalid transition rejected |
| Broker reports | Reports may be duplicated/out of order | State machine remains valid |
| Broker boundary | Broker callback cannot mutate portfolio | Integration test enforces OrderManager path |
| Fill path | Fill must pass through OrderManager before account update | Integration flow test |
| Cancel semantics | Cancel may race with fill | Race tests cover fill after cancel request |

## Risk and Safety

| Area | First-principles truth | Acceptance test |
|---|---|---|
| Risk gate | Orders pass risk before broker | Rejected order never submitted |
| Fail closed | Safety-critical unknowns block trading | Missing price/margin/calendar blocks order |
| Kill switch | Kill switch blocks new orders and cancels active orders | Kill switch integration test |
| Stale data | Stale data cannot generate unsafe orders | Stale data risk test |
| Limits | Limits are explicit and audited | RiskDecision includes reason and rule ID |

## Recovery and Reconciliation

| Area | First-principles truth | Acceptance test |
|---|---|---|
| Broker truth | Live state reconciles to broker truth | Startup reconciliation test |
| Event replay | Replay is deterministic | Replayed state equals snapshot |
| No double counting | Recovery must not duplicate fills | Restart with same fill is idempotent |
| Pending orders | Pending orders are reconciled | Pending order restart test |
| Mismatch handling | Mismatches are explicit | Reconciliation mismatch test |

## Operations

| Area | First-principles truth | Acceptance test |
|---|---|---|
| Auditability | Every order must be explainable | Trace includes signal, risk, order, fill |
| Observability | Runtime health must be visible | Metrics expose lag, queue, risk, broker health |
| Incident response | Operators need safe procedures | Runbooks and drills exist |
| Deployment safety | Live config must be validated | Live mode refuses incomplete config |
