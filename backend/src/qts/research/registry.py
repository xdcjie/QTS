"""Research-system JSONL run registry."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ResearchRunRecord:
    """One research-system registry row."""

    run_id: str
    manifest_hash: str
    artifact_dir: Path
    status: str
    promotion_status: str
    recorded_at: datetime

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchRunRecord:
        """Rehydrate one registry row."""

        return cls(
            run_id=_required_text(payload, "run_id"),
            manifest_hash=_required_text(payload, "manifest_hash"),
            artifact_dir=Path(_required_text(payload, "artifact_dir")),
            status=_required_text(payload, "status"),
            promotion_status=_required_text(payload, "promotion_status"),
            recorded_at=_datetime(payload, "recorded_at"),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready registry record."""

        return {
            "artifact_dir": str(self.artifact_dir),
            "manifest_hash": self.manifest_hash,
            "promotion_status": self.promotion_status,
            "recorded_at": self.recorded_at.isoformat(),
            "run_id": self.run_id,
            "status": self.status,
        }


class ResearchRunRegistry:
    """Owns appending and reading the research-system run index."""

    def __init__(self, index_path: Path = Path("artifacts/research/index.jsonl")) -> None:
        self.index_path = index_path

    def append(self, record: ResearchRunRecord) -> None:
        """Append one run record to the JSONL registry."""

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_payload(), sort_keys=True) + "\n")

    def list(self) -> tuple[ResearchRunRecord, ...]:
        """Read all registry rows in file order."""

        if not self.index_path.exists():
            return ()
        records: list[ResearchRunRecord] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(ResearchRunRecord.from_payload(json.loads(line)))
        return tuple(records)

    @classmethod
    def from_root(cls, root: Path) -> ResearchRunRegistry:
        """Return the registry under an artifact root."""

        return cls(root / "index.jsonl")


def latest_record(records: tuple[ResearchRunRecord, ...]) -> ResearchRunRecord:
    """Return the newest registry row by recorded timestamp."""

    if not records:
        raise ValueError("research registry is empty")
    return sorted(records, key=lambda record: record.recorded_at, reverse=True)[0]


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _datetime(payload: Mapping[str, Any], field_name: str) -> datetime:
    parsed = datetime.fromisoformat(_required_text(payload, field_name))
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return parsed


def new_record(
    *,
    run_id: str,
    manifest_hash: str,
    artifact_dir: Path,
    status: str,
    promotion_status: str,
) -> ResearchRunRecord:
    """Create a record using the current UTC timestamp."""

    return ResearchRunRecord(
        run_id=run_id,
        manifest_hash=manifest_hash,
        artifact_dir=artifact_dir,
        status=status,
        promotion_status=promotion_status,
        recorded_at=datetime.now(UTC),
    )


__all__ = ["ResearchRunRecord", "ResearchRunRegistry", "latest_record", "new_record"]
