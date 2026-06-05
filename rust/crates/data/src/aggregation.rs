use chrono::{DateTime, Duration, NaiveDateTime, NaiveTime, TimeZone, Utc};
use chrono_tz::Tz;
use qts_domain::{Bar, BarInput, InstrumentId, TimeInterval};
use rust_decimal::Decimal;
use thiserror::Error;

use crate::timeframe::{AlignmentMode, Timeframe};

#[derive(Clone, Debug)]
pub struct BarAggregator {
    target_timeframe: Timeframe,
    exchange_timezone: Tz,
    state: Option<AggregationState>,
}

impl BarAggregator {
    pub fn new(
        target_timeframe: Timeframe,
        exchange_timezone: Tz,
    ) -> Result<Self, AggregationError> {
        if target_timeframe.alignment() != AlignmentMode::Clock {
            return Err(AggregationError::SessionTimeframeUnsupported);
        }
        Ok(Self {
            target_timeframe,
            exchange_timezone,
            state: None,
        })
    }

    pub fn update(&mut self, bar: Bar) -> Result<Vec<Bar>, AggregationError> {
        let incoming_bucket = clock_bucket_for(
            bar.start_time,
            &self.target_timeframe,
            self.exchange_timezone,
        )?;
        let mut completed = Vec::new();
        if let Some(state) = &self.state {
            if !same_bucket(state, &bar, &incoming_bucket) {
                completed.push(aggregate_state(state)?);
                self.state = None;
            }
        }
        match &mut self.state {
            Some(state) => state.bars.push(bar),
            None => {
                self.state = Some(AggregationState {
                    bucket: incoming_bucket,
                    target_timeframe: self.target_timeframe.clone(),
                    instrument_id: bar.instrument_id.clone(),
                    session_id: bar.session_id.clone(),
                    bars: vec![bar],
                });
            }
        }
        if let Some(state) = &self.state {
            if let Some(last) = state.bars.last() {
                if last.end_time >= state.bucket.end() {
                    completed.push(aggregate_state(state)?);
                    self.state = None;
                }
            }
        }
        Ok(completed)
    }

    pub fn finish(&mut self) -> Result<Vec<Bar>, AggregationError> {
        match self.state.take() {
            Some(state) => Ok(vec![aggregate_state(&state)?]),
            None => Ok(Vec::new()),
        }
    }
}

#[derive(Clone, Debug)]
struct AggregationState {
    bucket: TimeInterval,
    target_timeframe: Timeframe,
    instrument_id: InstrumentId,
    session_id: Option<String>,
    bars: Vec<Bar>,
}

fn same_bucket(state: &AggregationState, bar: &Bar, incoming_bucket: &TimeInterval) -> bool {
    state.instrument_id == bar.instrument_id
        && state.session_id == bar.session_id
        && state.bucket == *incoming_bucket
}

pub fn clock_bucket_for(
    timestamp: DateTime<Utc>,
    timeframe: &Timeframe,
    exchange_timezone: Tz,
) -> Result<TimeInterval, AggregationError> {
    if timeframe.alignment() != AlignmentMode::Clock {
        return Err(AggregationError::SessionTimeframeUnsupported);
    }
    let duration = timeframe
        .duration()
        .ok_or(AggregationError::MissingDuration)?;
    let duration_seconds = duration.num_seconds();
    if duration_seconds <= 0 || 86_400 % duration_seconds != 0 {
        return Err(AggregationError::InvalidDuration);
    }
    let local = timestamp.with_timezone(&exchange_timezone);
    let midnight = resolve_local_datetime(
        exchange_timezone,
        NaiveDateTime::new(local.date_naive(), NaiveTime::MIN),
    )?;
    let elapsed_seconds = local
        .with_timezone(&Utc)
        .signed_duration_since(midnight)
        .num_seconds();
    let bucket_start_offset = elapsed_seconds.div_euclid(duration_seconds) * duration_seconds;
    let start = midnight + Duration::seconds(bucket_start_offset);
    TimeInterval::new(start, start + duration).map_err(|_| AggregationError::InvalidInterval)
}

