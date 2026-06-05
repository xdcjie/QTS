use std::env;
use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::process::ExitCode;
use std::str::FromStr;

use chrono::{DateTime, NaiveDate, NaiveTime, Utc};
use chrono_tz::Tz;
use qts_data::{materialize_historical_csv, MaterializeConfig};
use qts_python::{
    first_notice_roll_selection_json, parity_backtest_json_from_historical_csv,
    replay_json_from_historical_csv,
};
use qts_replay::{
    FirstNoticeRollSchedule, HistoricalCsvReplayConfig, ReplayConfig, RollContractSpec,
};
use rust_decimal::Decimal;
use serde_json::{json, Value};

fn main() -> ExitCode {
    let mut args = env::args();
    let _program = args.next();
    match args.next().as_deref() {
        None | Some("--version") | Some("version") => {
            println!("qts-rs {}", env!("CARGO_PKG_VERSION"));
            ExitCode::SUCCESS
        }
        Some("materialize") => match materialize_command(args.collect()) {
            Ok(()) => ExitCode::SUCCESS,
            Err(error) => {
                eprintln!("{error}");
                ExitCode::from(1)
            }
        },
        Some("replay") => match replay_command(args.collect()) {
            Ok(()) => ExitCode::SUCCESS,
            Err(error) => {
                eprintln!("{error}");
                ExitCode::from(1)
            }
        },
        Some("backtest") => match backtest_command(args.collect()) {
            Ok(()) => ExitCode::SUCCESS,
            Err(error) => {
                eprintln!("{error}");
                ExitCode::from(1)
            }
        },
        Some("roll-select") => match roll_select_command(args.collect()) {
            Ok(()) => ExitCode::SUCCESS,
            Err(error) => {
                eprintln!("{error}");
                ExitCode::from(1)
            }
        },
        Some("verify-gates") => verify_gates_command(args.collect()),
        Some("--help") | Some("help") => {
            print_help();
            ExitCode::SUCCESS
        }
        Some(command) => {
            eprintln!("unsupported qts-rs command: {command}");
            print_help();
            ExitCode::from(2)
        }
    }
}

fn print_help() {
    println!("qts-rs {}", env!("CARGO_PKG_VERSION"));
    println!();
    println!("Commands:");
    println!("  materialize   Materialize historical CSV timeframes and sidecar indexes");
    println!("  replay        Build deterministic replay tape JSON from historical CSV");
    println!("  backtest      Run parity-mode backtest JSON output");
    println!("  roll-select   Resolve a continuous future roll selection");
    println!("  verify-gates  Show required Python/Rust parity gates");
    println!("  version       Print version");
}

fn print_roll_select_help() {
    println!("qts-rs roll-select");
    println!();
    println!("Required:");
    println!("  --root <root>");
    println!("  --exchange <exchange>");
    println!("  --session-date <YYYY-MM-DD>");
    println!("  --contract <symbol|instrument_id|first_notice_day|expiry>");
    println!();
    println!("Optional:");
    println!("  --roll-sessions-before-first-notice <n>  Default: 3");
    println!("  --offset <n>                              Default: 0");
    println!("  --output-json <path>");
}

fn materialize_command(args: Vec<String>) -> Result<(), String> {
    let options = MaterializeOptions::parse(args)?;
    let config = MaterializeConfig {
        root: options.root,
        source_csv: options.source_csv,
        output_dir: options.output_dir,
        timeframes: options.timeframes,
        exchange_timezone: options.exchange_timezone,
        session_open: options.session_open,
        session_close: options.session_close,
        overwrite: options.overwrite,
    };
    let outputs = materialize_historical_csv(&config).map_err(|error| error.to_string())?;
    for output in outputs {
        println!("{}", output.display());
    }
    Ok(())
}

