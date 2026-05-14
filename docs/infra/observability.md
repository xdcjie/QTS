# Observability

Observability must support debugging and audit.

Required dimensions:

- event_id
- correlation_id
- causation_id
- account_id
- strategy_id
- instrument_id
- order_id
- broker_id

Use structured logging. Metrics and tracing can be added after MVP.

Runtime event envelopes also carry `parent_event_id` when an event is part of a
tree of related runtime events. Order, risk, and fill runtime events require a
`correlation_id` so an incident can be traced across strategy intent, risk
decision, order submission, broker acknowledgement, fill handling, and account
mutation.

Standard runtime counters live in `RuntimeCounterMetric`; latency names live in
`RuntimeLatencyMetric`. Operational incidents should use
`OperationalErrorCode` and emit payloads with a stable `reason_code`.

Operational dashboards should consume `OperationalDashboardSnapshot`, which
standardizes these sections:

- runtime state
- subscriptions
- open orders
- positions
- cash
- risk status
- broker connection state
- reconciliation status
