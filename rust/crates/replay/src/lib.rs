//! Deterministic replay inputs for backtests and research trials.

use std::collections::BTreeSet;
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::str::FromStr;

use chrono::{DateTime, Datelike, Duration, NaiveDate, NaiveTime, Utc};
use chrono_tz::Tz;
use csv::{ReaderBuilder, StringRecord};
use qts_calendar::RegularSessionWindow;
use qts_data::{AlignmentMode, Timeframe};
use qts_domain::{Bar, BarInput, InstrumentId};
use rust_decimal::Decimal;
use serde_json::{json, Value};
use thiserror::Error;

/// Current crate version.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReplayConfig {
    pub dataset_hash: String,
    pub timeframe: String,
    pub start: Option<DateTime<Utc>>,
    pub end: Option<DateTime<Utc>>,
    pub roots: Vec<String>,
    pub symbols: Vec<String>,
    pub instrument_ids: Vec<String>,
    pub roll_policy: String,
    pub source_path: Option<String>,
}

impl ReplayConfig {
    pub fn cache_identity_seed(&self) -> String {
        let mut roots = self.roots.clone();
        let mut symbols = self.symbols.clone();
        let mut instrument_ids = self.instrument_ids.clone();
        roots.sort();
        symbols.sort();
        instrument_ids.sort();
        format!(
            "qts-replay:v1|dataset_hash={}|timeframe={}|start={}|end={}|roots={}|symbols={}|instrument_ids={}|roll_policy={}|source_path={}",
            self.dataset_hash,
            self.timeframe,
            optional_timestamp(self.start),
            optional_timestamp(self.end),
            roots.join(","),
            symbols.join(","),
            instrument_ids.join(","),
            self.roll_policy,
            self.source_path.clone().unwrap_or_default(),
        )
    }
}

