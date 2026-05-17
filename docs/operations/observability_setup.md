# Observability setup

How to wire an external Prometheus / k8s setup to a QTS deployment.

## 1. Endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health/liveness` | none | restart-the-pod signal (process responsive) |
| `GET /health/readiness` | none | remove-from-LB signal (`200` if `HealthService.status == "ok"`, else `503`) |
| `GET /health/startup` | none | initial-boot grace period |
| `GET /health` | none | legacy alias of liveness |
| `GET /metrics` | none | Prometheus text-format scrape (OPT-15 / OPT-57) |

All five are whitelisted by `ApiSecurityMiddleware` (no bearer token
needed). Everything else under the API requires an authenticated principal
with the right scope.

## 2. Metrics inventory

### Counters (`RuntimeCounterMetric`)

| Name | Source |
|---|---|
| `market_data_events_total` | every `runtime.market_data` event |
| `market_data_stale_total` | every `runtime.market_data_stale` event |
| `market_data_subscription_failures_total` | every `market_data_subscription_failed` event, tagged by `reason_code` |
| `strategy_intents_total` | every strategy-emitted intent |
| `signal_conflicts_total` | every conflict resolution |
| `risk_rejections_total` | every `runtime.risk_rejected`, tagged by `reason_code` |
| `orders_submitted_total` | every `runtime.order_submitted` |
| `broker_rejections_total` | every `broker.order_rejected`, tagged by `reason_code` |
| `fills_total` | every `runtime.fill_applied` |
| `reconciliation_drifts_total` | every `runtime.reconciliation_drift` |
| `kill_switch_activations_total` | every `risk.kill_switch_activated` |
| `runtime_recovery_blocks_total` | every `runtime.recovery_blocked`, tagged by `reason_code` |

### Latency gauges (`RuntimeLatencyMetric`)

| Name | Source |
|---|---|
| `market_data_ingest_latency` | follow-up: actor-internal probe |
| `strategy_eval_latency` | OPT-57 sink-level delta between `runtime.market_data` and the first `runtime.signal_received` in the same bar |
| `signal_aggregation_latency` | follow-up |
| `risk_eval_latency` | follow-up |
| `order_manager_latency` | follow-up |
| `broker_submit_latency` | follow-up |
| `broker_ack_latency` | follow-up |
| `fill_to_account_apply_latency` | follow-up |

### Mailbox depth gauges

`queue.depth{name=...}` and `queue.oldest_lag_seconds{name=...}` — populated
by the actor-internal probe (deferred follow-up after OPT-57; not yet wired).

## 3. Alert rules

Eight alert rules ship in `configs/alerts/qts_alerts.yaml`, organized into
four groups. Drop the file into a Prometheus rule_files: directive.

| Alert | Severity | Metric | Default threshold |
|---|---|---|---|
| `KillSwitchActive` | page | `kill_switch_activations_total` | any activation in 5m |
| `ReconciliationDrift` | page | `reconciliation_drifts_total` | > 0 for 1m |
| `RuntimeRecoveryBlocked` | page | `runtime_recovery_blocks_total` | > 0 for 1m |
| `MarketDataStale` | page | `market_data_stale_total` | > 0 for 30s |
| `MarketDataSubscriptionFailure` | warn | `market_data_subscription_failures_total` | any in 5m |
| `BrokerRejectionRate` | warn | `broker_rejections_total` | rate > 0.01/s for 1m |
| `RiskRejectionRate` | warn | `risk_rejections_total` | rate > 0.1/s for 1m |
| `HighStrategyEvalLatency` | warn | `strategy_eval_latency` | > 200ms for 5m |

Each rule references a section of
`docs/operations/incident_runbook.md` via its `runbook_url` annotation.

## 4. Wiring checklist for a fresh deployment

1. Deploy the QTS API process; confirm `GET /metrics` returns a body when
   you hit it (no auth needed).
2. Add a Prometheus scrape job:
   ```yaml
   - job_name: qts
     metrics_path: /metrics
     static_configs:
       - targets: ["qts-api:8000"]
   ```
3. Load `configs/alerts/qts_alerts.yaml` into Prometheus
   `rule_files:`. Reload Prometheus.
4. Configure Alertmanager routing: severity `page` → on-call;
   severity `warn` → email/Slack.
5. Add k8s probes:
   ```yaml
   livenessProbe:
     httpGet: { path: /health/liveness, port: 8000 }
     periodSeconds: 10
   readinessProbe:
     httpGet: { path: /health/readiness, port: 8000 }
     periodSeconds: 5
   startupProbe:
     httpGet: { path: /health/startup, port: 8000 }
     periodSeconds: 5
     failureThreshold: 30
   ```

## 5. What is NOT in this baseline

Deliberately deferred to follow-up items:

- Grafana dashboard JSON — needs hands-on tuning against a real Grafana.
- Per-strategy / per-account metric labels — touches every
  `record_runtime_event` call site; do as OPT-58.E follow-up.
- Actor-internal latency probes (`market_data_ingest_latency`,
  `signal_aggregation_latency`, `risk_eval_latency`,
  `order_manager_latency`, `broker_submit_latency`,
  `broker_ack_latency`, `fill_to_account_apply_latency`).
- Mailbox depth gauge wiring — actor-internal access required.

These follow-ups stay in the backlog and land independently.
