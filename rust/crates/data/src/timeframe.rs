use chrono::Duration;
use thiserror::Error;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AlignmentMode {
    Clock,
    Session,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Timeframe {
    value: String,
    duration: Option<Duration>,
    alignment: AlignmentMode,
}

impl Timeframe {
    pub fn parse(value: &str) -> Result<Self, TimeframeError> {
        let normalized = value.trim().to_ascii_lowercase();
        let duration = match normalized.as_str() {
            "1m" => Some(Duration::minutes(1)),
            "2m" => Some(Duration::minutes(2)),
            "3m" => Some(Duration::minutes(3)),
            "5m" => Some(Duration::minutes(5)),
            "10m" => Some(Duration::minutes(10)),
            "15m" => Some(Duration::minutes(15)),
            "30m" => Some(Duration::minutes(30)),
            "1h" => Some(Duration::hours(1)),
            "4h" => Some(Duration::hours(4)),
            "1d" => {
                return Ok(Self {
                    value: normalized,
                    duration: None,
                    alignment: AlignmentMode::Session,
                })
            }
            _ => None,
        };
        match duration {
            Some(duration) => Ok(Self {
                value: normalized,
                duration: Some(duration),
                alignment: AlignmentMode::Clock,
            }),
            None => Err(TimeframeError::Unsupported(value.to_string())),
        }
    }

    pub fn value(&self) -> &str {
        &self.value
    }

    pub fn duration(&self) -> Option<Duration> {
        self.duration
    }

    pub fn alignment(&self) -> AlignmentMode {
        self.alignment
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum TimeframeError {
    #[error("unsupported timeframe: {0}")]
    Unsupported(String),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_all_supported_migration_timeframes() -> Result<(), Box<dyn std::error::Error>> {
        let clock_timeframes = [
            ("1m", Duration::minutes(1)),
            ("2m", Duration::minutes(2)),
            ("3m", Duration::minutes(3)),
            ("5m", Duration::minutes(5)),
            ("10m", Duration::minutes(10)),
            ("15m", Duration::minutes(15)),
            ("30m", Duration::minutes(30)),
            ("1h", Duration::hours(1)),
            ("4h", Duration::hours(4)),
        ];

        for (value, duration) in clock_timeframes {
            let timeframe = Timeframe::parse(value)?;
            assert_eq!(timeframe.value(), value);
            assert_eq!(timeframe.alignment(), AlignmentMode::Clock);
            assert_eq!(timeframe.duration(), Some(duration));
        }

        let daily = Timeframe::parse("1d")?;
        assert_eq!(daily.value(), "1d");
        assert_eq!(daily.alignment(), AlignmentMode::Session);
        assert_eq!(daily.duration(), None);
        Ok(())
    }

    #[test]
    fn rejects_unsupported_timeframes() {
        assert_eq!(
            Timeframe::parse("7m"),
            Err(TimeframeError::Unsupported("7m".to_string()))
        );
        assert_eq!(
            Timeframe::parse("1w"),
            Err(TimeframeError::Unsupported("1w".to_string()))
        );
    }
}
