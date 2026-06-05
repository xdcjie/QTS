use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::str::FromStr;

use chrono::{DateTime, Duration, NaiveTime, Utc};
use chrono_tz::Tz;
use csv::{ReaderBuilder, StringRecord, WriterBuilder};
use qts_calendar::RegularSessionWindow;
use qts_domain::{Bar, BarInput, InstrumentId};
use rust_decimal::Decimal;
use thiserror::Error;

use crate::aggregation::BarAggregator;
use crate::csv_index::write_historical_csv_index;
use crate::timeframe::{AlignmentMode, Timeframe};

pub const EXPECTED_HISTORICAL_COLUMNS: [&str; 10] = [
    "ts_event",
    "rtype",
    "publisher_id",
    "instrument_id",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "symbol",
];

#[derive(Clone, Debug)]
pub struct MaterializeConfig {
    pub root: String,
    pub source_csv: PathBuf,
    pub output_dir: PathBuf,
    pub timeframes: Vec<String>,
    pub exchange_timezone: Tz,
    pub session_open: NaiveTime,
    pub session_close: NaiveTime,
    pub overwrite: bool,
}

pub fn materialize_historical_csv(
    config: &MaterializeConfig,
) -> Result<Vec<PathBuf>, MaterializeError> {
    fs::create_dir_all(&config.output_dir)?;
    let mut outputs = Vec::new();
    let source_rows = read_source_rows(config)?;
    for timeframe_value in &config.timeframes {
        let output_path = config.output_dir.join(format!("{timeframe_value}.csv"));
        if output_path.exists() && !config.overwrite {
            return Err(MaterializeError::OutputExists(output_path));
        }
        if timeframe_value == "1m" {
            fs::copy(&config.source_csv, &output_path)?;
            write_historical_csv_index(&output_path)?;
            outputs.push(output_path);
            continue;
        }
        let timeframe = Timeframe::parse(timeframe_value)
            .map_err(|_| MaterializeError::UnsupportedTimeframe(timeframe_value.clone()))?;
        let mut bars = match timeframe.alignment() {
            AlignmentMode::Clock => {
                aggregate_clock_rows(&source_rows, &timeframe, config.exchange_timezone)?
            }
            AlignmentMode::Session => aggregate_daily_rows(&source_rows, &timeframe, config)?,
        };
        bars.sort_by(|left, right| {
            (
                left.bar.start_time,
                left.bar.instrument_id.as_str().to_string(),
                left.symbol.clone(),
            )
                .cmp(&(
                    right.bar.start_time,
                    right.bar.instrument_id.as_str().to_string(),
                    right.symbol.clone(),
                ))
        });
        write_rows(&output_path, &bars, &config.root)?;
        write_historical_csv_index(&output_path)?;
        outputs.push(output_path);
    }
    Ok(outputs)
}

fn read_source_rows(config: &MaterializeConfig) -> Result<Vec<SourceRow>, MaterializeError> {
    let session_window = RegularSessionWindow::new(
        config.exchange_timezone,
        config.session_open,
        config.session_close,
    );
    let mut reader = ReaderBuilder::new().from_path(&config.source_csv)?;
    let headers = reader.headers()?.clone();
    let indices = ColumnIndices::from_headers(&headers)?;
    let mut rows = Vec::new();
    for record in reader.records() {
        let record = record?;
        let start_time = parse_timestamp(field(&record, indices.ts_event)?)?;
        let session_id = session_window.session_id_for(start_time);
        let Some(session_id) = session_id else {
            continue;
        };
        let instrument_id = InstrumentId::new(field(&record, indices.instrument_id)?.to_string())
            .map_err(|_| MaterializeError::InvalidInstrumentId)?;
        let symbol = field(&record, indices.symbol)?.to_string();
        let bar = Bar::new(BarInput {
            instrument_id,
            timeframe: "1m".to_string(),
            start_time,
            end_time: start_time + Duration::minutes(1),
            open: parse_decimal(field(&record, indices.open)?)?,
            high: parse_decimal(field(&record, indices.high)?)?,
            low: parse_decimal(field(&record, indices.low)?)?,
            close: parse_decimal(field(&record, indices.close)?)?,
            volume: parse_decimal(field(&record, indices.volume)?)?,
            session_id: Some(session_id),
            is_complete: true,
            is_partial: false,
            is_synthetic: false,
        })
        .map_err(|_| MaterializeError::InvalidBar)?;
        rows.push(SourceRow { bar, symbol });
    }
    Ok(rows)
}

