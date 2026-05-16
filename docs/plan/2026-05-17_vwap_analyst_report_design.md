# VWAP Analyst Backtest Report Design

Date: 2026-05-17

## Goal

Provide a human-readable VWAP backtest report for analysts. The report should turn an existing completed backtest run directory into a static HTML document and a PDF export from the same rendered content.

The first implementation targets the VWAP pullback strategy smoke path, but the report boundary should stay generic enough for other single-strategy backtests that emit the same `summary.json`, `manifest.json`, and NDJSON artifacts.

## Domain Fact / Invariant

The visual report is a presentation of already-finalized backtest artifacts. It must not become a second source of truth for returns, fills, orders, dataset identity, execution assumptions, or report hashes.

Correct owner or abstraction boundary:

- Backtest execution and audit artifacts remain owned by `qts.backtest` and `qts.reporting.backtest`.
- The analyst report owns only loading, validating, deriving display metrics from finalized artifacts, rendering HTML, and exporting PDF.
- Report generation must read from a completed run directory and preserve links or references to the manifest and raw artifacts.

Forbidden shortcut:

- Do not recompute trades or equity from historical market data in the report layer.
- Do not silently fall back to synthetic metrics when an artifact is missing or invalid.
- Do not make a VWAP-only report model that cannot render a normal single-strategy backtest report.

Required gates / verification:

- Unit tests for report loading, metric derivation, and missing-artifact errors.
- Integration test that runs or consumes a VWAP smoke backtest and verifies HTML and PDF artifacts are generated.
- Manifest/report hash presence in the rendered report.
- A narrow Makefile target for local verification.

## User-Facing Output

The MVP report is an analyst summary, not an audit-only manifest dump.

Primary sections:

1. Executive summary: strategy, run status, symbol universe, date range, run id, report hash.
2. Key metrics: total return, max drawdown, final equity, processed bars, warmup/trading bars, trade count, fill count, win-rate if derivable from trade ledger.
3. Equity curve: static chart from `equity_curve.ndjson`, with drawdown context if available.
4. Trade summary: table and simple distribution from `orders.ndjson`, `fills.ndjson`, and `trade_ledger.ndjson`.
5. VWAP diagnostics: initial version reports strategy name, VWAP strategy parameters when available, and entry/exit counts. Deeper signal-level VWAP distance analysis is deferred unless raw events already expose enough data without rerunning strategy logic.
6. Backtest inputs: dataset, cost model, execution assumptions, risk hash, warmup/trading bars.
7. Appendix: manifest path, raw artifact paths, config hash, dataset hash, report hash.

## Architecture

Add a reporting boundary under the existing reporting/backtest area rather than inside the runner or strategy example.

Proposed ownership:

- `BacktestRunReportLoader`: validates a run directory and loads summary, manifest, and artifact streams.
- `BacktestReportDataset`: immutable in-memory report model derived from finalized artifacts.
- `AnalystBacktestReportRenderer`: renders static HTML from the report model.
- `BacktestPdfExporter`: exports PDF from the same HTML output.
- CLI/script entrypoint: generates HTML and optionally PDF for a completed run directory.

The loader should stream or bounded-read NDJSON where practical. The MVP can fully load small smoke artifacts, but the interface should not force all future full-run reports to hold every event in memory.

## Data Flow

1. User runs a backtest and produces a run directory.
2. User invokes report generation with the run directory or summary path.
3. Loader resolves:
   - `*.summary.json`
   - referenced manifest path
   - artifact paths from manifest
4. Loader validates required fields and artifact existence.
5. Report model derives display metrics from finalized artifacts.
6. Renderer writes `run_id.analyst_report.html`.
7. PDF exporter writes `run_id.analyst_report.pdf` from the same HTML.

The report generator should not trigger a backtest by default. Combining backtest + report can be added later as a convenience wrapper once the report boundary is stable.

## Error Handling

Fail closed for missing or inconsistent inputs:

- Missing summary, manifest, or required artifact: explicit error naming the missing file.
- Invalid JSON/NDJSON: explicit parse error with path and line number where possible.
- Manifest hash/report hash mismatch: explicit error; do not render a success report.
- Empty equity curve: render should fail unless the manifest explicitly represents a zero-bar run.
- PDF backend unavailable: HTML generation may still succeed, but the command must report that PDF export was not produced.

## PDF Export Decision

Use one HTML layout as the canonical visual report. PDF should be generated from that HTML rather than maintaining a separate PDF template.

Preferred implementation path:

- HTML/CSS template committed in source.
- Local chart rendering through a deterministic, offline dependency or inline SVG generated from report data.
- PDF export through an existing project-approved or already-available tool if present. If a new dependency is needed, justify it separately before adding it.

## Deferred Scope

These are intentionally out of MVP:

- Interactive filters and hosted dashboard.
- Multi-strategy attribution.
- Notebook-style analyst commentary editor.
- Re-running strategy logic to compute extra VWAP signal diagnostics.
- Broker/live report unification beyond preserving shared manifest concepts.

## Acceptance Criteria

The MVP is acceptable when:

- A completed VWAP smoke backtest can produce both HTML and PDF report files.
- The HTML report shows key run identity, performance metrics, equity chart, trade summary, input assumptions, and appendix links.
- The PDF visually matches the HTML content closely enough for review and sharing.
- Tests cover successful report generation and missing/invalid artifact failures.
- The command can be run locally without network access.
