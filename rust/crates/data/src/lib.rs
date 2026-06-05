//! Historical market data ingestion and materialization.

pub mod aggregation;
pub mod csv_index;
pub mod materialize;
pub mod timeframe;

pub use aggregation::BarAggregator;
pub use materialize::{materialize_historical_csv, MaterializeConfig};
pub use timeframe::{AlignmentMode, Timeframe};