fn aggregate_clock_rows(
    rows: &[SourceRow],
    timeframe: &Timeframe,
    exchange_timezone: Tz,
) -> Result<Vec<OutputRow>, MaterializeError> {
    let mut aggregators: BTreeMap<String, BarAggregator> = BTreeMap::new();
    let mut symbols: BTreeMap<String, String> = BTreeMap::new();
    let mut output = Vec::new();
    for row in rows {
        let instrument = row.bar.instrument_id.as_str().to_string();
        symbols.insert(instrument.clone(), row.symbol.clone());
        let aggregator = match aggregators.get_mut(&instrument) {
            Some(value) => value,
            None => {
                aggregators.insert(
                    instrument.clone(),
                    BarAggregator::new(timeframe.clone(), exchange_timezone)?,
                );
                aggregators
                    .get_mut(&instrument)
                    .ok_or(MaterializeError::MissingAggregator)?
            }
        };
        for bar in aggregator.update(row.bar.clone())? {
            output.push(OutputRow {
                symbol: symbols
                    .get(bar.instrument_id.as_str())
                    .cloned()
                    .unwrap_or_else(|| symbol_from_instrument_id(bar.instrument_id.as_str())),
                bar,
            });
        }
    }
    for aggregator in aggregators.values_mut() {
        for bar in aggregator.finish()? {
            output.push(OutputRow {
                symbol: symbols
                    .get(bar.instrument_id.as_str())
                    .cloned()
                    .unwrap_or_else(|| symbol_from_instrument_id(bar.instrument_id.as_str())),
                bar,
            });
        }
    }
    Ok(output)
}

fn aggregate_daily_rows(
    rows: &[SourceRow],
    timeframe: &Timeframe,
    config: &MaterializeConfig,
) -> Result<Vec<OutputRow>, MaterializeError> {
    let session_window = RegularSessionWindow::new(
        config.exchange_timezone,
        config.session_open,
        config.session_close,
    );
    let mut states: BTreeMap<(String, String), DailyState> = BTreeMap::new();
    for row in rows {
        let session_id = row
            .bar
            .session_id
            .clone()
            .ok_or(MaterializeError::MissingSessionId)?;
        let key = (row.bar.instrument_id.as_str().to_string(), session_id);
        match states.get_mut(&key) {
            Some(state) => state.update(row),
            None => {
                states.insert(key, DailyState::from_row(row));
            }
        }
    }
    let mut output = Vec::new();
    for state in states.values() {
        let session_id = state.session_id.clone();
        let interval = session_window.interval_for_session_id(&session_id)?;
        output.push(OutputRow {
            symbol: state.symbol.clone(),
            bar: Bar::new(BarInput {
                instrument_id: state.instrument_id.clone(),
                timeframe: timeframe.value().to_string(),
                start_time: interval.start(),
                end_time: interval.end(),
                open: state.open,
                high: state.high,
                low: state.low,
                close: state.close,
                volume: state.volume,
                session_id: Some(session_id),
                is_complete: state.first_start == interval.start()
                    && state.last_end == interval.end(),
                is_partial: state.first_start != interval.start()
                    || state.last_end != interval.end(),
                is_synthetic: false,
            })
            .map_err(|_| MaterializeError::InvalidBar)?,
        });
    }
    Ok(output)
}

fn write_rows(path: &Path, rows: &[OutputRow], root: &str) -> Result<(), MaterializeError> {
    let mut writer = WriterBuilder::new()
        .terminator(csv::Terminator::Any(b'\n'))
        .from_path(path)?;
    writer.write_record(EXPECTED_HISTORICAL_COLUMNS)?;
    for row in rows {
        writer.write_record([
            timestamp_text(row.bar.start_time),
            String::new(),
            String::new(),
            row.bar.instrument_id.as_str().to_string(),
            decimal_text(row.bar.open),
            decimal_text(row.bar.high),
            decimal_text(row.bar.low),
            decimal_text(row.bar.close),
            decimal_text(row.bar.volume),
            if row.symbol.is_empty() {
                root.to_string()
            } else {
                row.symbol.clone()
            },
        ])?;
    }
    writer.flush()?;
    Ok(())
}

#[derive(Clone, Debug)]
struct SourceRow {
    bar: Bar,
    symbol: String,
}

#[derive(Clone, Debug)]
struct OutputRow {
    bar: Bar,
    symbol: String,
}

#[derive(Clone, Debug)]
struct DailyState {
    instrument_id: InstrumentId,
    symbol: String,
    session_id: String,
    first_start: DateTime<Utc>,
    last_end: DateTime<Utc>,
    open: Decimal,
    high: Decimal,
    low: Decimal,
    close: Decimal,
    volume: Decimal,
}

impl DailyState {
    fn from_row(row: &SourceRow) -> Self {
        Self {
            instrument_id: row.bar.instrument_id.clone(),
            symbol: row.symbol.clone(),
            session_id: row.bar.session_id.clone().unwrap_or_default(),
            first_start: row.bar.start_time,
            last_end: row.bar.end_time,
            open: row.bar.open,
            high: row.bar.high,
            low: row.bar.low,
            close: row.bar.close,
            volume: row.bar.volume,
        }
    }

