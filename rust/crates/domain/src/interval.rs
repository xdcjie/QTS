use chrono::{DateTime, Utc};
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TimeInterval {
    start: DateTime<Utc>,
    end: DateTime<Utc>,
}

impl TimeInterval {
    pub fn new(start: DateTime<Utc>, end: DateTime<Utc>) -> Result<Self, TimeIntervalError> {
        if start >= end {
            return Err(TimeIntervalError::NonPositive);
        }
        Ok(Self { start, end })
    }

    pub fn start(&self) -> DateTime<Utc> {
        self.start
    }

    pub fn end(&self) -> DateTime<Utc> {
        self.end
    }

    pub fn contains(&self, value: DateTime<Utc>) -> bool {
        self.start <= value && value < self.end
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum TimeIntervalError {
    #[error("time interval must have start before end")]
    NonPositive,
}

#[cfg(test)]
mod tests {
    use chrono::{Duration, TimeZone, Utc};

    use super::*;

    #[test]
    fn contains_uses_half_open_interval_membership() -> Result<(), Box<dyn std::error::Error>> {
        let start = Utc
            .with_ymd_and_hms(2026, 1, 6, 14, 30, 0)
            .single()
            .ok_or("start")?;
        let end = start + Duration::minutes(5);
        let interval = TimeInterval::new(start, end)?;

        assert!(interval.contains(start));
        assert!(interval.contains(start + Duration::minutes(4)));
        assert!(!interval.contains(end));
        assert!(!interval.contains(start - Duration::nanoseconds(1)));
        Ok(())
    }

    #[test]
    fn rejects_non_positive_intervals() -> Result<(), Box<dyn std::error::Error>> {
        let start = Utc
            .with_ymd_and_hms(2026, 1, 6, 14, 30, 0)
            .single()
            .ok_or("start")?;

        assert_eq!(TimeInterval::new(start, start), Err(TimeIntervalError::NonPositive));
        assert_eq!(
            TimeInterval::new(start, start - Duration::nanoseconds(1)),
            Err(TimeIntervalError::NonPositive)
        );
        Ok(())
    }
}