fn replay_command(args: Vec<String>) -> Result<(), String> {
    let options = RustCoreRunOptions::parse(args, RustCoreCommand::Replay)?;
    let output = replay_json_from_historical_csv(&options.replay_csv_config()?)?;
    write_json_value(options.output_json.as_ref(), &output)
}

fn backtest_command(args: Vec<String>) -> Result<(), String> {
    let options = RustCoreRunOptions::parse(args, RustCoreCommand::Backtest)?;
    if !options.shadow {
        return Err("qts-rs backtest requires --shadow until parity gates are clean".to_string());
    }
    let output = parity_backtest_json_from_historical_csv(
        &options.replay_csv_config()?,
        options.initial_cash,
        options.quantity,
        options.output_dir.as_deref(),
    )?;
    write_json_value(options.output_json.as_ref(), &output)
}

fn roll_select_command(args: Vec<String>) -> Result<(), String> {
    let options = RollSelectOptions::parse(args)?;
    let schedule = FirstNoticeRollSchedule::new(
        options.root,
        options.exchange,
        options.contracts,
        options.roll_sessions_before_first_notice,
    )
    .map_err(|error| error.to_string())?;
    let output = first_notice_roll_selection_json(&schedule, options.session_date, options.offset)?;
    write_json_value(options.output_json.as_ref(), &output)
}