    fn update(&mut self, row: &SourceRow) {
        self.last_end = row.bar.end_time;
        self.high = self.high.max(row.bar.high);
        self.low = self.low.min(row.bar.low);
        self.close = row.bar.close;
        self.volume += row.bar.volume;
    }
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
    symbol: usize,
}

impl ColumnIndices {
    fn from_headers(headers: &StringRecord) -> Result<Self, MaterializeError> {
        Ok(Self {
            ts_event: required_column(headers, "ts_event")?,
            instrument_id: required_column(headers, "instrument_id")?,
            open: required_column(headers, "open")?,
            high: required_column(headers, "high")?,
            low: required_column(headers, "low")?,
            close: required_column(headers, "close")?,
            volume: required_column(headers, "volume")?,
            symbol: required_column(headers, "symbol")?,
        })
    }
}

fn required_column(headers: &StringRecord, name: &str) -> Result<usize, MaterializeError> {
    headers
        .iter()
        .position(|column| column == name)
        .ok_or_else(|| MaterializeError::MissingColumn(name.to_string()))
}

fn field(record: &StringRecord, index: usize) -> Result<&str, MaterializeError> {
    record.get(index).ok_or(MaterializeError::MalformedRow)
}

fn parse_timestamp(value: &str) -> Result<DateTime<Utc>, MaterializeError> {
    Ok(DateTime::parse_from_rfc3339(value)?.with_timezone(&Utc))
}

fn parse_decimal(value: &str) -> Result<Decimal, MaterializeError> {
    Decimal::from_str(value).map_err(|_| MaterializeError::InvalidDecimal(value.to_string()))
}

fn timestamp_text(value: DateTime<Utc>) -> String {
    value.to_rfc3339_opts(chrono::SecondsFormat::Nanos, true)
}

fn decimal_text(value: Decimal) -> String {
    value.normalize().to_string()
}

fn symbol_from_instrument_id(value: &str) -> String {
    value.rsplit('.').next().unwrap_or(value).to_string()
}

#[derive(Debug, Error)]
pub enum MaterializeError {
    #[error("io error")]
    Io(#[from] std::io::Error),
    #[error("csv error")]
    Csv(#[from] csv::Error),
    #[error("timestamp parse error")]
    Timestamp(#[from] chrono::ParseError),
    #[error("aggregation error")]
    Aggregation(#[from] crate::aggregation::AggregationError),
    #[error("index error")]
    Index(#[from] crate::csv_index::CsvIndexError),
    #[error("session error")]
    Session(#[from] qts_calendar::SessionError),
    #[error("unsupported timeframe: {0}")]
    UnsupportedTimeframe(String),
    #[error("output exists: {0}")]
    OutputExists(PathBuf),
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
    #[error("missing aggregation state")]
    MissingAggregator,
    #[error("missing session id")]
    MissingSessionId,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn materializes_five_minute_csv_and_index() -> Result<(), Box<dyn std::error::Error>> {
        let dir = std::env::temp_dir().join(format!("qts-rs-materialize-{}", std::process::id()));
        let source_dir = dir.join("source");
        let output_dir = dir.join("out");
        fs::create_dir_all(&source_dir)?;
        let source = source_dir.join("gc.csv");
        fs::write(
            &source,
            "ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol\n\
             2026-01-06T14:30:00.000000000Z,,,FUTURE.CME.GC.GCM26,100,101,99,100,1,GCM26\n\
             2026-01-06T14:31:00.000000000Z,,,FUTURE.CME.GC.GCM26,100,102,98,101,2,GCM26\n\
             2026-01-06T14:32:00.000000000Z,,,FUTURE.CME.GC.GCM26,101,103,97,102,3,GCM26\n\
             2026-01-06T14:33:00.000000000Z,,,FUTURE.CME.GC.GCM26,102,104,96,103,4,GCM26\n\
             2026-01-06T14:34:00.000000000Z,,,FUTURE.CME.GC.GCM26,103,105,95,104,5,GCM26\n",
        )?;

        let outputs = materialize_historical_csv(&MaterializeConfig {
            root: "GC".to_string(),
            source_csv: source,
            output_dir: output_dir.clone(),
            timeframes: vec!["5m".to_string()],
            exchange_timezone: chrono_tz::US::Eastern,
            session_open: NaiveTime::from_hms_opt(18, 0, 0).ok_or("open")?,
            session_close: NaiveTime::from_hms_opt(17, 0, 0).ok_or("close")?,
            overwrite: true,
        })?;

        assert_eq!(outputs, vec![output_dir.join("5m.csv")]);
        let csv_text = fs::read_to_string(output_dir.join("5m.csv"))?;
        assert!(csv_text.contains("2026-01-06T14:30:00.000000000Z"));
        assert!(csv_text.contains(",100,105,95,104,15,GCM26"));
        assert!(output_dir.join("5m.csv.index.json").exists());
        Ok(())
    }
}