#[derive(Clone, Debug)]
pub struct HistoricalCsvReplayConfig {
    pub source_csv: PathBuf,
    pub replay_config: ReplayConfig,
    pub exchange_timezone: Tz,
    pub session_open: NaiveTime,
    pub session_close: NaiveTime,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RollContractSpec {
    pub symbol: String,
    pub instrument_id: String,
    pub first_notice_day: NaiveDate,
    pub expiry: DateTime<Utc>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FirstNoticeRollSchedule {
    root_symbol: String,
    exchange: String,
    contracts: Vec<RollContractSpec>,
    roll_sessions_before_first_notice: u32,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RollSelection {
    pub continuous_instrument_id: String,
    pub root_symbol: String,
    pub exchange: String,
    pub session_date: NaiveDate,
    pub concrete_instrument_id: String,
    pub source_symbol: String,
    pub roll_policy: String,
    pub offset: usize,
}

impl FirstNoticeRollSchedule {
    pub fn new(
        root_symbol: String,
        exchange: String,
        contracts: Vec<RollContractSpec>,
        roll_sessions_before_first_notice: u32,
    ) -> Result<Self, RollError> {
        let root_symbol = root_symbol.trim().to_uppercase();
        if root_symbol.is_empty() {
            return Err(RollError::EmptyRoot);
        }
        let exchange = exchange.trim().to_uppercase();
        if exchange.is_empty() {
            return Err(RollError::EmptyExchange);
        }
        if roll_sessions_before_first_notice == 0 {
            return Err(RollError::InvalidRollSessionOffset);
        }
        if contracts.is_empty() {
            return Err(RollError::EmptyContracts);
        }
        let mut contracts = contracts
            .into_iter()
            .map(|contract| contract.normalized())
            .collect::<Result<Vec<_>, _>>()?;
        contracts
            .sort_by(|left, right| (left.expiry, &left.symbol).cmp(&(right.expiry, &right.symbol)));
        Ok(Self {
            root_symbol,
            exchange,
            contracts,
            roll_sessions_before_first_notice,
        })
    }

    pub fn select(
        &self,
        session_date: NaiveDate,
        offset: usize,
    ) -> Result<RollSelection, RollError> {
        let front_index = self
            .contracts
            .iter()
            .position(|contract| {
                session_date
                    < offset_business_sessions(
                        contract.first_notice_day,
                        -(self.roll_sessions_before_first_notice as i32),
                    )
            })
            .unwrap_or(self.contracts.len() - 1);
        let target_index = front_index + offset;
        let contract = self
            .contracts
            .get(target_index)
            .ok_or(RollError::OffsetOutOfRange)?;
        Ok(RollSelection {
            continuous_instrument_id: self.continuous_instrument_id(offset),
            root_symbol: self.root_symbol.clone(),
            exchange: self.exchange.clone(),
            session_date,
            concrete_instrument_id: contract.instrument_id.clone(),
            source_symbol: contract.symbol.clone(),
            roll_policy: "first_notice".to_string(),
            offset,
        })
    }

    fn continuous_instrument_id(&self, offset: usize) -> String {
        if offset == 0 {
            format!("CONTINUOUS_FUTURE.{}.{}", self.exchange, self.root_symbol)
        } else {
            format!(
                "CONTINUOUS_FUTURE.{}.{}.M{}",
                self.exchange,
                self.root_symbol,
                offset + 1
            )
        }
    }
}

impl RollContractSpec {
    fn normalized(self) -> Result<Self, RollError> {
        let symbol = self.symbol.trim().to_string();
        if symbol.is_empty() {
            return Err(RollError::EmptySymbol);
        }
        let instrument_id = self.instrument_id.trim().to_string();
        if instrument_id.is_empty() {
            return Err(RollError::EmptyInstrumentId);
        }
        Ok(Self {
            symbol,
            instrument_id,
            first_notice_day: self.first_notice_day,
            expiry: self.expiry,
        })
    }
}

impl RollSelection {
    pub fn to_json_value(&self) -> Value {
        json!({
            "continuous_instrument_id": self.continuous_instrument_id,
            "root_symbol": self.root_symbol,
            "exchange": self.exchange,
            "session_date": self.session_date.format("%Y-%m-%d").to_string(),
            "concrete_instrument_id": self.concrete_instrument_id,
            "source_symbol": self.source_symbol,
            "roll_policy": self.roll_policy,
            "offset": self.offset,
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReplayProvenance {
    pub cache_identity: String,
    pub dataset_hash: String,
    pub timeframe: String,
    pub roots: Vec<String>,
    pub symbols: Vec<String>,
    pub instrument_ids: Vec<String>,
    pub roll_policy: String,
    pub source_path: Option<String>,
}

#[derive(Clone, Debug)]
pub struct ReplayEvent {
    pub sequence: u64,
    pub visible_at: DateTime<Utc>,
    pub bar: Bar,
    pub provenance: ReplayProvenance,
}

#[derive(Clone, Debug)]
pub struct ReplayTape {
    config: ReplayConfig,
    cache_identity_seed: String,
    cache_identity: String,
    events: Vec<ReplayEvent>,
}

impl ReplayTape {
    pub fn from_bars(config: ReplayConfig, bars: Vec<Bar>) -> Result<Self, ReplayError> {
        let cache_identity_seed = config.cache_identity_seed();
        let cache_identity = stable_identity(&cache_identity_seed);
        let provenance = ReplayProvenance {
            cache_identity: cache_identity.clone(),
            dataset_hash: config.dataset_hash.clone(),
            timeframe: config.timeframe.clone(),
            roots: sorted_strings(&config.roots),
            symbols: sorted_strings(&config.symbols),
            instrument_ids: sorted_strings(&config.instrument_ids),
            roll_policy: config.roll_policy.clone(),
            source_path: config.source_path.clone(),
        };
        let instrument_filter = config
            .instrument_ids
            .iter()
            .cloned()
            .collect::<BTreeSet<_>>();
        let mut bars = bars
            .into_iter()
            .filter(|bar| {
                instrument_filter.is_empty()
                    || instrument_filter.contains(bar.instrument_id.as_str())
            })
            .filter(|bar| match config.start {
                Some(start) => bar.start_time >= start,
                None => true,
            })
            .filter(|bar| match config.end {
                Some(end) => bar.start_time < end,
                None => true,
            })
            .collect::<Vec<_>>();
        bars.sort_by(|left, right| {
            (
                left.end_time,
                left.instrument_id.as_str().to_string(),
                left.timeframe.clone(),
                left.start_time,
            )
                .cmp(&(
                    right.end_time,
                    right.instrument_id.as_str().to_string(),
                    right.timeframe.clone(),
                    right.start_time,
                ))
        });
        let events = bars
            .into_iter()
            .enumerate()
            .map(|(index, bar)| ReplayEvent {
                sequence: index as u64,
                visible_at: bar.end_time,
                bar,
                provenance: provenance.clone(),
            })
            .collect();
        Ok(Self {
            config,
            cache_identity_seed,
            cache_identity,
            events,
        })
    }

    pub fn events(&self) -> &[ReplayEvent] {
        &self.events
    }

    pub fn cache_identity(&self) -> &str {
        &self.cache_identity
    }

    pub fn cache_identity_seed(&self) -> &str {
        &self.cache_identity_seed
    }

    pub fn config(&self) -> &ReplayConfig {
        &self.config
    }

    pub fn to_json_value(&self) -> Value {
        json!({
            "cache_identity": self.cache_identity,
            "cache_identity_seed": self.cache_identity_seed,
            "config": {
                "dataset_hash": self.config.dataset_hash,
                "timeframe": self.config.timeframe,
                "start": self.config.start.map(timestamp_text),
                "end": self.config.end.map(timestamp_text),
                "roots": self.config.roots,
                "symbols": self.config.symbols,
                "instrument_ids": self.config.instrument_ids,
                "roll_policy": self.config.roll_policy,
                "source_path": self.config.source_path,
            },
            "events": self.events.iter().map(event_json).collect::<Vec<_>>(),
        })
    }

    pub fn write_json(&self, path: &Path) -> Result<(), ReplayError> {
        let mut file = File::create(path)?;
        writeln!(
            file,
            "{}",
            serde_json::to_string_pretty(&self.to_json_value())?
        )?;
        Ok(())
    }
}

pub fn replay_tape_from_historical_csv(
    config: &HistoricalCsvReplayConfig,
) -> Result<ReplayTape, ReplayError> {
    let timeframe = Timeframe::parse(&config.replay_config.timeframe)
        .map_err(|_| ReplayError::UnsupportedTimeframe(config.replay_config.timeframe.clone()))?;
    let session_window = RegularSessionWindow::new(
        config.exchange_timezone,
        config.session_open,
        config.session_close,
    );
    let mut reader = ReaderBuilder::new().from_path(&config.source_csv)?;
    let headers = reader.headers()?.clone();
    let indices = ColumnIndices::from_headers(&headers)?;
    let mut bars = Vec::new();
    for record in reader.records() {
        let record = record?;
        let start_time = parse_timestamp(field(&record, indices.ts_event)?)?;
        let end_time = end_time_for(start_time, &timeframe, &session_window)?;
        let instrument_id = InstrumentId::new(field(&record, indices.instrument_id)?.to_string())
            .map_err(|_| ReplayError::InvalidInstrumentId)?;
        let bar = Bar::new(BarInput {
            instrument_id,
            timeframe: timeframe.value().to_string(),
            start_time,
            end_time,
            open: parse_decimal(field(&record, indices.open)?)?,
            high: parse_decimal(field(&record, indices.high)?)?,
            low: parse_decimal(field(&record, indices.low)?)?,
            close: parse_decimal(field(&record, indices.close)?)?,
            volume: parse_decimal(field(&record, indices.volume)?)?,
            session_id: session_window.session_id_for(start_time),
            is_complete: true,
            is_partial: false,
            is_synthetic: false,
        })
        .map_err(|_| ReplayError::InvalidBar)?;
        bars.push(bar);
    }
    ReplayTape::from_bars(config.replay_config.clone(), bars)
}

fn end_time_for(
    start_time: DateTime<Utc>,
    timeframe: &Timeframe,
    session_window: &RegularSessionWindow,
) -> Result<DateTime<Utc>, ReplayError> {
    match timeframe.alignment() {
        AlignmentMode::Clock => timeframe
            .duration()
            .map(|duration| start_time + duration)
            .ok_or(ReplayError::MissingDuration),
        AlignmentMode::Session => {
            let session_id = session_window
                .session_id_for(start_time)
                .ok_or(ReplayError::MissingSessionId)?;
            Ok(session_window.interval_for_session_id(&session_id)?.end())
        }
    }
}

fn event_json(event: &ReplayEvent) -> Value {
    json!({
        "sequence": event.sequence,
        "visible_at": timestamp_text(event.visible_at),
        "bar": {
            "instrument_id": event.bar.instrument_id.as_str(),
            "timeframe": event.bar.timeframe,
            "start_time": timestamp_text(event.bar.start_time),
            "end_time": timestamp_text(event.bar.end_time),
            "open": decimal_text(event.bar.open),
            "high": decimal_text(event.bar.high),
            "low": decimal_text(event.bar.low),
            "close": decimal_text(event.bar.close),
            "volume": decimal_text(event.bar.volume),
            "session_id": event.bar.session_id,
            "is_complete": event.bar.is_complete,
            "is_partial": event.bar.is_partial,
            "is_synthetic": event.bar.is_synthetic,
        },
        "provenance": {
            "cache_identity": event.provenance.cache_identity,
            "dataset_hash": event.provenance.dataset_hash,
            "timeframe": event.provenance.timeframe,
            "roots": event.provenance.roots,
            "symbols": event.provenance.symbols,
            "instrument_ids": event.provenance.instrument_ids,
            "roll_policy": event.provenance.roll_policy,
            "source_path": event.provenance.source_path,
        }
    })
}

#[derive(Clone, Copy, Debug)]
struct ColumnIndices {
    ts_event: usize,
    instrument_id: usize,
    open: usize,
    high: usize,
    low: usize,
    close: usize,
    volume: usize,
}

impl ColumnIndices {
    fn from_headers(headers: &StringRecord) -> Result<Self, ReplayError> {
        Ok(Self {
            ts_event: required_column(headers, "ts_event")?,
            instrument_id: required_column(headers, "instrument_id")?,
            open: required_column(headers, "open")?,
            high: required_column(headers, "high")?,
            low: required_column(headers, "low")?,
            close: required_column(headers, "close")?,
            volume: required_column(headers, "volume")?,
        })
    }
}

fn required_column(headers: &StringRecord, name: &str) -> Result<usize, ReplayError> {
    headers
        .iter()
        .position(|column| column == name)
        .ok_or_else(|| ReplayError::MissingColumn(name.to_string()))
}

fn field(record: &StringRecord, index: usize) -> Result<&str, ReplayError> {
    record.get(index).ok_or(ReplayError::MalformedRow)
}

fn parse_timestamp(value: &str) -> Result<DateTime<Utc>, ReplayError> {
    Ok(DateTime::parse_from_rfc3339(value)?.with_timezone(&Utc))
}

fn parse_decimal(value: &str) -> Result<Decimal, ReplayError> {
    Decimal::from_str(value).map_err(|_| ReplayError::InvalidDecimal(value.to_string()))
}

fn stable_identity(seed: &str) -> String {
    format!("qts-replay-v1-{:016x}", fnv1a_64(seed.as_bytes()))
}

fn sorted_strings(values: &[String]) -> Vec<String> {
    let mut values = values.to_vec();
    values.sort();
    values
}

fn fnv1a_64(bytes: &[u8]) -> u64 {
    let mut hash = 0xcbf29ce484222325_u64;
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

fn optional_timestamp(value: Option<DateTime<Utc>>) -> String {
    value.map(timestamp_text).unwrap_or_default()
}

fn timestamp_text(value: DateTime<Utc>) -> String {
    value.to_rfc3339_opts(chrono::SecondsFormat::Nanos, true)
}

fn decimal_text(value: Decimal) -> String {
    value.normalize().to_string()
}

#[derive(Debug, Error)]
pub enum ReplayError {
    #[error("io error")]
    Io(#[from] std::io::Error),
    #[error("csv error")]
    Csv(#[from] csv::Error),
    #[error("json error")]
    Json(#[from] serde_json::Error),
    #[error("timestamp parse error")]
    Timestamp(#[from] chrono::ParseError),
    #[error("session error")]
    Session(#[from] qts_calendar::SessionError),
    #[error("unsupported timeframe: {0}")]
    UnsupportedTimeframe(String),
    #[error("missing clock timeframe duration")]
    MissingDuration,
    #[error("missing session id")]
    MissingSessionId,
    #[error("missing historical CSV column: {0}")]
    MissingColumn(String),
    #[error("malformed historical CSV row")]
    MalformedRow,
    #[error("invalid instrument id")]
    InvalidInstrumentId,
    #[error("invalid decimal: {0}")]
    InvalidDecimal(String),
    #[error("invalid bar")]
    InvalidBar,
}

#[derive(Debug, Error)]
pub enum RollError {
    #[error("root symbol must not be empty")]
    EmptyRoot,
    #[error("exchange must not be empty")]
    EmptyExchange,
    #[error("contract symbol must not be empty")]
    EmptySymbol,
    #[error("contract instrument id must not be empty")]
    EmptyInstrumentId,
    #[error("at least one roll contract is required")]
    EmptyContracts,
    #[error("roll_sessions_before_first_notice must be positive")]
    InvalidRollSessionOffset,
    #[error("roll offset exceeds available contracts")]
    OffsetOutOfRange,
}

fn offset_business_sessions(start: NaiveDate, offset: i32) -> NaiveDate {
    let step = if offset >= 0 { 1 } else { -1 };
    let mut remaining = offset.abs();
    let mut current = start;
    while remaining > 0 {
        current += Duration::days(i64::from(step));
        if current.weekday().number_from_monday() <= 5 {
            remaining -= 1;
        }
    }
    current
}

#[cfg(test)]
mod tests {
    use chrono::{Duration, TimeZone, Utc};
    use qts_domain::{Bar, BarInput, InstrumentId};
    use rust_decimal::Decimal;

    use super::{ReplayConfig, ReplayTape};

    #[test]
    fn replay_events_are_visible_at_bar_end_and_identity_is_stable(
    ) -> Result<(), Box<dyn std::error::Error>> {
        let start = Utc
            .with_ymd_and_hms(2026, 1, 6, 14, 30, 0)
            .single()
            .ok_or("time")?;
        let end = start + Duration::minutes(5);
        let bar = Bar::new(BarInput {
            instrument_id: InstrumentId::new("FUTURE.CME.GC.GCM26".to_string())?,
            timeframe: "5m".to_string(),
            start_time: start,
            end_time: end,
            open: Decimal::new(2000, 0),
            high: Decimal::new(2005, 0),
            low: Decimal::new(1999, 0),
            close: Decimal::new(2003, 0),
            volume: Decimal::new(10, 0),
            session_id: Some("2026-01-06".to_string()),
            is_complete: true,
            is_partial: false,
            is_synthetic: false,
        })?;
        let config = ReplayConfig {
            dataset_hash: "dataset-a".to_string(),
            timeframe: "5m".to_string(),
            start: Some(start),
            end: Some(end),
            roots: vec!["GC".to_string()],
            symbols: vec!["GCM26".to_string()],
            instrument_ids: vec!["FUTURE.CME.GC.GCM26".to_string()],
            roll_policy: "front".to_string(),
            source_path: Some("fixture.csv".to_string()),
        };

        let left = ReplayTape::from_bars(config.clone(), vec![bar.clone()])?;
        let right = ReplayTape::from_bars(config, vec![bar])?;

        assert_eq!(left.events()[0].visible_at, end);
        assert_eq!(left.cache_identity(), right.cache_identity());
        assert!(left
            .cache_identity_seed()
            .contains("dataset_hash=dataset-a"));
        assert!(left.cache_identity_seed().contains("timeframe=5m"));
        assert!(left.cache_identity_seed().contains("roll_policy=front"));
        assert_eq!(left.events()[0].provenance.timeframe, "5m");
        assert_eq!(left.events()[0].provenance.roots, vec!["GC"]);
        assert_eq!(left.events()[0].provenance.symbols, vec!["GCM26"]);
        assert_eq!(
            left.events()[0].provenance.instrument_ids,
            vec!["FUTURE.CME.GC.GCM26"]
        );
        Ok(())
    }
}
