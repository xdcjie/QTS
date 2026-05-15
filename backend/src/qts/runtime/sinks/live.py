"""Live runtime event sink."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_default, stable_json_hash
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext, RuntimeEventSink

_SECRET_KEY_PARTS = ("password", "secret", "token", "credential")


@dataclass(frozen=True, slots=True)
class WrittenRuntimeEvent:
    """Metadata returned after writing one event."""

    sequence: int
    event_hash: str


class LiveRuntimeEventSink(RuntimeEventSink):
    """Write append-only paper/live runtime events as deterministic NDJSON."""

    def __init__(
        self,
        output_dir: Path,
        *,
        filename: str = "events.ndjson",
        context: RuntimeEventContext | None = None,
    ) -> None:
        """Create a live event sink under an artifact directory."""
        if not filename.strip():
            raise ValueError("filename must not be empty")
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._output_dir / filename
        self._handle = self._path.open("w", encoding="utf-8")
        self._content_hasher = hashlib.sha256()
        self._rows = 0
        self._closed = False
        self._context = context

    @property
    def path(self) -> Path:
        """Return the event stream path."""
        return self._path

    @property
    def rows(self) -> int:
        """Return written row count."""
        return self._rows

    @property
    def content_hash(self) -> str:
        """Return the hash of rows written by this sink instance."""
        return f"sha256:{self._content_hasher.hexdigest()}"

    def write(self, event: RuntimeEvent) -> WrittenRuntimeEvent:
        """Append one normalized event row and return its hash metadata."""
        if self._closed:
            raise RuntimeError("event sink is closed")
        self._reject_secrets(event.payload)
        sequence = self._rows + 1
        event = self._context.apply(event, sequence_no=sequence) if self._context else event
        row = event.to_envelope(sequence_no=sequence)
        RuntimeEvent.require_canonical_envelope(row)
        event_hash = stable_json_hash(
            {
                key: value
                for key, value in row.items()
                if key not in {"event_id", "sequence_no", "ts_event", "ts_ingest"}
            }
        )
        row["event_hash"] = event_hash
        line = (
            json.dumps(
                row,
                default=stable_json_default,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
        self._handle.write(line)
        self._handle.flush()
        self._content_hasher.update(line.encode())
        self._rows = sequence
        return WrittenRuntimeEvent(sequence=sequence, event_hash=event_hash)

    def close(self) -> None:
        """Close the underlying event file."""
        if self._closed:
            return
        self._handle.close()
        self._closed = True

    def _reject_secrets(self, payload: Any) -> None:
        """Fail closed if event payload appears to contain secret material."""
        if isinstance(payload, dict):
            for key, value in payload.items():
                key_text = str(key).lower()
                if any(part in key_text for part in _SECRET_KEY_PARTS):
                    raise ValueError(f"runtime event payload contains secret-like key: {key}")
                self._reject_secrets(value)
            return
        if isinstance(payload, list | tuple):
            for item in payload:
                self._reject_secrets(item)


__all__ = ["LiveRuntimeEventSink", "WrittenRuntimeEvent"]