#[derive(Debug)]
struct MaterializeOptions {
    root: String,
    source_csv: PathBuf,
    output_dir: PathBuf,
    timeframes: Vec<String>,
    exchange_timezone: Tz,
    session_open: NaiveTime,
    session_close: NaiveTime,
    overwrite: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum RustCoreCommand {
    Replay,
    Backtest,
}

#[derive(Debug)]
struct RustCoreRunOptions {
    roots: Vec<String>,
    source_csv: PathBuf,
    timeframe: String,
    dataset_hash: String,
    roll_policy: String,
    symbols: Vec<String>,
    instrument_ids: Vec<String>,
    output_json: Option<PathBuf>,
    output_dir: Option<PathBuf>,
    exchange_timezone: Tz,
    session_open: NaiveTime,
    session_close: NaiveTime,
    start: Option<DateTime<Utc>>,
    end: Option<DateTime<Utc>>,
    initial_cash: Decimal,
    quantity: Decimal,
    shadow: bool,
}

#[derive(Debug)]
struct RollSelectOptions {
    root: String,
    exchange: String,
    contracts: Vec<RollContractSpec>,
    session_date: NaiveDate,
    roll_sessions_before_first_notice: u32,
    offset: usize,
    output_json: Option<PathBuf>,
}

impl RustCoreRunOptions {
    fn parse(args: Vec<String>, command: RustCoreCommand) -> Result<Self, String> {
        let mut roots: Vec<String> = Vec::new();
        let mut source_csv: Option<PathBuf> = None;
        let mut timeframe: Option<String> = None;
        let mut dataset_hash: Option<String> = None;
        let mut roll_policy: Option<String> = None;
        let mut symbols: Vec<String> = Vec::new();
        let mut instrument_ids: Vec<String> = Vec::new();
        let mut output_json: Option<PathBuf> = None;
        let mut output_dir: Option<PathBuf> = None;
        let mut exchange_timezone: Option<Tz> = None;
        let mut session_open: Option<NaiveTime> = None;
        let mut session_close: Option<NaiveTime> = None;
        let mut start: Option<DateTime<Utc>> = None;
        let mut end: Option<DateTime<Utc>> = None;
        let mut initial_cash = Decimal::new(100_000, 0);
        let mut quantity = Decimal::new(1, 0);
        let mut shadow = false;
        let mut index = 0;
        while index < args.len() {
            match args[index].as_str() {
                "--root" => roots.push(required_value(&args, &mut index, "--root")?),
                "--roots" => {
                    roots.extend(split_csv_values(&required_value(
                        &args, &mut index, "--roots",
                    )?));
                }
                "--source-csv" => {
                    source_csv = Some(PathBuf::from(required_value(
                        &args,
                        &mut index,
                        "--source-csv",
                    )?));
                }
                "--timeframe" => {
                    timeframe = Some(required_value(&args, &mut index, "--timeframe")?);
                }
                "--dataset-hash" => {
                    dataset_hash = Some(required_value(&args, &mut index, "--dataset-hash")?);
                }
                "--roll-policy" => {
                    roll_policy = Some(required_value(&args, &mut index, "--roll-policy")?);
                }
                "--symbol" => {
                    symbols.push(required_value(&args, &mut index, "--symbol")?);
                }
                "--symbols" => {
                    symbols.extend(split_csv_values(&required_value(
                        &args,
                        &mut index,
                        "--symbols",
                    )?));
                }
                "--instrument-id" => {
                    instrument_ids.push(required_value(&args, &mut index, "--instrument-id")?);
                }
                "--instrument-ids" => {
                    instrument_ids.extend(split_csv_values(&required_value(
                        &args,
                        &mut index,
                        "--instrument-ids",
                    )?));
                }
                "--output-json" => {
                    output_json = Some(PathBuf::from(required_value(
                        &args,
                        &mut index,
                        "--output-json",
                    )?));
                }
                "--output-dir" => {
                    output_dir = Some(PathBuf::from(required_value(
                        &args,
                        &mut index,
                        "--output-dir",
                    )?));
                }
                "--exchange-timezone" => {
                    let value = required_value(&args, &mut index, "--exchange-timezone")?;
                    exchange_timezone = Some(
                        value
                            .parse::<Tz>()
                            .map_err(|_| format!("invalid exchange timezone: {value}"))?,
                    );
                }
                "--session-open" => {
                    session_open = Some(parse_time(&required_value(
                        &args,
                        &mut index,
                        "--session-open",
                    )?)?);
                }
                "--session-close" => {
                    session_close = Some(parse_time(&required_value(
                        &args,
                        &mut index,
                        "--session-close",
                    )?)?);
                }
                "--start" => {
                    start = Some(parse_timestamp(&required_value(
                        &args, &mut index, "--start",
                    )?)?);
                }
                "--end" => {
                    end = Some(parse_timestamp(&required_value(
                        &args, &mut index, "--end",
                    )?)?);
                }
                "--initial-cash" => {
                    initial_cash =
                        parse_decimal(&required_value(&args, &mut index, "--initial-cash")?)?;
                }
                "--quantity" => {
                    quantity = parse_decimal(&required_value(&args, &mut index, "--quantity")?)?;
                }
                "--shadow" => shadow = true,
                "--help" | "help" => {
                    print_rust_core_help(command);
                    return Err("help requested".to_string());
                }
                value => return Err(format!("unsupported option: {value}")),
            }
            index += 1;
        }
        if roots.is_empty() {
            return Err("--root or --roots is required".to_string());
        }
        Ok(Self {
            roots,
            source_csv: required_option(source_csv, "--source-csv")?,
            timeframe: required_option(timeframe, "--timeframe")?,
            dataset_hash: required_option(dataset_hash, "--dataset-hash")?,
            roll_policy: roll_policy.unwrap_or_else(|| "unspecified".to_string()),
            symbols,
            instrument_ids,
            output_json,
            output_dir,
            exchange_timezone: exchange_timezone.unwrap_or(chrono_tz::US::Eastern),
            session_open: session_open.unwrap_or_else(default_session_open),
            session_close: session_close.unwrap_or_else(default_session_close),
            start,
            end,
            initial_cash,
            quantity,
            shadow,
        })
    }

