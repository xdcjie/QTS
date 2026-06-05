use thiserror::Error;

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct InstrumentId(String);

impl InstrumentId {
    pub fn new(value: impl Into<String>) -> Result<Self, InstrumentIdError> {
        let value = value.into();
        let trimmed = value.trim();
        if trimmed.is_empty() {
            return Err(InstrumentIdError::Empty);
        }
        Ok(Self(trimmed.to_string()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum InstrumentIdError {
    #[error("instrument id must not be empty")]
    Empty,
}
