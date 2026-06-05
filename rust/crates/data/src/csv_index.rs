use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

use chrono::{DateTime, Utc};
use serde_json::json;
use thiserror::Error;

pub const INDEX_VERSION: i64 = 1;
pub const DEFAULT_TIMESTAMP_COLUMN: &str = "ts_event";

pub fn write_historical_csv_index(path: &Path) -> Result<PathBuf, CsvIndexError> {
    let output_path = path.with_extension(format!(
        "{}.index.json",
        path.extension()
            .and_then(|value| value.to_str())
            .unwrap_or_default()
    ));
    let file = File::open(path)?;
    let mut reader = BufReader::new(file);
    let mut byte_offset: u64 = 0;
    let mut header = String::new();
    let header_bytes = reader.read_line(&mut header)?;
    if header_bytes == 0 {
        return Err(CsvIndexError::EmptyCsv(path.to_path_buf()));
    }
    byte_offset += header_bytes as u64;
    let header_offset = byte_offset;
    let columns = header
        .trim_end_matches(['\r', '\n'])
        .split(',')
        .map(str::trim)
        .collect::<Vec<_>>();
    let timestamp_index = columns
        .iter()
        .position(|column| *column == DEFAULT_TIMESTAMP_COLUMN)
        .ok_or(CsvIndexError::MissingTimestampColumn)?;
    let mut buckets = Vec::new();
    let mut previous_timestamp: Option<DateTime<Utc>> = None;
    let mut current_bucket_date: Option<String> = None;
    let mut row_count: u64 = 0;
    loop {
        let row_offset = byte_offset;
        let mut line = String::new();
        let line_bytes = reader.read_line(&mut line)?;
        if line_bytes == 0 {
            break;
        }
        byte_offset += line_bytes as u64;
        if line.trim().is_empty() {
            continue;
        }
        let fields = line
            .trim_end_matches(['\r', '\n'])
            .split(',')
            .collect::<Vec<_>>();
        let timestamp_text = fields
            .get(timestamp_index)
            .ok_or(CsvIndexError::MalformedRow)?;
        let timestamp = parse_timestamp(timestamp_text)?;
        if let Some(previous) = previous_timestamp {
            if timestamp < previous {
                return Err(CsvIndexError::OutOfOrder);
            }
        }
        let bucket_date = timestamp.date_naive().to_string();
        if current_bucket_date.as_deref() != Some(bucket_date.as_str()) {
            buckets.push(json!({
                "date": bucket_date,
                "offset": row_offset,
                "row_index": row_count,
            }));
            current_bucket_date = Some(timestamp.date_naive().to_string());
        }
        previous_timestamp = Some(timestamp);
        row_count += 1;
    }
    let payload = json!({
        "buckets": buckets,
        "granularity": "day",
        "header_offset": header_offset,
        "row_count": row_count,
        "source_path": path.to_string_lossy(),
        "timestamp_column": DEFAULT_TIMESTAMP_COLUMN,
        "version": INDEX_VERSION,
    });
    let mut output = File::create(&output_path)?;
    writeln!(output, "{}", serde_json::to_string(&payload)?)?;
    Ok(output_path)
}

fn parse_timestamp(value: &str) -> Result<DateTime<Utc>, CsvIndexError> {
    Ok(DateTime::parse_from_rfc3339(value)?.with_timezone(&Utc))
}

#[derive(Debug, Error)]
pub enum CsvIndexError {
    #[error("io error")]
    Io(#[from] std::io::Error),
    #[error("json error")]
    Json(#[from] serde_json::Error),
    #[error("timestamp parse error")]
    Timestamp(#[from] chrono::ParseError),
    #[error("historical CSV is empty: {0}")]
    EmptyCsv(PathBuf),
    #[error("timestamp column not found")]
    MissingTimestampColumn,
    #[error("historical CSV row has fewer columns than header")]
    MalformedRow,
    #[error("historical CSV timestamps are out of order")]
    OutOfOrder,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn writes_python_compatible_daily_index() -> Result<(), Box<dyn std::error::Error>> {
        let dir = std::env::temp_dir().join(format!("qts-rs-index-{}", std::process::id()));
        fs::create_dir_all(&dir)?;
        let path = dir.join("gc.csv");
        fs::write(
            &path,
            "ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol\n\
             2026-01-02T14:30:00.000000000Z,,,FUTURE.CME.GC.GCM26,1,1,1,1,1,GCM26\n\
             2026-01-03T14:30:00.000000000Z,,,FUTURE.CME.GC.GCM26,1,1,1,1,1,GCM26\n",
        )?;

        let index_path = write_historical_csv_index(&path)?;
        let payload: serde_json::Value = serde_json::from_str(&fs::read_to_string(index_path)?)?;

        assert_eq!(payload["granularity"], "day");
        assert_eq!(payload["row_count"], 2);
        assert_eq!(payload["buckets"][0]["date"], "2026-01-02");
        assert_eq!(payload["buckets"][1]["date"], "2026-01-03");
        Ok(())
    }
}