fn aggregate_state(state: &AggregationState) -> Result<Bar, AggregationError> {
    let first = state.bars.first().ok_or(AggregationError::EmptyState)?;
    let last = state.bars.last().ok_or(AggregationError::EmptyState)?;
    let mut high = first.high;
    let mut low = first.low;
    let mut volume = Decimal::ZERO;
    let mut is_complete = true;
    let mut is_partial = false;
    let mut is_synthetic = true;
    for bar in &state.bars {
        high = high.max(bar.high);
        low = low.min(bar.low);
        volume += bar.volume;
        is_complete = is_complete && bar.is_complete;
        is_partial = is_partial || bar.is_partial;
        is_synthetic = is_synthetic && bar.is_synthetic;
    }
    Bar::new(BarInput {
        instrument_id: state.instrument_id.clone(),
        timeframe: state.target_timeframe.value().to_string(),
        start_time: state.bucket.start(),
        end_time: state.bucket.end(),
        open: first.open,
        high,
        low,
        close: last.close,
        volume,
        session_id: state.session_id.clone(),
        is_complete: is_complete && !is_partial,
        is_partial: is_partial || !is_complete,
        is_synthetic,
    })
    .map_err(|_| AggregationError::InvalidBar)
}

fn resolve_local_datetime(
    timezone: Tz,
    local: NaiveDateTime,
) -> Result<DateTime<Utc>, AggregationError> {
    match timezone.from_local_datetime(&local) {
        chrono::LocalResult::Single(value) => Ok(value.with_timezone(&Utc)),
        chrono::LocalResult::Ambiguous(first, _) => Ok(first.with_timezone(&Utc)),
        chrono::LocalResult::None => Err(AggregationError::NonexistentLocalTime),
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum AggregationError {
    #[error("session-aligned timeframe is not supported by clock aggregator")]
    SessionTimeframeUnsupported,
    #[error("clock timeframe is missing duration")]
    MissingDuration,
    #[error("clock timeframe duration must evenly divide one day")]
    InvalidDuration,
    #[error("local timestamp does not exist")]
    NonexistentLocalTime,
    #[error("aggregation state is empty")]
    EmptyState,
    #[error("aggregated bar is invalid")]
    InvalidBar,
    #[error("bucket interval is invalid")]
    InvalidInterval,
}

#[cfg(test)]
mod tests {
    use super::*;
    use qts_domain::InstrumentId;

    #[test]
    fn aggregates_one_minute_bars_to_five_minutes() -> Result<(), Box<dyn std::error::Error>> {
        let instrument = InstrumentId::new("FUTURE.CME.GC.GCM26")?;
        let timeframe = Timeframe::parse("5m")?;
        let mut aggregator = BarAggregator::new(timeframe, chrono_tz::US::Eastern)?;
        let mut completed = Vec::new();
        for index in 0..5 {
            let start =
                DateTime::parse_from_rfc3339(&format!("2026-01-06T14:{:02}:00Z", 30 + index))?
                    .with_timezone(&Utc);
            let end = start + Duration::minutes(1);
            completed.extend(aggregator.update(Bar::new(BarInput {
                instrument_id: instrument.clone(),
                timeframe: "1m".to_string(),
                start_time: start,
                end_time: end,
                open: Decimal::new(100 + index, 0),
                high: Decimal::new(105 + index, 0),
                low: Decimal::new(95 - index, 0),
                close: Decimal::new(101 + index, 0),
                volume: Decimal::new(10, 0),
                session_id: Some("2026-01-06".to_string()),
                is_complete: true,
                is_partial: false,
                is_synthetic: false,
            })?)?);
        }

        assert_eq!(completed.len(), 1);
        let bar = &completed[0];
        assert_eq!(bar.timeframe, "5m");
        assert_eq!(bar.open, Decimal::new(100, 0));
        assert_eq!(bar.high, Decimal::new(109, 0));
        assert_eq!(bar.low, Decimal::new(91, 0));
        assert_eq!(bar.close, Decimal::new(105, 0));
        assert_eq!(bar.volume, Decimal::new(50, 0));
        Ok(())
    }
}
