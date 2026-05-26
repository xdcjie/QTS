"""Structured research data-quality artifacts.

The artifact records caller-supplied quality results and checked file paths. It
does not parse source data or own calendar/session semantics.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class DataQualityIssue:
    """One data-quality issue recorded for promotion review."""

    code: str
    message: str
    blocker: bool = True

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("issue code is required")
        if not self.message.strip():
            raise ValueError("issue message is required")

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready issue payload."""

        return {
            "blocker": self.blocker,
            "code": self.code,
            "message": self.message,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> DataQualityIssue:
        """Restore an issue from a JSON payload."""

        return cls(
            code=_required_text(payload, "code"),
            message=_required_text(payload, "message"),
            blocker=_bool_field(payload, "blocker", default=True),
        )


@dataclass(frozen=True, slots=True)
class DataQualityArtifact:
    """Promotion-grade structured data-quality evidence."""

    dataset_id: str
    accepted: bool
    checked_paths: tuple[str, ...]
    issues: tuple[DataQualityIssue, ...] = ()
    duplicate_timestamps: int = 0
    missing_bars: int = 0
    session_alignment: bool = True
    stale_prices: int = 0
    halted_sessions: int = 0
    label_visibility: bool = True
    schema_version: int = field(default=2, init=False)

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id is required")
        if any(not path.strip() for path in self.checked_paths):
            raise ValueError("checked_paths must contain non-empty strings")
        for field_name in (
            "duplicate_timestamps",
            "missing_bars",
            "stale_prices",
            "halted_sessions",
        ):
            if int(getattr(self, field_name)) < 0:
                raise ValueError(f"{field_name} must be non-negative")

    @classmethod
    def from_dataset_snapshot(cls, snapshot: Mapping[str, Any]) -> DataQualityArtifact:
        """Build a data-quality artifact from a dataset snapshot mapping."""

        dataset_id = _required_text(snapshot, "dataset_id")
        checked_paths = _checked_paths(snapshot)
        duplicate_timestamps = _non_negative_int(snapshot.get("duplicate_timestamps", 0))
        missing_bars = _non_negative_int(snapshot.get("missing_bars", 0))
        session_alignment = _bool_field(snapshot, "session_alignment", default=True)
        stale_prices = _non_negative_int(snapshot.get("stale_prices", 0))
        halted_sessions = _non_negative_int(snapshot.get("halted_sessions", 0))
        label_visibility = _bool_field(snapshot, "label_visibility", default=True)
        issues = list(_issues(snapshot.get("issues", ())))

        for checked_path in checked_paths:
            if not Path(checked_path).exists():
                issues.append(
                    DataQualityIssue(
                        code="missing_checked_path",
                        message=f"checked path does not exist: {checked_path}",
                    )
                )
        artifact = cls(
            dataset_id=dataset_id,
            accepted=True,
            checked_paths=checked_paths,
            issues=tuple(issues),
            duplicate_timestamps=duplicate_timestamps,
            missing_bars=missing_bars,
            session_alignment=session_alignment,
            stale_prices=stale_prices,
            halted_sessions=halted_sessions,
            label_visibility=label_visibility,
        )
        return cls(
            dataset_id=artifact.dataset_id,
            accepted=not artifact.blockers(),
            checked_paths=artifact.checked_paths,
            issues=artifact.issues,
            duplicate_timestamps=artifact.duplicate_timestamps,
            missing_bars=artifact.missing_bars,
            session_alignment=artifact.session_alignment,
            stale_prices=artifact.stale_prices,
            halted_sessions=artifact.halted_sessions,
            label_visibility=artifact.label_visibility,
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> DataQualityArtifact:
        """Restore a data-quality artifact from a JSON-safe payload."""

        schema_version = payload.get("schema_version")
        if schema_version != 2:
            raise ValueError(f"unsupported data quality schema_version: {schema_version}")
        checked_paths = payload.get("checked_paths")
        issues = payload.get("issues", ())
        if not isinstance(checked_paths, list):
            raise ValueError("checked_paths must be a list")
        if not isinstance(issues, list):
            raise ValueError("issues must be a list")
        artifact = cls(
            dataset_id=_required_text(payload, "dataset_id"),
            accepted=_bool_field(payload, "accepted"),
            checked_paths=tuple(str(path) for path in checked_paths),
            issues=tuple(DataQualityIssue.from_payload(issue) for issue in issues),
            duplicate_timestamps=_non_negative_int(payload.get("duplicate_timestamps", 0)),
            missing_bars=_non_negative_int(payload.get("missing_bars", 0)),
            session_alignment=_bool_field(payload, "session_alignment", default=True),
            stale_prices=_non_negative_int(payload.get("stale_prices", 0)),
            halted_sessions=_non_negative_int(payload.get("halted_sessions", 0)),
            label_visibility=_bool_field(payload, "label_visibility", default=True),
        )
        return cls(
            dataset_id=artifact.dataset_id,
            accepted=artifact.accepted and not artifact.blockers(),
            checked_paths=artifact.checked_paths,
            issues=artifact.issues,
            duplicate_timestamps=artifact.duplicate_timestamps,
            missing_bars=artifact.missing_bars,
            session_alignment=artifact.session_alignment,
            stale_prices=artifact.stale_prices,
            halted_sessions=artifact.halted_sessions,
            label_visibility=artifact.label_visibility,
        )

    def blockers(self) -> tuple[dict[str, str], ...]:
        """Return blocker issue codes/messages for promotion gating."""

        blockers: list[dict[str, str]] = []
        seen_codes: set[str] = set()
        for issue in self.issues:
            if issue.blocker:
                blockers.append({"code": issue.code, "message": issue.message})
                seen_codes.add(issue.code)
        for issue in self._critical_flag_issues():
            if issue.code not in seen_codes:
                blockers.append({"code": issue.code, "message": issue.message})
        return tuple(blockers)

    def to_payload(
        self,
        *,
        include_artifact_hash: bool = False,
        artifact_hash: str | None = None,
    ) -> dict[str, Any]:
        """Return a deterministic JSON-ready artifact payload."""

        payload: dict[str, Any] = {
            "accepted": self.accepted,
            "checked_paths": list(self.checked_paths),
            "dataset_id": self.dataset_id,
            "duplicate_timestamps": self.duplicate_timestamps,
            "halted_sessions": self.halted_sessions,
            "issues": [issue.to_payload() for issue in self.issues],
            "label_visibility": self.label_visibility,
            "missing_bars": self.missing_bars,
            "schema_version": self.schema_version,
            "session_alignment": self.session_alignment,
            "stale_prices": self.stale_prices,
        }
        if include_artifact_hash:
            payload["artifact_hash"] = artifact_hash
        return payload

    def _critical_flag_issues(self) -> tuple[DataQualityIssue, ...]:
        issues: list[DataQualityIssue] = []
        if self.duplicate_timestamps:
            issues.append(
                DataQualityIssue(
                    code="duplicate_timestamps",
                    message=f"duplicate timestamps detected: {self.duplicate_timestamps}",
                )
            )
        if self.missing_bars:
            issues.append(
                DataQualityIssue(
                    code="missing_bars",
                    message=f"missing bars detected: {self.missing_bars}",
                )
            )
        if not self.session_alignment:
            issues.append(
                DataQualityIssue(
                    code="session_alignment",
                    message="session alignment check failed",
                )
            )
        if self.stale_prices:
            issues.append(
                DataQualityIssue(
                    code="stale_prices",
                    message=f"stale prices detected: {self.stale_prices}",
                )
            )
        if self.halted_sessions:
            issues.append(
                DataQualityIssue(
                    code="halted_sessions",
                    message=f"halted sessions detected: {self.halted_sessions}",
                )
            )
        if not self.label_visibility:
            issues.append(
                DataQualityIssue(
                    code="label_visibility",
                    message="label visibility check failed",
                )
            )
        return tuple(issues)


@dataclass(frozen=True, slots=True)
class _DataQualityArtifactWriteResult:
    path: Path
    artifact_hash: str
    artifact: DataQualityArtifact


class DataQualityArtifactWriter:
    """Write deterministic data-quality artifacts."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def write(self, artifact: DataQualityArtifact) -> _DataQualityArtifactWriteResult:
        """Write an artifact and return its path plus canonical hash."""

        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / _artifact_filename(artifact.dataset_id)
        body = _canonical_json(artifact.to_payload(include_artifact_hash=False))
        artifact_hash = f"sha256:{hashlib.sha256(body.encode('utf-8')).hexdigest()}"
        payload = artifact.to_payload(include_artifact_hash=True, artifact_hash=artifact_hash)
        path.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
        return _DataQualityArtifactWriteResult(
            path=path,
            artifact_hash=artifact_hash,
            artifact=artifact,
        )


def _checked_paths(snapshot: Mapping[str, Any]) -> tuple[str, ...]:
    value = snapshot.get("checked_paths", snapshot.get("file_paths", ()))
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError("checked_paths must be a sequence")
    return tuple(str(Path(path)) for path in value)


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _issues(value: Any) -> tuple[DataQualityIssue, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError("issues must be a sequence")
    result: list[DataQualityIssue] = []
    for issue in value:
        if isinstance(issue, DataQualityIssue):
            result.append(issue)
        elif isinstance(issue, Mapping):
            result.append(DataQualityIssue.from_payload(issue))
        else:
            raise ValueError("issues must contain mappings or DataQualityIssue values")
    return tuple(result)


def _non_negative_int(value: Any) -> int:
    result = int(value)
    if result < 0:
        raise ValueError("quality counts must be non-negative")
    return result


def _bool_field(
    payload: Mapping[str, Any],
    field_name: str,
    *,
    default: bool | None = None,
) -> bool:
    value = payload.get(field_name, default)
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be bool")
    return value


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _artifact_filename(dataset_id: str) -> str:
    safe_prefix = re.sub(r"[^A-Za-z0-9_.-]+", "_", dataset_id).strip("._-")
    if not safe_prefix:
        safe_prefix = "dataset"
    digest = hashlib.sha256(dataset_id.encode("utf-8")).hexdigest()[:16]
    return f"{safe_prefix[:64]}-{digest}_data_quality.json"
