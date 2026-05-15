"""Live reporting outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from qts.core.hashing import stable_json_default, stable_json_hash
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.reporting.base import RUNTIME_ARTIFACT_SCHEMA_VERSION, RuntimeManifest
from qts.runtime.config import BacktestCostModel
from qts.runtime.mode import RuntimeMode
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.sinks.live import LiveRuntimeEventSink

if TYPE_CHECKING:
    from qts.runtime.live import LiveStartupChecklist

_SECRET_KEY_PARTS = ("password", "token", "credential")


@dataclass(frozen=True, slots=True)
class LiveReportManifest:
    """Live report manifest metadata."""

    manifest_path: Path
    payload: dict[str, Any]
    runtime_manifest: RuntimeManifest


class LiveReportWriter:
    """Write auditable paper/live run manifests."""

    def __init__(self, output_dir: Path) -> None:
        """Create a writer for live report artifacts."""
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def write_manifest(
        self,
        *,
        config_payload: dict[str, Any],
        runtime_mode: str,
        account_id: str,
        connection_metadata: dict[str, Any],
        event_sink: LiveRuntimeEventSink,
        market_data_environment: str | None = None,
        execution_environment: str | None = None,
        account_environment: str | None = None,
        broker_account_kind: str | None = None,
        allow_live_orders: bool = False,
        operator_signoff_id: str | None = None,
        market_data_permission_state: str | None = None,
        startup_checklist: LiveStartupChecklist | None = None,
        extra_artifacts: dict[str, Path] | None = None,
        runtime_topology_payload: dict[str, Any] | None = None,
        execution_assumptions: dict[str, Any] | None = None,
    ) -> LiveReportManifest:
        """Write a manifest naming event and evidence artifacts."""
        finalized_at = datetime.now(UTC)
        runtime_mode_value = RuntimeMode.from_value(runtime_mode).value
        if not account_id.strip():
            raise ValueError("account_id must not be empty")
        artifacts = {
            "events": {
                "path": str(event_sink.path),
                "rows": event_sink.rows,
                "sha256": event_sink.content_hash,
            }
        }
        for name, path in (extra_artifacts or {}).items():
            artifacts[name] = self._artifact_payload(path)
        startup_checklist_payload: dict[str, Any] | None = None
        if startup_checklist is not None:
            startup_checklist_payload = startup_checklist.to_payload()
            startup_checklist_path = self._output_dir / "startup_checklist.json"
            startup_checklist_path.write_text(
                json.dumps(
                    startup_checklist_payload,
                    default=stable_json_default,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            artifacts["startup_checklist"] = self._artifact_payload(startup_checklist_path)
        payload = {
            "runtime_mode": runtime_mode_value,
            "account_id": account_id,
            "event_schema_version": RuntimeEvent.SCHEMA_VERSION,
            "artifact_schema_version": RUNTIME_ARTIFACT_SCHEMA_VERSION,
            "market_data_environment": self._non_empty_or_default(
                market_data_environment,
                default="unknown",
            ),
            "execution_environment": self._non_empty_or_default(
                execution_environment,
                default="unknown",
            ),
            "account_environment": self._non_empty_or_default(
                account_environment,
                default="unknown",
            ),
            "broker_account_kind": self._non_empty_or_default(
                broker_account_kind,
                default="unknown",
            ),
            "market_data_permission_state": self._non_empty_or_default(
                market_data_permission_state,
                default="unknown",
            ),
            "allow_live_orders": allow_live_orders,
            "operator_signoff_id": operator_signoff_id,
            "config_hash": stable_json_hash(config_payload),
            "topology_hash": (
                str(runtime_topology_payload["topology_hash"])
                if runtime_topology_payload is not None
                and runtime_topology_payload.get("topology_hash") is not None
                else None
            ),
            "created_at": finalized_at.isoformat(),
            "finalized_at": finalized_at.isoformat(),
            "connection_metadata": self._redacted_connection_metadata(connection_metadata),
            "artifacts": artifacts,
        }
        if execution_assumptions is not None:
            payload["execution_assumptions"] = dict(execution_assumptions)
        elif runtime_mode_value == RuntimeMode.PAPER_SIMULATED.value:
            payload["execution_assumptions"] = self._default_simulated_execution_assumptions()
        if runtime_topology_payload is not None:
            payload["runtime_topology"] = runtime_topology_payload
        if startup_checklist_payload is not None:
            payload["startup_checklist"] = startup_checklist_payload
        report_hash = stable_json_hash(payload)
        payload["report_hash"] = report_hash
        run_id = f"live-{report_hash.removeprefix('sha256:')[:12]}"
        payload["run_id"] = run_id
        runtime_manifest = RuntimeManifest.from_payload(payload)
        manifest_path = self._output_dir / f"{run_id}.manifest.json"
        manifest_path.write_text(
            json.dumps(
                payload,
                default=stable_json_default,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return LiveReportManifest(
            manifest_path=manifest_path,
            payload=payload,
            runtime_manifest=runtime_manifest,
        )

    def finalize(self) -> None:
        """Finalize live report writer resources."""
        return None

    @staticmethod
    def _artifact_payload(path: Path) -> dict[str, Any]:
        content = ""
        rows = 0
        if path.exists() and path.is_file():
            content = path.read_text(encoding="utf-8")
            rows = len(content.splitlines())
        return {
            "path": str(path),
            "rows": rows,
            "sha256": stable_json_hash(content),
        }

    @staticmethod
    def _default_simulated_execution_assumptions() -> dict[str, object]:
        return SimulatedExecutionAdapter(BacktestCostModel()).execution_assumptions_payload()

    @staticmethod
    def _redacted_connection_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        redacted: dict[str, Any] = {}
        for key, value in metadata.items():
            key_text = key.lower()
            if key_text == "secret_ref":
                redacted[key] = "<configured>" if str(value).strip() else "<missing>"
            elif any(part in key_text for part in _SECRET_KEY_PARTS):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = value
        return redacted

    @staticmethod
    def _non_empty_or_default(value: str | None, *, default: str) -> str:
        """Return a stripped value or a manifest-safe fallback."""
        if value is None:
            return default
        normalized = value.strip()
        return normalized or default


class LiveEventReporter:
    """Boundary for live event reporting integrations."""


__all__ = ["LiveEventReporter", "LiveReportManifest", "LiveReportWriter"]
