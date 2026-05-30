"""Human-readable analyst reports for finalized backtest artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from html import escape
from pathlib import Path
from typing import Any, Literal


class BacktestReportError(ValueError):
    """Raised when finalized backtest artifacts cannot produce an analyst report."""


@dataclass(frozen=True, slots=True)
class ArtifactRows:
    """Loaded rows from the finalized backtest artifact set."""

    events: tuple[dict[str, Any], ...]
    orders: tuple[dict[str, Any], ...]
    fills: tuple[dict[str, Any], ...]
    trade_ledger: tuple[dict[str, Any], ...]
    equity_curve: tuple[dict[str, Any], ...]
    statistics: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class BacktestReportMetrics:
    """Human-facing display metrics derived from finalized artifacts."""

    total_return: str
    max_drawdown: str
    final_equity: str
    trade_count: int
    fill_count: int
    order_count: int
    processed_bars: int
    warmup_bars: int
    trading_bars: int
    sharpe_ratio: str = "n/a"
    sortino_ratio: str = "n/a"
    calmar_ratio: str = "n/a"
    win_rate: str = "n/a"
    profit_factor: str = "n/a"


@dataclass(frozen=True, slots=True)
class AnalystBacktestReportArtifacts:
    """Generated analyst report output paths."""

    html_path: Path
    pdf_path: Path
    dataset: BacktestReportDataset


@dataclass(frozen=True, slots=True)
class BacktestReportDataset:
    """Validated report input loaded from a completed backtest run."""

    summary_path: Path
    manifest_path: Path
    summary: dict[str, Any]
    manifest: dict[str, Any]
    artifacts: ArtifactRows

    @property
    def run_id(self) -> str:
        """Return the finalized backtest run id."""
        return str(self.manifest["run_id"])

    @property
    def metrics(self) -> BacktestReportMetrics:
        """Return display metrics derived from finalized artifacts."""
        manifest_metrics = self.manifest.get("statistics", self.manifest.get("metrics", {}))
        if not isinstance(manifest_metrics, dict):
            manifest_metrics = {}
        final_equity = self._final_equity()
        return BacktestReportMetrics(
            total_return=_format_percent(_decimal_value(manifest_metrics.get("total_return"))),
            max_drawdown=_format_percent(_decimal_value(manifest_metrics.get("max_drawdown"))),
            final_equity=_format_decimal(final_equity),
            trade_count=len(self.artifacts.trade_ledger),
            fill_count=len(self.artifacts.fills),
            order_count=len(self.artifacts.orders),
            processed_bars=int(self.manifest.get("processed_bars", 0)),
            warmup_bars=int(self.manifest.get("warmup_bars", 0)),
            trading_bars=int(self.manifest.get("trading_bars", 0)),
            sharpe_ratio=_format_decimal(_decimal_value(manifest_metrics.get("sharpe_ratio"))),
            sortino_ratio=_format_decimal(_decimal_value(manifest_metrics.get("sortino_ratio"))),
            calmar_ratio=_format_decimal(_decimal_value(manifest_metrics.get("calmar_ratio"))),
            win_rate=_format_percent(_decimal_value(manifest_metrics.get("win_rate"))),
            profit_factor=_format_decimal(_decimal_value(manifest_metrics.get("profit_factor"))),
        )

    def _final_equity(self) -> Decimal | None:
        if not self.artifacts.equity_curve:
            return None
        return _decimal_value(self.artifacts.equity_curve[-1].get("equity"))


class BacktestRunReportLoader:
    """Load finalized backtest artifacts for analyst report rendering."""

    _ARTIFACT_KINDS = ("events", "orders", "fills", "trade_ledger", "equity_curve")

    @classmethod
    def from_summary(cls, summary_path: Path) -> BacktestReportDataset:
        """Load a completed backtest report dataset from a summary artifact."""
        resolved_summary_path = Path(summary_path)
        summary = cls._read_json_object(resolved_summary_path, label="summary")
        manifest_path = cls._resolve_manifest_path(summary, base_dir=resolved_summary_path.parent)
        manifest = cls._read_json_object(manifest_path, label="manifest")
        cls._validate_identity(summary, manifest)
        artifacts = ArtifactRows(
            events=cls._read_artifact_rows(manifest, "events", base_dir=manifest_path.parent),
            orders=cls._read_artifact_rows(manifest, "orders", base_dir=manifest_path.parent),
            fills=cls._read_artifact_rows(manifest, "fills", base_dir=manifest_path.parent),
            trade_ledger=cls._read_artifact_rows(
                manifest,
                "trade_ledger",
                base_dir=manifest_path.parent,
            ),
            equity_curve=cls._read_artifact_rows(
                manifest,
                "equity_curve",
                base_dir=manifest_path.parent,
            ),
            statistics=cls._read_optional_artifact_rows(
                manifest,
                "statistics",
                base_dir=manifest_path.parent,
            ),
        )
        if not artifacts.equity_curve and int(manifest.get("processed_bars", 0)) > 0:
            raise BacktestReportError("equity_curve artifact must not be empty")
        return BacktestReportDataset(
            summary_path=resolved_summary_path,
            manifest_path=manifest_path,
            summary=summary,
            manifest=manifest,
            artifacts=artifacts,
        )

    @classmethod
    def from_run_directory(cls, run_directory: Path) -> BacktestReportDataset:
        """Load the only completed summary in a run directory."""
        summaries = sorted(Path(run_directory).glob("*.summary.json"))
        if not summaries:
            raise BacktestReportError(f"missing summary artifact in {run_directory}")
        if len(summaries) > 1:
            raise BacktestReportError(f"expected one summary artifact in {run_directory}")
        return cls.from_summary(summaries[0])

    @classmethod
    def _resolve_manifest_path(cls, summary: dict[str, Any], *, base_dir: Path) -> Path:
        manifest_value = summary.get("manifest_path")
        if not isinstance(manifest_value, str) or not manifest_value.strip():
            raise BacktestReportError("summary is missing manifest_path")
        manifest_path = Path(manifest_value)
        if not manifest_path.is_absolute() and not manifest_path.exists():
            manifest_path = base_dir / manifest_path
        if not manifest_path.exists():
            raise BacktestReportError(f"missing manifest artifact: {manifest_path}")
        return manifest_path

    @classmethod
    def _validate_identity(cls, summary: dict[str, Any], manifest: dict[str, Any]) -> None:
        summary_run_id = str(summary.get("run_id", ""))
        manifest_run_id = str(manifest.get("run_id", ""))
        if not summary_run_id or not manifest_run_id or summary_run_id != manifest_run_id:
            raise BacktestReportError("summary and manifest run_id values do not match")
        summary_report_hash = summary.get("report_hash")
        manifest_report_hash = manifest.get("report_hash")
        if summary_report_hash != manifest_report_hash:
            raise BacktestReportError("summary and manifest report_hash values do not match")

    @classmethod
    def _read_artifact_rows(
        cls,
        manifest: dict[str, Any],
        artifact_kind: str,
        *,
        base_dir: Path,
    ) -> tuple[dict[str, Any], ...]:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            raise BacktestReportError("manifest is missing artifacts")
        artifact = artifacts.get(artifact_kind)
        if not isinstance(artifact, dict):
            raise BacktestReportError(f"manifest is missing {artifact_kind} artifact")
        path_value = artifact.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            raise BacktestReportError(f"{artifact_kind} artifact is missing path")
        path = Path(path_value)
        if not path.is_absolute() and not path.exists():
            path = base_dir / path
        if not path.exists():
            raise BacktestReportError(f"missing {artifact_kind} artifact: {path}")
        return cls._read_ndjson(path)

    @classmethod
    def _read_optional_artifact_rows(
        cls,
        manifest: dict[str, Any],
        artifact_kind: str,
        *,
        base_dir: Path,
    ) -> tuple[dict[str, Any], ...]:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict) or artifact_kind not in artifacts:
            return ()
        return cls._read_artifact_rows(manifest, artifact_kind, base_dir=base_dir)

    @classmethod
    def _read_json_object(cls, path: Path, *, label: str) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise BacktestReportError(f"invalid {label} JSON at {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise BacktestReportError(f"{label} artifact must contain a JSON object: {path}")
        return payload

    @classmethod
    def _read_ndjson(cls, path: Path) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise BacktestReportError(f"invalid NDJSON at {path}:{line_number}: {exc}") from exc
            if not isinstance(payload, dict):
                raise BacktestReportError(
                    f"NDJSON row must contain an object at {path}:{line_number}"
                )
            rows.append(payload)
        return tuple(rows)


class AnalystBacktestReportRenderer:
    """Render a static analyst HTML report from finalized backtest artifacts."""

    def render(self, dataset: BacktestReportDataset) -> str:
        """Return a complete static HTML report document."""
        metrics = dataset.metrics
        strategy_name = self._strategy_name(dataset)
        artifact_links = self._artifact_links(dataset)
        return "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '<meta charset="utf-8">',
                '<meta name="viewport" content="width=device-width, initial-scale=1">',
                f"<title>VWAP Backtest Analyst Report - {escape(dataset.run_id)}</title>",
                "<style>",
                self._style(),
                "</style>",
                "</head>",
                "<body>",
                '<main class="report">',
                "<header>",
                "<p>Analyst Backtest Report</p>",
                "<h1>VWAP Backtest Analyst Report</h1>",
                f"<div>Run <strong>{escape(dataset.run_id)}</strong> · "
                f"Strategy <strong>{escape(strategy_name)}</strong></div>",
                "</header>",
                '<section class="summary-grid">',
                self._metric_card("Total Return", metrics.total_return),
                self._metric_card("Max Drawdown", metrics.max_drawdown),
                self._metric_card("Final Equity", metrics.final_equity),
                self._metric_card("Sharpe", metrics.sharpe_ratio),
                self._metric_card("Sortino", metrics.sortino_ratio),
                self._metric_card("Calmar", metrics.calmar_ratio),
                self._metric_card("Win Rate", metrics.win_rate),
                self._metric_card("Profit Factor", metrics.profit_factor),
                self._metric_card("Trade Count", str(metrics.trade_count)),
                self._metric_card("Fill Count", str(metrics.fill_count)),
                self._metric_card("Processed Bars", str(metrics.processed_bars)),
                "</section>",
                '<section class="panel">',
                "<h2>Equity Curve</h2>",
                self._equity_svg(dataset.artifacts.equity_curve),
                "</section>",
                '<section class="two-column">',
                '<div class="panel">',
                "<h2>Trade Summary</h2>",
                "<dl>",
                f"<dt>Orders</dt><dd>{metrics.order_count}</dd>",
                f"<dt>Fills</dt><dd>{metrics.fill_count}</dd>",
                f"<dt>Trades</dt><dd>{metrics.trade_count}</dd>",
                "</dl>",
                "</div>",
                '<div class="panel">',
                "<h2>Backtest Inputs</h2>",
                "<dl>",
                f"<dt>Report Hash</dt><dd>{escape(str(dataset.manifest.get('report_hash')))}</dd>",
                f"<dt>Config Hash</dt><dd>{escape(str(dataset.manifest.get('config_hash')))}</dd>",
                f"<dt>Warmup Bars</dt><dd>{metrics.warmup_bars}</dd>",
                f"<dt>Trading Bars</dt><dd>{metrics.trading_bars}</dd>",
                "</dl>",
                "</div>",
                "</section>",
                '<section class="panel">',
                "<h2>Appendix</h2>",
                f'<p><a href="{escape(dataset.manifest_path.name)}">'
                f"{escape(dataset.manifest_path.name)}</a></p>",
                "<ul>",
                *artifact_links,
                "</ul>",
                "</section>",
                "</main>",
                "</body>",
                "</html>",
            ]
        )

    @staticmethod
    def _style() -> str:
        return """
        :root { color-scheme: light; font-family: Arial, Helvetica, sans-serif; }
        body { margin: 0; background: #f4f6f8; color: #17202a; }
        .report { max-width: 1120px; margin: 0 auto; padding: 32px; }
        header { margin-bottom: 24px; }
        header p { margin: 0 0 8px; color: #5c6b73; text-transform: uppercase; font-size: 12px; }
        h1 { margin: 0 0 10px; font-size: 32px; }
        h2 { margin: 0 0 14px; font-size: 18px; }
        .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        .metric, .panel {
          background: #fff;
          border: 1px solid #d9e1e8;
          border-radius: 8px;
          padding: 16px;
        }
        .metric .label { color: #5c6b73; font-size: 12px; text-transform: uppercase; }
        .metric .value { margin-top: 8px; font-size: 24px; font-weight: 700; }
        .panel { margin-top: 16px; }
        .two-column { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        dl { display: grid; grid-template-columns: 130px 1fr; gap: 8px 12px; margin: 0; }
        dt { color: #5c6b73; }
        dd { margin: 0; overflow-wrap: anywhere; }
        a { color: #145ea8; }
        svg { width: 100%; height: auto; border: 1px solid #d9e1e8; border-radius: 6px; }
        @media print {
          body { background: #fff; }
          .report { padding: 18px; }
          .metric, .panel { break-inside: avoid; }
        }
        """

    @staticmethod
    def _metric_card(label: str, value: str) -> str:
        return (
            '<div class="metric">'
            f'<div class="label">{escape(label)}</div>'
            f'<div class="value">{escape(value)}</div>'
            "</div>"
        )

    @staticmethod
    def _strategy_name(dataset: BacktestReportDataset) -> str:
        topology = dataset.manifest.get("runtime_topology")
        if isinstance(topology, dict):
            strategies = topology.get("strategies")
            if isinstance(strategies, list) and strategies:
                first = strategies[0]
                if isinstance(first, dict) and first.get("strategy_class"):
                    return str(first["strategy_class"])
        return str(dataset.manifest.get("strategy_version", "unknown"))

    @classmethod
    def _artifact_links(cls, dataset: BacktestReportDataset) -> list[str]:
        artifacts = dataset.manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            return []
        links: list[str] = []
        for name in sorted(artifacts):
            artifact = artifacts[name]
            if not isinstance(artifact, dict):
                continue
            path = Path(str(artifact.get("path", "")))
            links.append(
                f'<li>{escape(name)}: <a href="{escape(path.name)}">{escape(path.name)}</a></li>'
            )
        return links

    @classmethod
    def _equity_svg(cls, rows: tuple[dict[str, Any], ...]) -> str:
        values = [_decimal_value(row.get("equity")) for row in rows]
        points = [value for value in values if value is not None]
        if not points:
            return '<p class="empty">No equity curve rows available.</p>'
        width = Decimal("760")
        height = Decimal("220")
        padding = Decimal("20")
        min_value = min(points)
        max_value = max(points)
        span = max_value - min_value
        if span == Decimal("0"):
            span = Decimal("1")
        x_span = max(len(points) - 1, 1)
        path_points = []
        for index, value in enumerate(points):
            x = padding + (Decimal(index) / Decimal(x_span)) * (width - padding * 2)
            y = height - padding - ((value - min_value) / span) * (height - padding * 2)
            path_points.append(f"{_svg_number(x)},{_svg_number(y)}")
        return (
            f'<svg viewBox="0 0 {_svg_number(width)} {_svg_number(height)}" '
            'role="img" aria-label="Equity curve">'
            f'<polyline fill="none" stroke="#145ea8" stroke-width="3" '
            f'points="{" ".join(path_points)}" />'
            f'<text x="20" y="18" font-size="12" fill="#5c6b73">'
            f"Min {escape(_format_decimal(min_value))} · Max {escape(_format_decimal(max_value))}"
            "</text>"
            "</svg>"
        )


def _decimal_value(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _format_percent(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return f"{(value * Decimal('100')).quantize(Decimal('0.01'))}%"


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    normalized = value.normalize()
    return format(normalized, "f")


def _svg_number(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


class BacktestPdfExporter:
    """Export analyst HTML reports to PDF through a local Chrome executable."""

    _CHROME_NAMES = ("google-chrome", "chromium", "chromium-browser")
    _MACOS_CHROME_PATH = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

    def __init__(
        self,
        *,
        chrome_path: Path | None | Literal["auto"] = "auto",
        run_command: RunCommand = subprocess.run,
    ) -> None:
        """Create a PDF exporter with optional Chrome path override."""
        resolved_chrome_path = self._detect_chrome() if chrome_path == "auto" else chrome_path
        self._chrome_path = Path(resolved_chrome_path) if resolved_chrome_path is not None else None
        self._run_command = run_command

    def export(self, html_path: Path, pdf_path: Path) -> Path:
        """Export a local HTML file to PDF and return the PDF path."""
        if self._chrome_path is None:
            raise BacktestReportError("Chrome executable is required for PDF export")
        resolved_html_path = Path(html_path).resolve()
        resolved_pdf_path = Path(pdf_path)
        resolved_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        command = self._command(resolved_html_path, resolved_pdf_path)
        result = self._run_command(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise BacktestReportError(
                f"Chrome PDF export failed with exit code {result.returncode}: {result.stderr}"
            )
        if not resolved_pdf_path.exists():
            raise BacktestReportError(f"Chrome PDF export did not create {resolved_pdf_path}")
        return resolved_pdf_path

    def _command(self, html_path: Path, pdf_path: Path) -> list[str]:
        assert self._chrome_path is not None
        return [
            str(self._chrome_path),
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ]

    @classmethod
    def _detect_chrome(cls) -> Path | None:
        for name in cls._CHROME_NAMES:
            found = shutil.which(name)
            if found is not None:
                return Path(found)
        if cls._MACOS_CHROME_PATH.exists():
            return cls._MACOS_CHROME_PATH
        return None


class AnalystBacktestReportGenerator:
    """Generate analyst HTML and PDF reports from completed backtest runs."""

    def __init__(
        self,
        *,
        renderer: AnalystBacktestReportRenderer | None = None,
        pdf_exporter: Any | None = None,
    ) -> None:
        """Create a report generator with injectable rendering boundaries."""
        self._renderer = renderer or AnalystBacktestReportRenderer()
        self._pdf_exporter = pdf_exporter or BacktestPdfExporter()

    def generate(
        self,
        source: Path,
        *,
        output_dir: Path | None = None,
        write_pdf: bool = True,
    ) -> AnalystBacktestReportArtifacts:
        """Generate an analyst report from a summary path or run directory."""
        dataset = self._load_dataset(source)
        report_dir = output_dir or dataset.summary_path.parent
        report_dir.mkdir(parents=True, exist_ok=True)
        html_path = report_dir / f"{dataset.run_id}.analyst_report.html"
        pdf_path = report_dir / f"{dataset.run_id}.analyst_report.pdf"
        html_path.write_text(self._renderer.render(dataset), encoding="utf-8")
        if write_pdf:
            self._pdf_exporter.export(html_path, pdf_path)
        return AnalystBacktestReportArtifacts(
            html_path=html_path,
            pdf_path=pdf_path,
            dataset=dataset,
        )

    @staticmethod
    def _load_dataset(source: Path) -> BacktestReportDataset:
        if Path(source).is_dir():
            return BacktestRunReportLoader.from_run_directory(source)
        return BacktestRunReportLoader.from_summary(source)


__all__ = [
    "AnalystBacktestReportArtifacts",
    "AnalystBacktestReportGenerator",
    "AnalystBacktestReportRenderer",
    "ArtifactRows",
    "BacktestPdfExporter",
    "BacktestReportDataset",
    "BacktestReportError",
    "BacktestReportMetrics",
    "BacktestRunReportLoader",
]
