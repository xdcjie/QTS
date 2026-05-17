# VWAP Analyst Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local HTML/PDF analyst report generator for completed backtest artifact directories.

**Architecture:** Add a reporting boundary that reads finalized `summary.json`, `manifest.json`, and NDJSON artifacts, derives display metrics, renders a static HTML report, and exports PDF with a local Chrome print backend. The report layer must not rerun strategies or recompute audit truth from market data.

**Tech Stack:** Python standard library, existing `qts.reporting` package, existing `scripts/` CLI style, pytest, local Chrome headless PDF export.

---

## File Structure

- Create `backend/src/qts/reporting/backtest_analyst.py`: loader, report model, HTML renderer, Chrome PDF exporter, and report generator facade.
- Modify `backend/src/qts/reporting/__init__.py`: export report generator types.
- Create `scripts/generate_backtest_report.py`: CLI for completed run directories or summary paths.
- Modify `Makefile`: add a narrow `backtest-vwap-report-smoke` target after the code exists.
- Create `tests/unit/reporting/test_backtest_analyst_report.py`: TDD tests for loader, renderer, and errors.
- Create `tests/integration/test_backtest_analyst_report_generation.py`: end-to-end report generation from a synthetic completed backtest run.

## Domain Gate

Domain fact: finalized backtest artifacts are the source of truth for report content.

Correct abstraction boundary: `qts.reporting.backtest_analyst` owns presentation loading and rendering only; `qts.backtest` and `qts.reporting.backtest` continue to own execution and manifest artifact production.

Forbidden shortcut: the report generator must not read historical market data, rerun the strategy, or invent fallback metrics when required artifacts are missing.

Verification: unit tests for artifact validation and metric derivation, integration test for HTML/PDF generation, `make guardrails`, and targeted pytest runs.

## Tasks

### Task 1: Loader Red Test

**Files:**
- Create: `tests/unit/reporting/test_backtest_analyst_report.py`

- [x] **Step 1: Write failing tests**

Add tests that construct a minimal finalized run directory and assert `BacktestRunReportLoader.from_summary(...)` loads summary, manifest, and artifact rows. Also add a missing artifact test.

- [x] **Step 2: Verify red**

Run:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/reporting/test_backtest_analyst_report.py -q
```

Expected: import failure for `qts.reporting.backtest_analyst`.

### Task 2: Loader Green

**Files:**
- Create: `backend/src/qts/reporting/backtest_analyst.py`

- [x] **Step 1: Implement loader and data model**

Add `BacktestRunReportLoader`, `BacktestReportDataset`, `BacktestReportError`, and `ArtifactRows`.

- [x] **Step 2: Verify green**

Run:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/reporting/test_backtest_analyst_report.py -q
```

Expected: loader tests pass.

### Task 3: Metrics And HTML Red

**Files:**
- Modify: `tests/unit/reporting/test_backtest_analyst_report.py`

- [x] **Step 1: Add failing metric and HTML tests**

Assert derived metrics include trade count, fill count, final equity, total return, max drawdown, and that rendered HTML contains run id, report hash, metric labels, chart SVG, and raw artifact links.

- [x] **Step 2: Verify red**

Run:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/reporting/test_backtest_analyst_report.py -q
```

Expected: failures for missing renderer/metrics behavior.

### Task 4: Metrics And HTML Green

**Files:**
- Modify: `backend/src/qts/reporting/backtest_analyst.py`
- Modify: `backend/src/qts/reporting/__init__.py`

- [x] **Step 1: Implement metrics and HTML renderer**

Add `BacktestReportMetrics`, `AnalystBacktestReportRenderer`, and deterministic inline SVG chart generation from equity curve rows.

- [x] **Step 2: Verify green**

Run:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/reporting/test_backtest_analyst_report.py -q
```

Expected: all unit report tests pass.

### Task 5: PDF Export Red

**Files:**
- Modify: `tests/unit/reporting/test_backtest_analyst_report.py`

- [x] **Step 1: Add PDF exporter tests**

Test that `BacktestPdfExporter` invokes a configured Chrome executable with `--headless`, `--disable-gpu`, and `--print-to-pdf=...`, and raises `BacktestReportError` when Chrome is unavailable.

- [x] **Step 2: Verify red**

Run:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/reporting/test_backtest_analyst_report.py -q
```

Expected: failures for missing PDF exporter behavior.

### Task 6: PDF Export Green

**Files:**
- Modify: `backend/src/qts/reporting/backtest_analyst.py`

- [x] **Step 1: Implement Chrome PDF exporter**

Use `subprocess.run` with a configurable Chrome path. Auto-detect common Chrome/Chromium paths.

- [x] **Step 2: Verify green**

Run:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/reporting/test_backtest_analyst_report.py -q
```

Expected: all unit report tests pass.

### Task 7: CLI And Integration

**Files:**
- Create: `scripts/generate_backtest_report.py`
- Create: `tests/integration/test_backtest_analyst_report_generation.py`

- [x] **Step 1: Add failing CLI/integration test**

Create a completed backtest run with `BacktestEngine`, generate HTML and PDF through `AnalystBacktestReportGenerator`, and assert output files exist and contain expected identity fields.

- [x] **Step 2: Implement CLI and generator facade**

Add `AnalystBacktestReportGenerator.generate(...)` and `scripts/generate_backtest_report.py`.

- [x] **Step 3: Verify integration**

Run:

```bash
PYTHONPATH=backend/src:. uv run pytest tests/integration/test_backtest_analyst_report_generation.py -q
```

Expected: integration test passes.

### Task 8: Makefile And Final Checks

**Files:**
- Modify: `Makefile`
- Inspect changed Python files for private helpers.

- [x] **Step 1: Add Makefile target**

Add `backtest-vwap-report-smoke` that runs the existing VWAP smoke backtest path and then generates HTML/PDF from its summary.

- [x] **Step 2: Run required checks**

Run:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/reporting/test_backtest_analyst_report.py -q
PYTHONPATH=backend/src:. uv run pytest tests/integration/test_backtest_analyst_report_generation.py -q
rg -n "^def _|^class _" backend/src/qts/reporting/backtest_analyst.py scripts/generate_backtest_report.py
make guardrails
```

Expected: targeted tests and guardrails pass; private helpers have justified class ownership or module-level pure rendering status.
