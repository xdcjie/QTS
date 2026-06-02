"""Structured research data-quality artifacts.

The artifact records quality results and checked file paths for promotion
review. DataQualityRunner owns deterministic CSV snapshot checks; canonical
calendar/session definitions remain owned by data-domain metadata.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from qts.data.historical.chains import HistoricalChain
from qts.data.sessions import RegularSessionWindow

_MISSING_BAR_POLICIES = frozenset({"block", "record_only"})


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
    missing_bar_policy: str = "block"
    schema_version: int = field(default=2, init=False)

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id is required")
        if any(not path.strip() for path in self.checked_paths):
            raise ValueError("checked_paths must contain non-empty strings")
        for field_name, value in (
            ("duplicate_timestamps", self.duplicate_timestamps),
            ("missing_bars", self.missing_bars),
            ("stale_prices", self.stale_prices),
            ("halted_sessions", self.halted_sessions),
        ):
            if int(value) < 0:
                raise ValueError(f"{field_name} must be non-negative")
        object.__setattr__(
            self,
            "missing_bar_policy",
            _missing_bar_policy(self.missing_bar_policy),
        )

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
        missing_bar_policy = _missing_bar_policy(snapshot.get("missing_bar_policy", "block"))
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
            accepted=_accepted_from_quality_checks(
                checked_paths=checked_paths,
                issues=tuple(issues),
                duplicate_timestamps=duplicate_timestamps,
                missing_bars=missing_bars,
                session_alignment=session_alignment,
                stale_prices=stale_prices,
                halted_sessions=halted_sessions,
                label_visibility=label_visibility,
                missing_bar_policy=missing_bar_policy,
            ),
            checked_paths=checked_paths,
            issues=tuple(issues),
            duplicate_timestamps=duplicate_timestamps,
            missing_bars=missing_bars,
            session_alignment=session_alignment,
            stale_prices=stale_prices,
            halted_sessions=halted_sessions,
            label_visibility=label_visibility,
            missing_bar_policy=missing_bar_policy,
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
            missing_bar_policy=artifact.missing_bar_policy,
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
            missing_bar_policy=_missing_bar_policy(payload.get("missing_bar_policy", "block")),
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
            missing_bar_policy=artifact.missing_bar_policy,
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
                seen_codes.add(issue.code)
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
            "missing_bar_policy": self.missing_bar_policy,
            "schema_version": self.schema_version,
            "session_alignment": self.session_alignment,
            "stale_prices": self.stale_prices,
        }
        if include_artifact_hash:
            payload["artifact_hash"] = artifact_hash
        return payload

    def _critical_flag_issues(self) -> tuple[DataQualityIssue, ...]:
        issues: list[DataQualityIssue] = []
        if not self.checked_paths:
            issues.append(
                DataQualityIssue(
                    code="checked_paths",
                    message="checked_paths must not be empty",
                )
            )
        if not self.accepted:
            issues.append(
                DataQualityIssue(
                    code="accepted",
                    message="data quality artifact is not accepted",
                )
            )
        if self.duplicate_timestamps:
            issues.append(
                DataQualityIssue(
                    code="duplicate_timestamps",
                    message=f"duplicate timestamps detected: {self.duplicate_timestamps}",
                )
            )
        if self.missing_bars and self.missing_bar_policy == "block":
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
class DataQualityRunner:
    """Generate structured data-quality evidence from dataset file snapshots."""

    dataset_id: str
    timeframe: str
    start: str | None = None
    end: str | None = None
    calendar: str | None = None
    stale_price_max_repeats: int | None = None
    windows: tuple[Mapping[str, str], ...] = ()
    missing_bar_policy: str = "block"

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id is required")
        if not self.timeframe.strip():
            raise ValueError("timeframe is required")
        if self.calendar is not None and not self.calendar.strip():
            raise ValueError("calendar is required when provided")
        if self.stale_price_max_repeats is not None and self.stale_price_max_repeats < 1:
            raise ValueError("stale_price_max_repeats must be positive")
        object.__setattr__(
            self,
            "missing_bar_policy",
            _missing_bar_policy(self.missing_bar_policy),
        )
        self._validated_windows()

    def run(self, snapshot: Mapping[str, Any]) -> DataQualityArtifact:
        """Run deterministic file-level quality checks and return an artifact."""

        checked_paths = self._checked_paths(snapshot)
        existing_bar_paths = tuple(path for path in checked_paths if Path(path).exists())
        duplicate_timestamps = 0
        missing_bars = 0
        stale_prices = 0
        session_alignment = True
        label_visibility = True
        issues: list[DataQualityIssue] = []
        for path_text in checked_paths:
            if not Path(path_text).exists():
                issues.append(
                    DataQualityIssue(
                        code="missing_checked_path",
                        message=f"checked path does not exist: {path_text}",
                    )
                )
        for path_text in existing_bar_paths:
            path = Path(path_text)
            rows = self._read_csv_rows(path)
            timestamps = self._timestamps(rows)
            duplicate_timestamps += self._duplicate_count(timestamps)
            missing_bars += self._missing_bar_count(
                timestamps,
                session_window=self._session_window_for_path(path),
            )
            stale_prices += self._stale_price_count(rows)
            if not self._session_aligned(timestamps):
                session_alignment = False
        for label_path in self._label_paths(snapshot):
            if not Path(label_path).exists():
                continue
            if not self._labels_visible(Path(label_path)):
                label_visibility = False

        halted_sessions = int(snapshot.get("halted_sessions", 0) or 0)
        artifact = DataQualityArtifact(
            dataset_id=self.dataset_id,
            accepted=_accepted_from_quality_checks(
                checked_paths=checked_paths,
                issues=tuple(issues),
                duplicate_timestamps=duplicate_timestamps,
                missing_bars=missing_bars,
                session_alignment=session_alignment,
                stale_prices=stale_prices,
                halted_sessions=halted_sessions,
                label_visibility=label_visibility,
                missing_bar_policy=self.missing_bar_policy,
            ),
            checked_paths=checked_paths,
            issues=tuple(issues),
            duplicate_timestamps=duplicate_timestamps,
            missing_bars=missing_bars,
            session_alignment=session_alignment,
            stale_prices=stale_prices,
            halted_sessions=halted_sessions,
            label_visibility=label_visibility,
            missing_bar_policy=self.missing_bar_policy,
        )
        return DataQualityArtifact(
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
            missing_bar_policy=artifact.missing_bar_policy,
        )

    def _checked_paths(self, snapshot: Mapping[str, Any]) -> tuple[str, ...]:
        explicit = snapshot.get("checked_paths", snapshot.get("file_paths"))
        if explicit is not None:
            return _checked_paths({"checked_paths": explicit})
        paths: list[str] = []
        for row in snapshot.get("dataset_files", ()):
            if isinstance(row, Mapping) and isinstance(row.get("path"), str):
                paths.append(str(Path(str(row["path"]))))
        paths.extend(self._label_paths(snapshot))
        return tuple(dict.fromkeys(paths))

    @staticmethod
    def _label_paths(snapshot: Mapping[str, Any]) -> tuple[str, ...]:
        value = snapshot.get("label_paths", ())
        if not isinstance(value, Sequence) or isinstance(value, str):
            return ()
        return tuple(str(Path(path)) for path in value)

    @staticmethod
    def _read_csv_rows(path: Path) -> tuple[dict[str, str], ...]:
        if path.suffix.lower() != ".csv":
            return ()
        with path.open("r", encoding="utf-8", newline="") as handle:
            return tuple(dict(row) for row in csv.DictReader(handle))

    @classmethod
    def _timestamps(cls, rows: Sequence[Mapping[str, str]]) -> tuple[datetime, ...]:
        timestamps: list[datetime] = []
        for row in rows:
            value = row.get("timestamp") or row.get("datetime") or row.get("ts_event")
            if value:
                timestamps.append(cls._parse_datetime(value))
        return tuple(timestamps)

    @staticmethod
    def _duplicate_count(timestamps: Sequence[datetime]) -> int:
        return len(timestamps) - len(set(timestamps))

    def _missing_bar_count(
        self,
        timestamps: Sequence[datetime],
        *,
        session_window: RegularSessionWindow | None = None,
    ) -> int:
        step = self._timeframe_seconds()
        if step is None:
            return 0
        if session_window is not None:
            return self._missing_bar_count_for_session_window(
                timestamps,
                step=step,
                session_window=session_window,
            )
        windows = self._parsed_windows()
        if windows:
            return sum(
                self._missing_bar_count_for_window(
                    timestamps,
                    step=step,
                    start=start,
                    end=end,
                )
                for start, end in windows
            )
        missing = 0
        unique = sorted(set(timestamps))
        start = None if self.start is None else self._parse_datetime(self.start)
        end = None if self.end is None else self._parse_datetime(self.end)
        if not unique:
            if start is not None and end is not None and end > start:
                return int((end - start).total_seconds()) // step
            return 0
        if start is not None and unique[0] > start:
            missing += int((unique[0] - start).total_seconds()) // step
        if end is not None and unique[-1] < end:
            seconds_to_end = int((end - unique[-1]).total_seconds())
            if seconds_to_end > step:
                missing += max((seconds_to_end // step) - 1, 0)
        for left, right in itertools.pairwise(unique):
            seconds = int((right - left).total_seconds())
            if seconds > step:
                missing += max((seconds // step) - 1, 0)
        return missing

    def _missing_bar_count_for_session_window(
        self,
        timestamps: Sequence[datetime],
        *,
        step: int,
        session_window: RegularSessionWindow,
    ) -> int:
        unique = sorted(
            timestamp
            for timestamp in set(timestamps)
            if self._timestamp_in_declared_scope(timestamp)
        )
        missing = 0
        previous: datetime | None = None
        previous_session_id: str | None = None
        for timestamp in unique:
            session_id = session_window.session_id_for_timestamp(timestamp)
            if session_id is None:
                previous = None
                previous_session_id = None
                continue
            if previous is not None and session_id == previous_session_id:
                seconds = int((timestamp - previous).total_seconds())
                if seconds > step:
                    missing += max((seconds // step) - 1, 0)
            previous = timestamp
            previous_session_id = session_id
        return missing

    def _missing_bar_count_for_window(
        self,
        timestamps: Sequence[datetime],
        *,
        step: int,
        start: datetime,
        end: datetime,
    ) -> int:
        unique = sorted(timestamp for timestamp in set(timestamps) if start <= timestamp < end)
        if not unique:
            return int((end - start).total_seconds()) // step
        missing = 0
        if unique[0] > start:
            missing += int((unique[0] - start).total_seconds()) // step
        seconds_to_end = int((end - unique[-1]).total_seconds())
        if seconds_to_end > step:
            missing += max((seconds_to_end // step) - 1, 0)
        for left, right in itertools.pairwise(unique):
            seconds = int((right - left).total_seconds())
            if seconds > step:
                missing += max((seconds // step) - 1, 0)
        return missing

    def _timestamp_in_declared_scope(self, timestamp: datetime) -> bool:
        windows = self._parsed_windows()
        if windows:
            return any(start <= timestamp < end for start, end in windows)
        start = None if self.start is None else self._parse_datetime(self.start)
        end = None if self.end is None else self._parse_datetime(self.end)
        if start is not None and timestamp < start:
            return False
        if end is not None and timestamp >= end:
            return False
        return True

    @staticmethod
    def _session_window_for_path(path: Path) -> RegularSessionWindow | None:
        if path.suffix.lower() != ".csv":
            return None
        chains_dir = path.parent.parent / "chains"
        candidates = (
            chains_dir / f"{path.stem}.json",
            chains_dir / f"{path.stem.upper()}.json",
        )
        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                return HistoricalChain.load(candidate).session_window()
            except (OSError, ValueError, json.JSONDecodeError):
                return None
        return None

    def _stale_price_count(self, rows: Sequence[Mapping[str, str]]) -> int:
        if self.stale_price_max_repeats is None:
            return 0
        stale = 0
        previous: str | None = None
        repeat_count = 0
        for row in rows:
            close = row.get("close")
            if close is None:
                previous = None
                repeat_count = 0
                continue
            if close == previous:
                repeat_count += 1
                if repeat_count >= self.stale_price_max_repeats:
                    stale += 1
            else:
                previous = close
                repeat_count = 0
        return stale

    def _session_aligned(self, timestamps: Sequence[datetime]) -> bool:
        windows = self._parsed_windows()
        if windows:
            return all(
                any(start <= timestamp < end for start, end in windows) for timestamp in timestamps
            )
        start = None if self.start is None else self._parse_datetime(self.start)
        end = None if self.end is None else self._parse_datetime(self.end)
        for timestamp in timestamps:
            if start is not None and timestamp < start:
                return False
            if end is not None and timestamp >= end:
                return False
        return True

    @classmethod
    def _labels_visible(cls, path: Path) -> bool:
        for row in cls._read_csv_rows(path):
            label_timestamp = row.get("label_timestamp")
            if label_timestamp is None:
                continue
            visible_at = row.get("visible_at")
            if not visible_at:
                return False
            if cls._parse_datetime(visible_at) < cls._parse_datetime(label_timestamp):
                return False
        return True

    def _timeframe_seconds(self) -> int | None:
        value = self.timeframe.strip().lower()
        unit = value[-1:]
        amount_text = value[:-1]
        if not amount_text.isdigit():
            return None
        amount = int(amount_text)
        if unit == "s":
            return amount
        if unit == "m":
            return amount * 60
        if unit == "h":
            return amount * 60 * 60
        return None

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("data quality timestamps must be timezone-aware")
        return parsed

    def _validated_windows(self) -> None:
        previous_end: datetime | None = None
        for window in self.windows:
            if not isinstance(window, Mapping):
                raise ValueError("data quality windows must contain mappings")
            start = _required_text(window, "start")
            end = _required_text(window, "end")
            start_time = self._parse_datetime(start)
            end_time = self._parse_datetime(end)
            if start_time >= end_time:
                raise ValueError("data quality window start must be before end")
            if previous_end is not None and start_time < previous_end:
                raise ValueError("data quality windows must be sorted and non-overlapping")
            previous_end = end_time

    def _parsed_windows(self) -> tuple[tuple[datetime, datetime], ...]:
        return tuple(
            (
                self._parse_datetime(_required_text(window, "start")),
                self._parse_datetime(_required_text(window, "end")),
            )
            for window in self.windows
        )


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


def _accepted_from_quality_checks(
    *,
    checked_paths: tuple[str, ...],
    issues: tuple[DataQualityIssue, ...],
    duplicate_timestamps: int,
    missing_bars: int,
    session_alignment: bool,
    stale_prices: int,
    halted_sessions: int,
    label_visibility: bool,
    missing_bar_policy: str,
) -> bool:
    """Derive the data-quality verdict from raw blocker inputs."""

    return (
        bool(checked_paths)
        and not any(issue.blocker for issue in issues)
        and duplicate_timestamps == 0
        and (missing_bars == 0 or missing_bar_policy == "record_only")
        and session_alignment
        and stale_prices == 0
        and halted_sessions == 0
        and label_visibility
    )


def _missing_bar_policy(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing_bar_policy is required")
    policy = value.strip()
    if policy not in _MISSING_BAR_POLICIES:
        raise ValueError(f"missing_bar_policy must be one of {sorted(_MISSING_BAR_POLICIES)}")
    return policy


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
