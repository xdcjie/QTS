use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use thiserror::Error;

use crate::{InstrumentId, TimeInterval};

#[derive(Clone, Debug, PartialEq)]
pub struct Bar {
    pub instrument_id: InstrumentId,
    pub timeframe: String,
    pub start_time: DateTime<Utc>,
    pub end_time: DateTime<Utc>,
    pub open: Decimal,
    pub high: Decimal,
    pub low: Decimal,
    pub close: Decimal,
    pub volume: Decimal,
    pub session_id: Option<String>,
    pub is_complete: bool,
    pub is_partial: bool,
    pub is_synthetic: bool,
}

impl Bar {
    pub fn new(input: BarInput) -> Result<Self, BarError> {
        if input.timeframe.trim().is_empty() {
            return Err(BarError::EmptyTimeframe);
        }
        TimeInterval::new(input.start_time, input.end_time)
            .map_err(|_| BarError::InvalidInterval)?;
        if input.high < input.low {
            return Err(BarError::InvalidOhlc);
        }
        if input.open > input.high || input.open < input.low {
            return Err(BarError::InvalidOhlc);
        }
        if input.close > input.high || input.close < input.low {
            return Err(BarError::InvalidOhlc);
        }
        Ok(Self {
            instrument_id: input.instrument_id,
            timeframe: input.timeframe,
            start_time: input.start_time,
            end_time: input.end_time,
            open: input.open,
            high: input.high,
            low: input.low,
            close: input.close,
            volume: input.volume,
            session_id: input.session_id,
            is_complete: input.is_complete,
            is_partial: input.is_partial,
            is_synthetic: input.is_synthetic,
        })
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct BarInput {
    pub instrument_id: InstrumentId,
    pub timeframe: String,
    pub start_time: DateTime<Utc>,
    pub end_time: DateTime<Utc>,
    pub open: Decimal,
    pub high: Decimal,
    pub low: Decimal,
    pub close: Decimal,
    pub volume: Decimal,
    pub session_id: Option<String>,
    pub is_complete: bool,
    pub is_partial: bool,
    pub is_synthetic: bool,
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum BarError {
    #[error("bar timeframe must not be empty")]
    EmptyTimeframe,
    #[error("bar interval must have start before end")]
    InvalidInterval,
    #[error("bar OHLC values are inconsistent")]
    InvalidOhlc,
}
