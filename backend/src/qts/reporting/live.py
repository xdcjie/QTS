"""Live reporting outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_default, stable_json_hash
from qts.runtime.sinks.live import LiveRuntimeEventSink

_SECRET_KEY_PARTS = ("password", "token", "credential")


@dataclass(frozen=True, slots=True)
class LiveReportManifest:
    """Live report manifest metadata."""

    manifest_path: Path
    payload: dict[str, Any]


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
        extra_artifacts: dict[str, Path] | None = None,
    ) -> LiveReportManifest:
        """Write a manifest naming event and evidence artifacts."""
        if not runtime_mode.strip():
            raise ValueError("runtime_mode must not be empty")
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
        payload = {
            "runtime_mode": runtime_mode,
            "account_id": account_id,
            "config_hash": stable_json_hash(config_payload),
            "connection_metadata": self._redacted_connection_metadata(connection_metadata),
            "artifacts": artifacts,
        }
        report_hash = stable_json_hash(payload)
        payload["report_hash"] = report_hash
        run_id = f"live-{report_hash.removeprefix('sha256:')[:12]}"
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
        return LiveReportManifest(manifest_path=manifest_path, payload=payload)

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


class LiveEventReporter:
    """Boundary for live event reporting integrations."""


__all__ = ["LiveEventReporter", "LiveReportManifest", "LiveReportWriter"]
