//! Deterministic backtest execution core.
//!
//! This crate currently exposes a parity-mode kernel used for Python/Rust
//! parity gates. It is not a production replacement for the Python Strategy
//! SDK/Risk/Order/Execution/Account path.

use std::collections::BTreeMap;
use std::fs::{self, File};
use std::io::Write;
use std::path::{Path, PathBuf};

use chrono::{DateTime, Utc};
use qts_replay::{ReplayEvent, ReplayTape};
use rust_decimal::Decimal;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use thiserror::Error;

/// Current crate version.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FillTiming {
    NextBarOpen,
}

impl FillTiming {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::NextBarOpen => "next_bar_open",
        }
    }
}

#[derive(Clone, Debug)]
pub struct EngineBacktestConfig {
    pub initial_cash: Decimal,
    pub quantity: Decimal,
    pub fill_timing: FillTiming,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineManifest {
    pub mode: String,
    pub fill_timing: String,
    pub replay_cache_identity: String,
    pub processed_bars: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineOrder {
    pub order_id: String,
    pub submitted_at: DateTime<Utc>,
    pub instrument_id: String,
    pub quantity: Decimal,
    pub risk_status: String,
    pub status: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineFill {
    pub order_id: String,
    pub filled_at: DateTime<Utc>,
    pub instrument_id: String,
    pub quantity: Decimal,
    pub price: Decimal,
    pub account_id: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineEquityPoint {
    pub timestamp: DateTime<Utc>,
    pub cash: Decimal,
    pub position_quantity: Decimal,
    pub positions: BTreeMap<String, Decimal>,
    pub equity: Decimal,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineMetrics {
    pub processed_bars: u64,
    pub orders: u64,
    pub fills: u64,
    pub final_cash: Decimal,
    pub final_equity: Decimal,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineBacktestReport {
    pub manifest: EngineManifest,
    pub events: Vec<EngineRuntimeEvent>,
    pub orders: Vec<EngineOrder>,
    pub fills: Vec<EngineFill>,
    pub equity_curve: Vec<EngineEquityPoint>,
    pub metrics: EngineMetrics,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineRuntimeEvent {
    pub sequence: u64,
    pub kind: String,
    pub timestamp: DateTime<Utc>,
    pub order_id: String,
    pub account_id: String,
    pub instrument_id: String,
    pub payload: BTreeMap<String, String>,
}

impl EngineBacktestReport {
    pub fn to_json_value(&self) -> Value {
        json!({
            "manifest": {
                "engine_id": "rust",
                "engine_mode": self.manifest.mode,
                "reference_engine": "python",
                "candidate_replaces_reference": false,
                "mode": self.manifest.mode,
                "fill_timing": self.manifest.fill_timing,
                "replay_cache_identity": self.manifest.replay_cache_identity,
                "processed_bars": self.manifest.processed_bars,
            },
            "events": self.events.iter().map(runtime_event_json).collect::<Vec<_>>(),
            "orders": self.orders.iter().map(order_json).collect::<Vec<_>>(),
            "fills": self.fills.iter().map(fill_json).collect::<Vec<_>>(),
            "equity_curve": self.equity_curve.iter().map(equity_json).collect::<Vec<_>>(),
            "metrics": {
                "processed_bars": self.metrics.processed_bars,
                "orders": self.metrics.orders,
                "fills": self.metrics.fills,
                "final_cash": decimal_text(self.metrics.final_cash),
                "final_equity": decimal_text(self.metrics.final_equity),
            },
            "engine_id": "rust",
            "engine_mode": self.manifest.mode,
            "reference_engine": "python",
            "candidate_replaces_reference": false,
        })
    }

    pub fn write_artifacts(
        &self,
        output_dir: &Path,
    ) -> Result<EngineBacktestArtifacts, BacktestError> {
        fs::create_dir_all(output_dir)?;
        let run_id = self.run_id();
        let artifact_rows = self.artifact_rows();
        let mut artifact_paths = BTreeMap::new();
        let mut artifact_metadata = BTreeMap::new();
        for (kind, rows) in artifact_rows {
            let path = output_dir.join(format!("{run_id}.{kind}.ndjson"));
            let hash = write_ndjson(&path, &rows)?;
            artifact_metadata.insert(
                kind.to_string(),
                json!({
                    "path": path.display().to_string(),
                    "rows": rows.len(),
                    "sha256": hash,
                }),
            );
            artifact_paths.insert(kind.to_string(), path);
        }
        let report_hash = hash_json(&json!({
            "run_id": run_id,
            "metrics": self.metrics_json(),
            "processed_bars": self.metrics.processed_bars,
            "artifacts": artifact_metadata,
        }))?;
        let now = "1970-01-01T00:00:00.000000000Z";
        let manifest = json!({
            "run_id": run_id,
            "runtime_instance_id": run_id,
            "runtime_mode": "backtest",
            "market_data_environment": "historical_replay",
            "execution_environment": "simulated",
            "account_environment": "simulated",
            "order_submission_permission": false,
            "event_schema_version": "1",
            "artifact_schema_version": "1",
            "config_hash": self.manifest.replay_cache_identity,
            "topology_hash": "sha256:engine-parity-topology",
            "startup_checklist_hash": "sha256:not-applicable",
            "platform_baseline_version": "qts-platform-v1",
            "created_at": now,
            "finalized_at": now,
            "source_commit": "engine-parity",
            "operator_identity_hash": "sha256:not-applicable",
            "report_hash": report_hash,
            "dataset_metadata": [{
                "dataset_id": self.manifest.replay_cache_identity,
                "file_hash": self.manifest.replay_cache_identity,
                "row_count": self.metrics.processed_bars,
                "first_ts": self.equity_curve.first().map(|point| timestamp_text(point.timestamp)).unwrap_or_default(),
                "last_ts": self.equity_curve.last().map(|point| timestamp_text(point.timestamp)).unwrap_or_default(),
                "timezone": "UTC",
                "adjustment_mode": "raw",
            }],
            "cost_model": {},
            "processed_bars": self.metrics.processed_bars,
            "warmup_bars": 0,
            "trading_bars": self.metrics.processed_bars,
            "brokerage_model": "simulated_engine",
            "execution_assumptions": {
                "fill_model_name": "next_bar_open",
                "fill_model_version": "1",
                "slippage_model": "zero",
                "commission_model": "zero",
                "partial_fill_policy": "none",
                "broker_capability_model": {"broker_id": "simulated-engine"},
            },
            "risk_config_hash": "sha256:engine-parity-risk",
            "contract_economics_hash": "sha256:engine-parity-contract-economics",
            "margin_policy_hash": "sha256:engine-parity-margin-policy",
            "metrics": self.metrics_json(),
            "statistics": self.statistics_json(),
            "statistics_hash": hash_json(&self.statistics_json())?,
            "artifacts": artifact_metadata,
            "engine_id": "rust",
            "engine_mode": self.manifest.mode,
            "reference_engine": "python",
            "candidate_replaces_reference": false,
        });
        let manifest_path = output_dir.join(format!("{run_id}.manifest.json"));
        write_json(&manifest_path, &manifest)?;
        let summary = json!({
            "run_id": run_id,
            "status": "completed",
            "report_hash": report_hash,
            "manifest_path": manifest_path.display().to_string(),
            "metrics": self.metrics_json(),
            "processed_bars": self.metrics.processed_bars,
            "engine_id": "rust",
            "engine_mode": self.manifest.mode,
            "reference_engine": "python",
            "candidate_replaces_reference": false,
        });
        let summary_path = output_dir.join(format!("{run_id}.summary.json"));
        write_json(&summary_path, &summary)?;
        Ok(EngineBacktestArtifacts {
            run_id,
            summary_path,
            manifest_path,
            artifact_paths,
        })
    }

    fn run_id(&self) -> String {
        let suffix = self
            .manifest
            .replay_cache_identity
            .rsplit('-')
            .next()
            .unwrap_or("engine");
        format!("rs-bt-{suffix}")
    }

    fn metrics_json(&self) -> Value {
        json!({
            "processed_bars": self.metrics.processed_bars,
            "orders": self.metrics.orders,
            "fills": self.metrics.fills,
            "final_cash": decimal_text(self.metrics.final_cash),
            "final_equity": decimal_text(self.metrics.final_equity),
        })
    }

    fn statistics_json(&self) -> Value {
        json!({
            "processed_bars": self.metrics.processed_bars,
            "orders": self.metrics.orders,
            "fills": self.metrics.fills,
        })
    }

    fn artifact_rows(&self) -> BTreeMap<&'static str, Vec<Value>> {
        let mut rows = BTreeMap::new();
        rows.insert(
            "events",
            self.events.iter().map(runtime_event_json).collect(),
        );
        rows.insert("orders", self.orders.iter().map(order_json).collect());
        rows.insert("fills", self.fills.iter().map(fill_json).collect());
        rows.insert(
            "trade_ledger",
            self.fills.iter().map(trade_ledger_json).collect(),
        );
        rows.insert(
            "equity_curve",
            self.equity_curve.iter().map(equity_json).collect(),
        );
        rows.insert("statistics", vec![self.statistics_json()]);
        rows
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineBacktestArtifacts {
    pub run_id: String,
    pub summary_path: PathBuf,
    pub manifest_path: PathBuf,
    pub artifact_paths: BTreeMap<String, PathBuf>,
}

pub struct BacktestEngine;

impl BacktestEngine {
    pub fn run(
        tape: &ReplayTape,
        config: &EngineBacktestConfig,
    ) -> Result<EngineBacktestReport, BacktestError> {
        if config.fill_timing != FillTiming::NextBarOpen {
            return Err(BacktestError::UnsupportedFillTiming);
        }
        let processed_bars = tape.events().len() as u64;
        let mut orders = Vec::new();
        let mut fills = Vec::new();
        let mut runtime_events = Vec::new();
        let mut equity_curve = Vec::new();
        let mut cash = config.initial_cash;
        let mut position_quantity = Decimal::ZERO;
        let mut positions = BTreeMap::new();
        let mut final_equity = config.initial_cash;
        let Some(first_event) = tape.events().first() else {
            return Ok(empty_report(
                tape,
                config,
                processed_bars,
                cash,
                final_equity,
            ));
        };
        let order_id = "engine-order-1".to_string();
        let instrument_id = first_event.bar.instrument_id.as_str().to_string();
        orders.push(EngineOrder {
            order_id: order_id.clone(),
            submitted_at: first_event.visible_at,
            instrument_id: instrument_id.clone(),
            quantity: config.quantity,
            risk_status: "accepted".to_string(),
            status: "accepted".to_string(),
        });
        runtime_events.push(runtime_event(
            runtime_events.len() as u64,
            "risk.accepted",
            first_event.visible_at,
            &order_id,
            &instrument_id,
            [("quantity", decimal_text(config.quantity))],
        ));
        runtime_events.push(runtime_event(
            runtime_events.len() as u64,
            "order.accepted",
            first_event.visible_at,
            &order_id,
            &instrument_id,
            [("status", "accepted".to_string())],
        ));
        let fill_event = next_bar_event(tape.events(), first_event);
        for event in tape.events() {
            if fills.is_empty()
                && fill_event
                    .map(|candidate| candidate.sequence == event.sequence)
                    .unwrap_or(false)
            {
                let fill = EngineFill {
                    order_id: order_id.clone(),
                    filled_at: event.bar.start_time,
                    instrument_id: instrument_id.clone(),
                    quantity: config.quantity,
                    price: event.bar.open,
                    account_id: "simulated-engine-account".to_string(),
                };
                cash -= fill.quantity * fill.price;
                position_quantity = fill.quantity;
                positions.insert(instrument_id.clone(), position_quantity);
                if let Some(order) = orders.first_mut() {
                    order.status = "filled".to_string();
                }
                runtime_events.push(runtime_event(
                    runtime_events.len() as u64,
                    "execution.filled",
                    fill.filled_at,
                    &order_id,
                    &instrument_id,
                    [("price", decimal_text(fill.price))],
                ));
                runtime_events.push(runtime_event(
                    runtime_events.len() as u64,
                    "account.updated",
                    fill.filled_at,
                    &order_id,
                    &instrument_id,
                    [
                        ("cash", decimal_text(cash)),
                        ("position_quantity", decimal_text(position_quantity)),
                    ],
                ));
                fills.push(fill);
            }
            if event.bar.instrument_id.as_str() == instrument_id {
                final_equity = cash + position_quantity * event.bar.close;
            }
            equity_curve.push(EngineEquityPoint {
                timestamp: event.visible_at,
                cash,
                position_quantity,
                positions: positions.clone(),
                equity: final_equity,
            });
        }
        Ok(EngineBacktestReport {
            manifest: EngineManifest {
                mode: "shadow".to_string(),
                fill_timing: config.fill_timing.as_str().to_string(),
                replay_cache_identity: tape.cache_identity().to_string(),
                processed_bars,
            },
            events: runtime_events,
            orders,
            fills,
            equity_curve,
            metrics: EngineMetrics {
                processed_bars,
                orders: 1,
                fills: if fill_event.is_some() { 1 } else { 0 },
                final_cash: cash,
                final_equity,
            },
        })
    }
}

fn next_bar_event<'a>(
    events: &'a [ReplayEvent],
    first_event: &ReplayEvent,
) -> Option<&'a ReplayEvent> {
    events.iter().find(|event| {
        event.bar.instrument_id == first_event.bar.instrument_id
            && event.bar.start_time >= first_event.visible_at
            && event.sequence > first_event.sequence
    })
}

fn empty_report(
    tape: &ReplayTape,
    config: &EngineBacktestConfig,
    processed_bars: u64,
    cash: Decimal,
    final_equity: Decimal,
) -> EngineBacktestReport {
    EngineBacktestReport {
        manifest: EngineManifest {
            mode: "shadow".to_string(),
            fill_timing: config.fill_timing.as_str().to_string(),
            replay_cache_identity: tape.cache_identity().to_string(),
            processed_bars,
        },
        events: Vec::new(),
        orders: Vec::new(),
        fills: Vec::new(),
        equity_curve: Vec::new(),
        metrics: EngineMetrics {
            processed_bars,
            orders: 0,
            fills: 0,
            final_cash: cash,
            final_equity,
        },
    }
}

fn order_json(order: &EngineOrder) -> Value {
    json!({
        "order_id": order.order_id,
        "submitted_at": timestamp_text(order.submitted_at),
        "instrument_id": order.instrument_id,
        "quantity": decimal_text(order.quantity),
        "risk_status": order.risk_status,
        "status": order.status,
    })
}

fn fill_json(fill: &EngineFill) -> Value {
    json!({
        "fill_id": format!("{}-fill-1", fill.order_id),
        "order_id": fill.order_id,
        "filled_at": timestamp_text(fill.filled_at),
        "instrument_id": fill.instrument_id,
        "side": "buy",
        "quantity": decimal_text(fill.quantity),
        "price": decimal_text(fill.price),
        "commission": "0",
        "slippage": "0",
        "account_id": fill.account_id,
    })
}

fn trade_ledger_json(fill: &EngineFill) -> Value {
    json!({
        "order_id": fill.order_id,
        "fill_id": format!("{}-fill-1", fill.order_id),
        "instrument_id": fill.instrument_id,
        "side": "buy",
        "quantity": decimal_text(fill.quantity),
        "fill_price": decimal_text(fill.price),
        "commission": "0",
        "slippage": "0",
        "filled_at": timestamp_text(fill.filled_at),
        "account_id": fill.account_id,
    })
}

fn equity_json(point: &EngineEquityPoint) -> Value {
    json!({
        "timestamp": timestamp_text(point.timestamp),
        "cash": decimal_text(point.cash),
        "position_quantity": decimal_text(point.position_quantity),
        "positions": point.positions.iter().map(|(instrument_id, quantity)| {
            (instrument_id.clone(), decimal_text(*quantity))
        }).collect::<BTreeMap<_, _>>(),
        "equity": decimal_text(point.equity),
    })
}

fn runtime_event_json(event: &EngineRuntimeEvent) -> Value {
    json!({
        "sequence_no": event.sequence,
        "kind": event.kind,
        "timestamp": timestamp_text(event.timestamp),
        "order_id": event.order_id,
        "account_id": event.account_id,
        "instrument_id": event.instrument_id,
        "payload": event.payload,
    })
}

fn runtime_event<const N: usize>(
    sequence: u64,
    kind: &str,
    timestamp: DateTime<Utc>,
    order_id: &str,
    instrument_id: &str,
    payload: [(&str, String); N],
) -> EngineRuntimeEvent {
    EngineRuntimeEvent {
        sequence,
        kind: kind.to_string(),
        timestamp,
        order_id: order_id.to_string(),
        account_id: "simulated-engine-account".to_string(),
        instrument_id: instrument_id.to_string(),
        payload: payload
            .into_iter()
            .map(|(key, value)| (key.to_string(), value))
            .collect(),
    }
}

fn timestamp_text(value: DateTime<Utc>) -> String {
    value.to_rfc3339_opts(chrono::SecondsFormat::Nanos, true)
}

fn decimal_text(value: Decimal) -> String {
    value.normalize().to_string()
}

fn write_ndjson(path: &Path, rows: &[Value]) -> Result<String, BacktestError> {
    let mut file = File::create(path)?;
    for row in rows {
        writeln!(file, "{}", serde_json::to_string(row)?)?;
    }
    hash_file(path)
}

fn write_json(path: &Path, value: &Value) -> Result<(), BacktestError> {
    let mut file = File::create(path)?;
    writeln!(file, "{}", serde_json::to_string_pretty(value)?)?;
    Ok(())
}

fn hash_file(path: &Path) -> Result<String, BacktestError> {
    let bytes = fs::read(path)?;
    Ok(format!("sha256:{}", hex_sha256(&bytes)))
}

fn hash_json(value: &Value) -> Result<String, BacktestError> {
    Ok(format!(
        "sha256:{}",
        hex_sha256(serde_json::to_string(value)?.as_bytes())
    ))
}

fn hex_sha256(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[derive(Debug, Error)]
pub enum BacktestError {
    #[error("io error")]
    Io(#[from] std::io::Error),
    #[error("json error")]
    Json(#[from] serde_json::Error),
    #[error("unsupported fill timing")]
    UnsupportedFillTiming,
}

#[cfg(test)]
mod tests {
    use chrono::{Duration, TimeZone, Utc};
    use qts_domain::{Bar, BarInput, InstrumentId};
    use qts_replay::{ReplayConfig, ReplayTape};
    use rust_decimal::Decimal;

    use super::{BacktestEngine, EngineBacktestConfig, FillTiming};

    #[test]
    fn parity_backtest_defaults_to_next_bar_open_fill_timing(
    ) -> Result<(), Box<dyn std::error::Error>> {
        let start = Utc
            .with_ymd_and_hms(2026, 1, 6, 14, 30, 0)
            .single()
            .ok_or("time")?;
        let first = bar(start, Decimal::new(2000, 0), Decimal::new(2001, 0))?;
        let second = bar(
            start + Duration::minutes(5),
            Decimal::new(2002, 0),
            Decimal::new(2003, 0),
        )?;
        let tape = ReplayTape::from_bars(
            ReplayConfig {
                dataset_hash: "dataset-a".to_string(),
                timeframe: "5m".to_string(),
                start: Some(start),
                end: Some(start + Duration::minutes(10)),
                roots: vec!["GC".to_string()],
                symbols: vec!["GCM26".to_string()],
                instrument_ids: vec!["FUTURE.CME.GC.GCM26".to_string()],
                roll_policy: "front".to_string(),
                source_path: Some("fixture.csv".to_string()),
            },
            vec![first, second],
        )?;

        let report = BacktestEngine::run(
            &tape,
            &EngineBacktestConfig {
                initial_cash: Decimal::new(100_000, 0),
                quantity: Decimal::new(1, 0),
                fill_timing: FillTiming::NextBarOpen,
            },
        )?;

        assert_eq!(report.orders.len(), 1);
        assert_eq!(report.fills.len(), 1);
        assert_eq!(report.fills[0].filled_at, start + Duration::minutes(5));
        assert_eq!(report.fills[0].price, Decimal::new(2002, 0));
        assert_eq!(report.metrics.final_equity, Decimal::new(100_001, 0));
        assert_eq!(report.manifest.mode, "shadow");
        Ok(())
    }

    #[test]
    fn parity_backtest_records_risk_order_execution_and_account_state_flow(
    ) -> Result<(), Box<dyn std::error::Error>> {
        let start = Utc
            .with_ymd_and_hms(2026, 1, 6, 14, 30, 0)
            .single()
            .ok_or("time")?;
        let tape = ReplayTape::from_bars(
            ReplayConfig {
                dataset_hash: "dataset-a".to_string(),
                timeframe: "5m".to_string(),
                start: Some(start),
                end: Some(start + Duration::minutes(10)),
                roots: vec!["GC".to_string()],
                symbols: vec!["GCM26".to_string()],
                instrument_ids: vec!["FUTURE.CME.GC.GCM26".to_string()],
                roll_policy: "front".to_string(),
                source_path: Some("fixture.csv".to_string()),
            },
            vec![
                bar(start, Decimal::new(2000, 0), Decimal::new(2001, 0))?,
                bar(
                    start + Duration::minutes(5),
                    Decimal::new(2002, 0),
                    Decimal::new(2003, 0),
                )?,
            ],
        )?;

        let report = BacktestEngine::run(
            &tape,
            &EngineBacktestConfig {
                initial_cash: Decimal::new(100_000, 0),
                quantity: Decimal::new(1, 0),
                fill_timing: FillTiming::NextBarOpen,
            },
        )?;

        let payload = report.to_json_value();
        let events = payload["events"].as_array().ok_or("events")?;
        let event_kinds = events
            .iter()
            .filter_map(|event| event["kind"].as_str())
            .collect::<Vec<_>>();
        assert_eq!(
            event_kinds,
            vec![
                "risk.accepted",
                "order.accepted",
                "execution.filled",
                "account.updated"
            ]
        );
        assert_eq!(payload["orders"][0]["status"], "filled");
        assert_eq!(payload["orders"][0]["risk_status"], "accepted");
        assert_eq!(
            payload["fills"][0]["account_id"],
            "simulated-engine-account"
        );
        assert_eq!(
            payload["equity_curve"][1]["positions"]["FUTURE.CME.GC.GCM26"],
            "1"
        );
        Ok(())
    }

    fn bar(
        start: chrono::DateTime<Utc>,
        open: Decimal,
        close: Decimal,
    ) -> Result<Bar, Box<dyn std::error::Error>> {
        Ok(Bar::new(BarInput {
            instrument_id: InstrumentId::new("FUTURE.CME.GC.GCM26".to_string())?,
            timeframe: "5m".to_string(),
            start_time: start,
            end_time: start + Duration::minutes(5),
            open,
            high: open.max(close),
            low: open.min(close),
            close,
            volume: Decimal::new(10, 0),
            session_id: Some("2026-01-06".to_string()),
            is_complete: true,
            is_partial: false,
            is_synthetic: false,
        })?)
    }
}
