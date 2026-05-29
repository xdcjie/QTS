"""Trial-budget decisions and hash-chained ledger records."""

from __future__ import annotations

import json
from collections.abc import Mapping, MutableSequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.core.time import require_aware_datetime


@dataclass(frozen=True, slots=True)
class TrialBudgetDecision:
    """Decision returned for one requested research trial."""

    accepted: bool
    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("trial budget decision reason is required")


@dataclass(frozen=True, slots=True)
class TrialBudgetRecord:
    """One durable row in the trial-budget decision ledger."""

    record_id: str
    record_type: Literal["trial_budget_decision"]
    payload_hash: str
    previous_record_hash: str | None
    created_at: datetime
    payload: Mapping[str, Any]

    @classmethod
    def create(
        cls,
        payload: Mapping[str, Any],
        *,
        previous_record_hash: str | None = None,
        created_at: datetime | None = None,
        record_id: str | None = None,
    ) -> TrialBudgetRecord:
        """Create one deterministic trial-budget ledger record."""

        timestamp = created_at or datetime.now(UTC)
        require_aware_datetime(timestamp, name="created_at")
        json_payload = cls._json_safe_payload(payload)
        payload_hash = stable_json_hash(json_payload)
        record_hash = cls._record_hash(
            payload_hash=payload_hash,
            previous_record_hash=previous_record_hash,
            created_at=timestamp,
            payload=json_payload,
        )
        if record_id is not None and record_id != record_hash:
            raise ValueError("record_id must match record_hash")
        return cls(
            record_id=record_id or record_hash,
            record_type="trial_budget_decision",
            payload_hash=payload_hash,
            previous_record_hash=previous_record_hash,
            created_at=timestamp,
            payload=json_payload,
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> TrialBudgetRecord:
        """Rehydrate one ledger record from a JSON-safe payload."""

        record_type = cls._required_text(payload, "record_type")
        if record_type != "trial_budget_decision":
            raise ValueError(f"unknown trial budget record_type: {record_type}")
        created_at = datetime.fromisoformat(cls._required_text(payload, "created_at"))
        require_aware_datetime(created_at, name="created_at")
        return cls(
            record_id=cls._required_text(payload, "record_id"),
            record_type="trial_budget_decision",
            payload_hash=cls._required_text(payload, "payload_hash"),
            previous_record_hash=cls._optional_text(payload, "previous_record_hash"),
            created_at=created_at,
            payload=cls._required_mapping(payload, "payload"),
        )

    @property
    def record_hash(self) -> str:
        """Return the deterministic hash of this ledger record."""

        return self._record_hash(
            payload_hash=self.payload_hash,
            previous_record_hash=self.previous_record_hash,
            created_at=self.created_at,
            payload=self.payload,
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready ledger row."""

        return {
            "created_at": self.created_at.isoformat(),
            "payload": dict(self.payload),
            "payload_hash": self.payload_hash,
            "previous_record_hash": self.previous_record_hash,
            "record_id": self.record_id,
            "record_type": self.record_type,
        }

    @classmethod
    def expected_payload_hash(cls, payload: Mapping[str, Any]) -> str:
        """Return the canonical payload hash expected for a record payload."""

        return stable_json_hash(cls._json_safe_payload(payload))

    @classmethod
    def _record_hash(
        cls,
        *,
        payload_hash: str,
        previous_record_hash: str | None,
        created_at: datetime,
        payload: Mapping[str, Any],
    ) -> str:
        return stable_json_hash(
            {
                "created_at": created_at.isoformat(),
                "payload": cls._json_safe_payload(payload),
                "payload_hash": payload_hash,
                "previous_record_hash": previous_record_hash,
                "record_type": "trial_budget_decision",
            }
        )

    @staticmethod
    def _json_safe_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise ValueError("trial budget record payload must be a JSON object")
        normalized = json.loads(stable_json_dumps(dict(payload)))
        if not isinstance(normalized, dict):
            raise ValueError("trial budget record payload must be a JSON object")
        return normalized

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} is required")
        return value

    @staticmethod
    def _optional_text(payload: Mapping[str, Any], field_name: str) -> str | None:
        value = payload.get(field_name)
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} must be a non-empty string or null")
        return value

    @staticmethod
    def _required_mapping(payload: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
        value = payload.get(field_name)
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a JSON object")
        return value


class TrialBudgetLedger:
    """Owns the append-only JSONL trial-budget decision ledger."""

    def __init__(self, root_or_path: str | Path) -> None:
        path = Path(root_or_path)
        self.path = path if path.suffix == ".jsonl" else path / "trial_budget_ledger.jsonl"

    def append_decision(
        self,
        payload: Mapping[str, Any],
        *,
        created_at: datetime | None = None,
    ) -> TrialBudgetRecord:
        """Append one trial-budget decision and return the persisted record."""

        records = self.list()
        previous_record_hash = records[-1].record_hash if records else None
        record = TrialBudgetRecord.create(
            payload,
            previous_record_hash=previous_record_hash,
            created_at=created_at,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_payload(), sort_keys=True) + "\n")
        return record

    def list(self) -> tuple[TrialBudgetRecord, ...]:
        """Read all trial-budget ledger records in file order."""

        if not self.path.exists():
            return ()
        records: list[TrialBudgetRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, Mapping):
                raise ValueError("trial budget ledger row must be a JSON object")
            records.append(TrialBudgetRecord.from_payload(payload))
        return tuple(records)

    def verify_hash_chain(self) -> tuple[str, ...]:
        """Verify payload hashes, record hashes, and previous-record links."""

        if not self.path.exists():
            return ()
        reasons: list[str] = []
        previous_record_hash: str | None = None
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = self._parse_record(line, line_number, reasons)
            if record is None:
                previous_record_hash = None
                continue
            expected_payload_hash = TrialBudgetRecord.expected_payload_hash(record.payload)
            if record.payload_hash != expected_payload_hash:
                reasons.append(
                    f"payload_hash mismatch at line {line_number}: "
                    f"expected {expected_payload_hash}, found {record.payload_hash}"
                )
            if record.previous_record_hash != previous_record_hash:
                reasons.append(
                    f"previous_record_hash mismatch at line {line_number}: "
                    f"expected {previous_record_hash}, found {record.previous_record_hash}"
                )
            if record.record_id != record.record_hash:
                reasons.append(
                    f"record_hash mismatch at line {line_number}: "
                    f"expected {record.record_hash}, found {record.record_id}"
                )
            previous_record_hash = record.record_hash
        return tuple(reasons)

    @staticmethod
    def _parse_record(
        line: str,
        line_number: int,
        reasons: MutableSequence[str],
    ) -> TrialBudgetRecord | None:
        try:
            payload = json.loads(line)
            if not isinstance(payload, Mapping):
                reasons.append(f"invalid JSON record at line {line_number}: expected object")
                return None
            return TrialBudgetRecord.from_payload(payload)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            reasons.append(f"invalid trial budget record at line {line_number}: {exc}")
            return None


class TrialBudgetManager:
    """Enforces finite research trial budgets before a trial is run."""

    def __init__(
        self,
        *,
        ledger: TrialBudgetLedger,
        campaign_trial_limit: int | None = None,
        strategy_family_trial_limit: int | None = None,
        factor_family_trial_limit: int | None = None,
        idea_trial_limit: int | None = None,
        compute_budget_limit: int | float | Decimal | None = None,
    ) -> None:
        self.ledger = ledger
        self._campaign_trial_limit = self._optional_non_negative_int(
            campaign_trial_limit,
            "campaign_trial_limit",
        )
        self._strategy_family_trial_limit = self._optional_non_negative_int(
            strategy_family_trial_limit,
            "strategy_family_trial_limit",
        )
        self._factor_family_trial_limit = self._optional_non_negative_int(
            factor_family_trial_limit,
            "factor_family_trial_limit",
        )
        self._idea_trial_limit = self._optional_non_negative_int(
            idea_trial_limit,
            "idea_trial_limit",
        )
        self._compute_budget_limit = self._optional_non_negative_decimal(
            compute_budget_limit,
            "compute_budget_limit",
        )

    def request_trial(
        self,
        *,
        trial_id: str,
        campaign_id: str,
        generation_id: str,
        strategy_family: str,
        factor_family: str,
        idea_id: str,
        time_window: str | None = None,
        compute_cost: int | float | Decimal | None = None,
        created_at: datetime | None = None,
    ) -> TrialBudgetDecision:
        """Decide whether one trial can consume budget, then write the decision."""

        timestamp = created_at or datetime.now(UTC)
        require_aware_datetime(timestamp, name="created_at")
        payload: dict[str, Any] = {
            "campaign_id": self._required_text(campaign_id, "campaign_id"),
            "factor_family": self._required_text(factor_family, "factor_family"),
            "generation_id": self._required_text(generation_id, "generation_id"),
            "idea_id": self._required_text(idea_id, "idea_id"),
            "strategy_family": self._required_text(strategy_family, "strategy_family"),
            "trial_id": self._required_text(trial_id, "trial_id"),
        }
        if time_window is not None:
            payload["time_window"] = self._required_text(time_window, "time_window")
        normalized_compute_cost = self._optional_non_negative_decimal(
            compute_cost,
            "compute_cost",
        )
        if normalized_compute_cost is not None:
            payload["compute_cost"] = normalized_compute_cost

        decision = self._decide(payload)
        payload["accepted"] = decision.accepted
        payload["decision_reason"] = decision.reason
        self.ledger.append_decision(payload, created_at=timestamp)
        return decision

    def accepted_trial_count(
        self,
        campaign_id: str,
        *,
        strategy_family: str | None = None,
        factor_family: str | None = None,
    ) -> int:
        """Return the number of trials that consumed budget for a campaign.

        This is the multiple-testing trial count ``N`` threaded from the search
        budget into candidate selection: every accepted trial is one configuration
        tested. Optionally narrow the count to a strategy or factor family so the
        multiplicity correction can be applied per family. ``campaign_id`` is
        required.
        """

        resolved_campaign = self._required_text(campaign_id, "campaign_id")
        payloads = self._accepted_payloads(resolved_campaign)
        if strategy_family is not None:
            payloads = tuple(
                payload
                for payload in payloads
                if payload.get("strategy_family")
                == self._required_text(strategy_family, "strategy_family")
            )
        if factor_family is not None:
            payloads = tuple(
                payload
                for payload in payloads
                if payload.get("factor_family")
                == self._required_text(factor_family, "factor_family")
            )
        return len(payloads)

    def _decide(self, payload: Mapping[str, Any]) -> TrialBudgetDecision:
        accepted_payloads = self._accepted_payloads(str(payload["campaign_id"]))
        campaign_count = len(accepted_payloads)
        campaign_decision = self._trial_limit_decision(
            "campaign",
            campaign_count,
            self._campaign_trial_limit,
        )
        if campaign_decision is not None:
            return campaign_decision

        strategy_count = self._count_matching(
            accepted_payloads,
            "strategy_family",
            str(payload["strategy_family"]),
        )
        strategy_decision = self._trial_limit_decision(
            "strategy family",
            strategy_count,
            self._strategy_family_trial_limit,
        )
        if strategy_decision is not None:
            return strategy_decision

        factor_count = self._count_matching(
            accepted_payloads,
            "factor_family",
            str(payload["factor_family"]),
        )
        factor_decision = self._trial_limit_decision(
            "factor family",
            factor_count,
            self._factor_family_trial_limit,
        )
        if factor_decision is not None:
            return factor_decision

        idea_count = self._count_matching(accepted_payloads, "idea_id", str(payload["idea_id"]))
        idea_decision = self._trial_limit_decision("idea", idea_count, self._idea_trial_limit)
        if idea_decision is not None:
            return idea_decision

        compute_decision = self._compute_budget_decision(accepted_payloads, payload)
        if compute_decision is not None:
            return compute_decision
        return TrialBudgetDecision(accepted=True, reason="accepted within trial budget")

    def _accepted_payloads(self, campaign_id: str) -> tuple[Mapping[str, Any], ...]:
        return tuple(
            record.payload
            for record in self.ledger.list()
            if record.payload.get("accepted") is True
            and record.payload.get("campaign_id") == campaign_id
        )

    def _compute_budget_decision(
        self,
        accepted_payloads: tuple[Mapping[str, Any], ...],
        payload: Mapping[str, Any],
    ) -> TrialBudgetDecision | None:
        if self._compute_budget_limit is None:
            return None
        compute_cost = Decimal(str(payload.get("compute_cost", 0)))
        consumed = sum(
            (Decimal(str(item.get("compute_cost", 0))) for item in accepted_payloads),
            Decimal("0"),
        )
        next_total = consumed + compute_cost
        if next_total > self._compute_budget_limit:
            return TrialBudgetDecision(
                accepted=False,
                reason=(
                    "compute budget exceeded: "
                    f"{consumed}/{self._compute_budget_limit} accepted, "
                    f"requested {compute_cost}"
                ),
            )
        return None

    @staticmethod
    def _trial_limit_decision(
        scope_name: str,
        accepted_count: int,
        limit: int | None,
    ) -> TrialBudgetDecision | None:
        if limit is not None and accepted_count >= limit:
            return TrialBudgetDecision(
                accepted=False,
                reason=f"{scope_name} trial budget exceeded: {accepted_count}/{limit} accepted",
            )
        return None

    @staticmethod
    def _count_matching(
        payloads: tuple[Mapping[str, Any], ...],
        field_name: str,
        expected: str,
    ) -> int:
        return sum(1 for payload in payloads if payload.get(field_name) == expected)

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        resolved = str(value).strip()
        if not resolved:
            raise ValueError(f"{field_name} is required")
        return resolved

    @staticmethod
    def _optional_non_negative_int(value: int | None, field_name: str) -> int | None:
        if value is None:
            return None
        if value < 0:
            raise ValueError(f"{field_name} must be non-negative")
        return value

    @staticmethod
    def _optional_non_negative_decimal(
        value: int | float | Decimal | None,
        field_name: str,
    ) -> Decimal | None:
        if value is None:
            return None
        resolved = Decimal(str(value))
        if not resolved.is_finite() or resolved < 0:
            raise ValueError(f"{field_name} must be a non-negative finite value")
        return resolved


__all__ = [
    "TrialBudgetDecision",
    "TrialBudgetLedger",
    "TrialBudgetManager",
    "TrialBudgetRecord",
]
