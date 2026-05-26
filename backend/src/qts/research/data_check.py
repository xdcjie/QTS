"""Research data input check artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ResearchDataIssue:
    """Owns one research data input issue."""

    code: str
    message: str
    path: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code is required")
        if not self.message.strip():
            raise ValueError("message is required")

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchDataIssue:
        """Rehydrate one issue."""

        raw_path = payload.get("path")
        return cls(
            code=_required_text(payload, "code"),
            message=_required_text(payload, "message"),
            path=None if raw_path is None else str(raw_path),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready issue payload."""

        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True, slots=True)
class ResearchDataCheck:
    """Owns promotion-grade checks for research data inputs."""

    schema_version: int
    dataset_id: str
    accepted: bool
    checked_paths: tuple[str, ...]
    issues: tuple[ResearchDataIssue, ...] = ()

    @classmethod
    def from_dataset_files(
        cls,
        *,
        dataset_id: str,
        dataset_files: Sequence[Mapping[str, Any]],
    ) -> ResearchDataCheck:
        """Build checks from dataset file metadata."""

        checked_paths: list[str] = []
        issues: list[ResearchDataIssue] = []
        for row in dataset_files:
            path = None if row.get("path") is None else str(row.get("path"))
            if path is not None:
                checked_paths.append(path)
            if row.get("exists") is not True:
                issues.append(
                    ResearchDataIssue(
                        code="missing_file",
                        message=str(row.get("reason", "file is missing")),
                        path=path,
                    )
                )
        return cls(
            schema_version=1,
            dataset_id=dataset_id,
            accepted=not issues,
            checked_paths=tuple(checked_paths),
            issues=tuple(issues),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchDataCheck:
        """Rehydrate a data check artifact."""

        if int(payload.get("schema_version", 0)) != 1:
            raise ValueError("schema_version must be 1")
        raw_issues = payload.get("issues", ())
        if not isinstance(raw_issues, Sequence) or isinstance(raw_issues, str):
            raise ValueError("issues must be a sequence")
        return cls(
            schema_version=1,
            dataset_id=_required_text(payload, "dataset_id"),
            accepted=bool(payload.get("accepted", False)),
            checked_paths=tuple(str(item) for item in payload.get("checked_paths", ())),
            issues=tuple(
                ResearchDataIssue.from_payload(item)
                for item in raw_issues
                if isinstance(item, Mapping)
            ),
        )

    def blockers(self) -> tuple[str, ...]:
        """Return blocking data check reasons."""

        if self.accepted:
            return ()
        return tuple(f"{issue.code}: {issue.message}" for issue in self.issues)

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready check payload."""

        return {
            "accepted": self.accepted,
            "blockers": list(self.blockers()),
            "checked_paths": list(self.checked_paths),
            "dataset_id": self.dataset_id,
            "issues": [issue.to_payload() for issue in self.issues],
            "schema_version": self.schema_version,
        }


class ResearchDataCheckWriter:
    """Writes research data check artifacts."""

    def write(self, path: Path, check: ResearchDataCheck) -> Path:
        """Write a JSON check artifact."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(check.to_payload(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return path


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


__all__ = ["ResearchDataCheck", "ResearchDataCheckWriter", "ResearchDataIssue"]
