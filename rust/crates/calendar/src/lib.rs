//! Market calendar and session semantics.

use chrono::{DateTime, Duration, NaiveDate, NaiveDateTime, NaiveTime, TimeZone, Utc};
use chrono_tz::Tz;
use qts_domain::TimeInterval;
use thiserror::Error;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RegularSessionWindow {
    timezone: Tz,
    open_time: NaiveTime,
    close_time: NaiveTime,
}

impl RegularSessionWindow {
    pub fn new(timezone: Tz, open_time: NaiveTime, close_time: NaiveTime) -> Self {
        Self {
            timezone,
            open_time,
            close_time,
        }
    }

    pub fn interval_for_session_id(&self, session_id: &str) -> Result<TimeInterval, SessionError> {
        let close_date = NaiveDate::parse_from_str(session_id, "%Y-%m-%d")
            .map_err(|_| SessionError::InvalidSessionId)?;
        let open_date = if self.open_time >= self.close_time {
            close_date
                .checked_sub_signed(Duration::days(1))
                .ok_or(SessionError::InvalidSessionId)?
        } else {
            close_date
        };
        let start =
            resolve_local_datetime(self.timezone, NaiveDateTime::new(open_date, self.open_time))?;
        let end = resolve_local_datetime(
            self.timezone,
            NaiveDateTime::new(close_date, self.close_time),
        )?;
        TimeInterval::new(start, end).map_err(|_| SessionError::InvalidInterval)
    }

    pub fn session_id_for(&self, timestamp: DateTime<Utc>) -> Option<String> {
        let local = timestamp.with_timezone(&self.timezone);
        let local_time = local.time();
        if self.open_time >= self.close_time {
            if local_time >= self.open_time {
                let close_date = local.date_naive().checked_add_signed(Duration::days(1))?;
                return Some(close_date.format("%Y-%m-%d").to_string());
            }
            if local_time < self.close_time {
                return Some(local.date_naive().format("%Y-%m-%d").to_string());
            }
            return None;
        }
        if local_time >= self.open_time && local_time < self.close_time {
            return Some(local.date_naive().format("%Y-%m-%d").to_string());
        }
        None
    }
}

fn resolve_local_datetime(
    timezone: Tz,
    local: NaiveDateTime,
) -> Result<DateTime<Utc>, SessionError> {
    match timezone.from_local_datetime(&local) {
        chrono::LocalResult::Single(value) => Ok(value.with_timezone(&Utc)),
        chrono::LocalResult::Ambiguous(first, _) => Ok(first.with_timezone(&Utc)),
        chrono::LocalResult::None => Err(SessionError::NonexistentLocalTime),
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum SessionError {
    #[error("session id must be YYYY-MM-DD")]
    InvalidSessionId,
    #[error("session interval is invalid")]
    InvalidInterval,
    #[error("local session timestamp does not exist")]
    NonexistentLocalTime,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn comex_regular_session_is_1380_minutes() -> Result<(), Box<dyn std::error::Error>> {
        let open = NaiveTime::from_hms_opt(18, 0, 0).ok_or("invalid open")?;
        let close = NaiveTime::from_hms_opt(17, 0, 0).ok_or("invalid close")?;
        let window = RegularSessionWindow::new(chrono_tz::US::Eastern, open, close);

        let interval = window.interval_for_session_id("2026-01-06")?;

        assert_eq!(
            interval
                .end()
                .signed_duration_since(interval.start())
                .num_minutes(),
            1_380
        );
        Ok(())
    }

    #[test]
    fn session_id_uses_exchange_local_close_date() -> Result<(), Box<dyn std::error::Error>> {
        let open = NaiveTime::from_hms_opt(18, 0, 0).ok_or("invalid open")?;
        let close = NaiveTime::from_hms_opt(17, 0, 0).ok_or("invalid close")?;
        let window = RegularSessionWindow::new(chrono_tz::US::Eastern, open, close);
        let timestamp = DateTime::parse_from_rfc3339("2026-01-05T23:30:00Z")?.with_timezone(&Utc);

        assert_eq!(
            window.session_id_for(timestamp).as_deref(),
            Some("2026-01-06")
        );
        Ok(())
    }
}