    fn replay_csv_config(&self) -> Result<HistoricalCsvReplayConfig, String> {
        Ok(HistoricalCsvReplayConfig {
            source_csv: self.source_csv.clone(),
            replay_config: ReplayConfig {
                dataset_hash: self.dataset_hash.clone(),
                timeframe: self.timeframe.clone(),
                start: self.start,
                end: self.end,
                roots: self.roots.clone(),
                symbols: self.symbols.clone(),
                instrument_ids: self.instrument_ids.clone(),
                roll_policy: self.roll_policy.clone(),
                source_path: Some(self.source_csv.display().to_string()),
            },
            exchange_timezone: self.exchange_timezone,
            session_open: self.session_open,
            session_close: self.session_close,
        })
    }
}

impl RollSelectOptions {
    fn parse(args: Vec<String>) -> Result<Self, String> {
        let mut root: Option<String> = None;
        let mut exchange: Option<String> = None;
        let mut contracts: Vec<RollContractSpec> = Vec::new();
        let mut session_date: Option<NaiveDate> = None;
        let mut roll_sessions_before_first_notice: u32 = 3;
        let mut offset: usize = 0;
        let mut output_json: Option<PathBuf> = None;
        let mut index = 0;
        while index < args.len() {
            match args[index].as_str() {
                "--root" => root = Some(required_value(&args, &mut index, "--root")?),
                "--exchange" => {
                    exchange = Some(required_value(&args, &mut index, "--exchange")?);
                }
                "--contract" => {
                    contracts.push(parse_roll_contract(&required_value(
                        &args,
                        &mut index,
                        "--contract",
                    )?)?);
                }
                "--session-date" => {
                    session_date = Some(parse_date(&required_value(
                        &args,
                        &mut index,
                        "--session-date",
                    )?)?);
                }
                "--roll-sessions-before-first-notice" => {
                    let value =
                        required_value(&args, &mut index, "--roll-sessions-before-first-notice")?;
                    roll_sessions_before_first_notice = value.parse::<u32>().map_err(|_| {
                        format!("invalid --roll-sessions-before-first-notice: {value}")
                    })?;
                }
                "--offset" => {
                    let value = required_value(&args, &mut index, "--offset")?;
                    offset = value
                        .parse::<usize>()
                        .map_err(|_| format!("invalid --offset: {value}"))?;
                }
                "--output-json" => {
                    output_json = Some(PathBuf::from(required_value(
                        &args,
                        &mut index,
                        "--output-json",
                    )?));
                }
                "--help" | "help" => {
                    print_roll_select_help();
                    return Err("roll-select help requested".to_string());
                }
                value => {
                    return Err(format!("unsupported roll-select option: {value}"));
                }
            }
            index += 1;
        }
        Ok(Self {
            root: root.ok_or("missing --root")?,
            exchange: exchange.ok_or("missing --exchange")?,
            contracts,
            session_date: session_date.ok_or("missing --session-date")?,
            roll_sessions_before_first_notice,
            offset,
            output_json,
        })
    }
}

fn parse_roll_contract(value: &str) -> Result<RollContractSpec, String> {
    let parts = value.split('|').collect::<Vec<_>>();
    if parts.len() != 4 {
        return Err(
            "invalid --contract; expected symbol|instrument_id|first_notice_day|expiry".to_string(),
        );
    }
    Ok(RollContractSpec {
        symbol: parts[0].to_string(),
        instrument_id: parts[1].to_string(),
        first_notice_day: parse_date(parts[2])?,
        expiry: parse_timestamp(parts[3])?,
    })
}

fn parse_date(value: &str) -> Result<NaiveDate, String> {
    NaiveDate::parse_from_str(value, "%Y-%m-%d").map_err(|_| format!("invalid date: {value}"))
}

impl MaterializeOptions {
    fn parse(args: Vec<String>) -> Result<Self, String> {
        let mut root: Option<String> = None;
        let mut source_csv: Option<PathBuf> = None;
        let mut output_dir: Option<PathBuf> = None;
        let mut timeframes: Vec<String> = Vec::new();
        let mut exchange_timezone: Option<Tz> = None;
        let mut session_open: Option<NaiveTime> = None;
        let mut session_close: Option<NaiveTime> = None;
        let mut overwrite = false;
        let mut index = 0;
        while index < args.len() {
            match args[index].as_str() {
                "--root" => {
                    root = Some(required_value(&args, &mut index, "--root")?);
                }
                "--source-csv" => {
                    source_csv = Some(PathBuf::from(required_value(
                        &args,
                        &mut index,
                        "--source-csv",
                    )?));
                }
                "--output-dir" => {
                    output_dir = Some(PathBuf::from(required_value(
                        &args,
                        &mut index,
                        "--output-dir",
                    )?));
                }
                "--timeframe" => {
                    timeframes.push(required_value(&args, &mut index, "--timeframe")?);
                }
                "--timeframes" => {
                    for timeframe in required_value(&args, &mut index, "--timeframes")?.split(',') {
                        let value = timeframe.trim();
                        if !value.is_empty() {
                            timeframes.push(value.to_string());
                        }
                    }
                }
                "--exchange-timezone" => {
                    let value = required_value(&args, &mut index, "--exchange-timezone")?;
                    exchange_timezone = Some(
                        value
                            .parse::<Tz>()
                            .map_err(|_| format!("invalid exchange timezone: {value}"))?,
                    );
                }
                "--session-open" => {
                    session_open = Some(parse_time(&required_value(
                        &args,
                        &mut index,
                        "--session-open",
                    )?)?);
                }
                "--session-close" => {
                    session_close = Some(parse_time(&required_value(
                        &args,
                        &mut index,
                        "--session-close",
                    )?)?);
                }
                "--overwrite" => {
                    overwrite = true;
                }
                "--help" | "help" => {
                    print_materialize_help();
                    return Err("materialize help requested".to_string());
                }
                value => {
                    return Err(format!("unsupported materialize option: {value}"));
                }
            }
            index += 1;
        }

        if timeframes.is_empty() {
            return Err("at least one --timeframe or --timeframes value is required".to_string());
        }
        Ok(Self {
            root: required_option(root, "--root")?,
            source_csv: required_option(source_csv, "--source-csv")?,
            output_dir: required_option(output_dir, "--output-dir")?,
            timeframes,
            exchange_timezone: exchange_timezone.unwrap_or(chrono_tz::US::Eastern),
            session_open: session_open.unwrap_or_else(default_session_open),
            session_close: session_close.unwrap_or_else(default_session_close),
            overwrite,
        })
    }
}

fn required_value(args: &[String], index: &mut usize, option: &str) -> Result<String, String> {
    *index += 1;
    args.get(*index)
        .cloned()
        .ok_or_else(|| format!("missing value for {option}"))
}

fn required_option<T>(value: Option<T>, option: &str) -> Result<T, String> {
    value.ok_or_else(|| format!("{option} is required"))
}

fn parse_time(value: &str) -> Result<NaiveTime, String> {
    NaiveTime::parse_from_str(value, "%H:%M").map_err(|_| format!("invalid HH:MM time: {value}"))
}

fn parse_timestamp(value: &str) -> Result<DateTime<Utc>, String> {
    DateTime::parse_from_rfc3339(value)
        .map(|timestamp| timestamp.with_timezone(&Utc))
        .map_err(|_| format!("invalid RFC3339 timestamp: {value}"))
}

fn parse_decimal(value: &str) -> Result<Decimal, String> {
    Decimal::from_str(value).map_err(|_| format!("invalid decimal: {value}"))
}

fn split_csv_values(value: &str) -> Vec<String> {
    value
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .map(ToString::to_string)
        .collect()
}

fn write_json_value(output_path: Option<&PathBuf>, value: &Value) -> Result<(), String> {
    let payload = serde_json::to_string_pretty(value).map_err(|error| error.to_string())?;
    match output_path {
        Some(path) => {
            if let Some(parent) = path.parent() {
                if !parent.as_os_str().is_empty() {
                    fs::create_dir_all(parent).map_err(|error| error.to_string())?;
                }
            }
            let mut file = fs::File::create(path).map_err(|error| error.to_string())?;
            writeln!(file, "{payload}").map_err(|error| error.to_string())?;
        }
        None => {
            println!("{payload}");
        }
    }
    Ok(())
}

fn default_session_open() -> NaiveTime {
    NaiveTime::from_hms_opt(18, 0, 0).unwrap_or(NaiveTime::MIN)
}

fn default_session_close() -> NaiveTime {
    NaiveTime::from_hms_opt(17, 0, 0).unwrap_or(NaiveTime::MIN)
}

fn print_materialize_help() {
    println!("Usage:");
    println!(
        "  qts-rs materialize --root GC --source-csv <path> --output-dir <dir> --timeframe 5m"
    );
    println!();
    println!("Options:");
    println!("  --root <ROOT>");
    println!("  --source-csv <path>");
    println!("  --output-dir <dir>");
    println!("  --timeframe <tf>          Repeatable");
    println!("  --timeframes <tf,tf>");
    println!("  --exchange-timezone <tz>  Default: US/Eastern");
    println!("  --session-open <HH:MM>    Default: 18:00");
    println!("  --session-close <HH:MM>   Default: 17:00");
    println!("  --overwrite");
}

fn print_rust_core_help(command: RustCoreCommand) {
    match command {
        RustCoreCommand::Replay => {
            println!("Usage:");
            println!("  qts-rs replay --root GC --source-csv <path> --timeframe 5m --dataset-hash <hash>");
        }
        RustCoreCommand::Backtest => {
            println!("Usage:");
            println!("  qts-rs backtest --shadow --root GC --source-csv <path> --timeframe 5m --dataset-hash <hash>");
        }
    }
    println!();
    println!("Options:");
    println!("  --root <ROOT>");
    println!("  --source-csv <path>");
    println!("  --timeframe <tf>");
    println!("  --dataset-hash <hash>");
    println!("  --roll-policy <policy>");
    println!("  --symbol <symbol> / --symbols <a,b>");
    println!("  --instrument-id <id> / --instrument-ids <a,b>");
    println!("  --start <RFC3339>");
    println!("  --end <RFC3339>");
    println!("  --output-json <path>");
    println!("  --output-dir <dir>      Backtest artifact directory");
    println!("  --exchange-timezone <tz>  Default: US/Eastern");
    println!("  --session-open <HH:MM>    Default: 18:00");
    println!("  --session-close <HH:MM>   Default: 17:00");
    if command == RustCoreCommand::Backtest {
        println!("  --shadow                 Required");
        println!("  --initial-cash <decimal> Default: 100000");
        println!("  --quantity <decimal>     Default: 1");
    }
}

fn verify_gates_command(args: Vec<String>) -> ExitCode {
    if args.iter().any(|arg| arg == "--json") {
        let payload = json!({
            "required_gates": [
                "phase1: CSV/index golden diff",
                "phase2: replay sequence golden diff",
                "phase3: backtest orders/fills/equity/metrics golden diff",
                "phase4: workflow/campaign parity diff clean"
            ],
            "capabilities": qts_python::capabilities_json(),
            "candidate_replaces_reference": false,
        });
        match write_json_value(None, &payload) {
            Ok(()) => ExitCode::SUCCESS,
            Err(error) => {
                eprintln!("{error}");
                ExitCode::from(1)
            }
        }
    } else {
        print_verify_gates();
        ExitCode::SUCCESS
    }
}

fn print_verify_gates() {
    println!("required gates before Rust replaces Python:");
    println!("  phase1: CSV/index golden diff");
    println!("  phase2: replay sequence golden diff");
    println!("  phase3: backtest orders/fills/equity/metrics golden diff");
    println!("  phase4: workflow/campaign parity diff clean");
}
