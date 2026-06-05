//! Python integration boundary for the Rust QTS core.
//!
//! This crate intentionally exposes a narrow Rust-side bridge surface first.
//! PyO3 should only be added when a reviewed Python binding is actually needed.

use std::path::Path;

use chrono::NaiveDate;
use qts_backtest::{BacktestEngine, EngineBacktestConfig, FillTiming};
use qts_replay::{
    replay_tape_from_historical_csv, FirstNoticeRollSchedule, HistoricalCsvReplayConfig,
};
use rust_decimal::Decimal;
use serde_json::{json, Value};

/// Current crate version.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RustCoreCapabilities {
    pub materialize: bool,
    pub replay_tape: bool,
    pub parity_backtest: bool,
    pub release_parity_gate: bool,
    pub python_research_orchestration_is_source: bool,
}

pub fn capabilities() -> RustCoreCapabilities {
    RustCoreCapabilities {
        materialize: true,
        replay_tape: true,
        parity_backtest: true,
        release_parity_gate: true,
        python_research_orchestration_is_source: true,
    }
}

pub fn capabilities_json() -> Value {
    let value = capabilities();
    json!({
        "materialize": value.materialize,
        "replay_tape": value.replay_tape,
        "parity_backtest": value.parity_backtest,
        "release_parity_gate": value.release_parity_gate,
        "python_research_orchestration_is_source": value.python_research_orchestration_is_source,
    })
}

pub fn replay_json_from_historical_csv(
    config: &HistoricalCsvReplayConfig,
) -> Result<Value, String> {
    let tape = replay_tape_from_historical_csv(config).map_err(|error| error.to_string())?;
    Ok(tape.to_json_value())
}

pub fn parity_backtest_json_from_historical_csv(
    config: &HistoricalCsvReplayConfig,
    initial_cash: Decimal,
    quantity: Decimal,
    output_dir: Option<&Path>,
) -> Result<Value, String> {
    let tape = replay_tape_from_historical_csv(config).map_err(|error| error.to_string())?;
    let report = BacktestEngine::run(
        &tape,
        &EngineBacktestConfig {
            initial_cash,
            quantity,
            fill_timing: FillTiming::NextBarOpen,
        },
    )
    .map_err(|error| error.to_string())?;
    let mut output = report.to_json_value();
    if let Some(output_dir) = output_dir {
        let artifacts = report
            .write_artifacts(output_dir)
            .map_err(|error| error.to_string())?;
        output["artifacts"] = json!({
            "run_id": artifacts.run_id,
            "summary_path": artifacts.summary_path.display().to_string(),
            "manifest_path": artifacts.manifest_path.display().to_string(),
            "artifact_paths": artifacts.artifact_paths.iter().map(|(kind, path)| {
                (kind.clone(), path.display().to_string())
            }).collect::<std::collections::BTreeMap<_, _>>(),
        });
    }
    Ok(output)
}

pub fn first_notice_roll_selection_json(
    schedule: &FirstNoticeRollSchedule,
    session_date: NaiveDate,
    offset: usize,
) -> Result<Value, String> {
    let selection = schedule
        .select(session_date, offset)
        .map_err(|error| error.to_string())?;
    Ok(selection.to_json_value())
}
