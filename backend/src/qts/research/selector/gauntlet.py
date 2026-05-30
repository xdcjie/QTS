"""Validation gauntlet gates for selected autonomous research candidates."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.audit_log import ResearchAuditLog


@dataclass(frozen=True, slots=True)
class GateDecision:
    """One validation gate decision with audit-ready evidence."""

    gate_name: str
    accepted: bool
    reasons: tuple[str, ...]
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.gate_name.strip():
            raise ValueError("gate_name is required")
        object.__setattr__(self, "reasons", tuple(str(reason) for reason in self.reasons))
        object.__setattr__(self, "evidence", self._json_object(self.evidence))

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready gate payload."""

        return {
            "accepted": self.accepted,
            "evidence": dict(self.evidence),
            "gate_name": self.gate_name,
            "reasons": list(self.reasons),
        }

    @staticmethod
    def _json_object(payload: Mapping[str, Any]) -> dict[str, Any]:
        loaded = json.loads(stable_json_dumps(dict(payload)))
        if not isinstance(loaded, dict):
            raise ValueError("gate evidence must be a JSON object")
        return loaded


@dataclass(frozen=True, slots=True)
class WalkForwardGate:
    """Validate walk-forward consistency evidence for one survivor."""

    min_test_windows: int = 1
    max_train_test_gap: float | None = None

    def __post_init__(self) -> None:
        if self.min_test_windows < 1:
            raise ValueError("min_test_windows must be positive")
        if self.max_train_test_gap is not None and self.max_train_test_gap < 0:
            raise ValueError("max_train_test_gap must be non-negative")

    def evaluate(self, candidate: Mapping[str, Any]) -> GateDecision:
        """Return the walk-forward gate decision."""

        evidence = self._walk_forward_evidence(candidate)
        reasons: list[str] = []
        if not evidence:
            return GateDecision(
                gate_name="walk_forward",
                accepted=False,
                reasons=("walk_forward: evidence missing",),
                evidence={},
            )
        if evidence.get("consistent") is not True:
            reasons.append("walk_forward: consistency check failed")

        windows = self._windows(evidence.get("test_windows"))
        accepted_windows = [window for window in windows if window.get("accepted") is True]
        if len(accepted_windows) < self.min_test_windows:
            reasons.append(
                f"walk_forward: accepted test windows {len(accepted_windows)} "
                f"below {self.min_test_windows}"
            )
        for window in windows:
            if window.get("accepted") is False:
                reasons.append(
                    f"walk_forward: {window.get('name', 'window')!s} test window rejected"
                )

        gap = self._number(evidence.get("max_train_test_gap"))
        if (
            self.max_train_test_gap is not None
            and gap is not None
            and gap > self.max_train_test_gap
        ):
            reasons.append(
                f"walk_forward: max_train_test_gap {gap:g} exceeds {self.max_train_test_gap:g}"
            )

        return GateDecision(
            gate_name="walk_forward",
            accepted=not reasons,
            reasons=tuple(reasons),
            evidence={
                **_artifact_metadata(evidence),
                "accepted_test_windows": len(accepted_windows),
                "consistent": evidence.get("consistent") is True,
                "max_train_test_gap": gap,
                "test_window_count": len(windows),
            },
        )

    @staticmethod
    def _walk_forward_evidence(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        validation = candidate.get("validation")
        if not isinstance(validation, Mapping):
            return {}
        walk_forward = validation.get("walk_forward")
        return walk_forward if isinstance(walk_forward, Mapping) else {}

    @staticmethod
    def _windows(value: Any) -> tuple[Mapping[str, Any], ...]:
        if not isinstance(value, Sequence) or isinstance(value, str):
            return ()
        return tuple(item for item in value if isinstance(item, Mapping))

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, int | float):
            return float(value)
        try:
            return float(str(value))
        except ValueError:
            return None


@dataclass(frozen=True, slots=True)
class FailureWindowVetoGate:
    """Reject candidates that breach adverse-window loss constraints."""

    max_drawdown: float

    def __post_init__(self) -> None:
        if self.max_drawdown < 0:
            raise ValueError("max_drawdown must be non-negative")

    def evaluate(self, candidate: Mapping[str, Any]) -> GateDecision:
        """Return the failure-window veto decision."""

        windows = self._failure_windows(candidate)
        if not windows:
            return GateDecision(
                gate_name="failure_window_veto",
                accepted=False,
                reasons=("failure_window_veto: evidence missing",),
                evidence={},
            )
        reasons: list[str] = []
        veto_count = 0
        for window in windows:
            if window.get("report_only") is True:
                continue
            veto_count += 1
            if window.get("breached") is True:
                reasons.append(f"failure_window_veto: {window.get('name', 'window')!s} breached")
            drawdown = WalkForwardGate._number(window.get("max_drawdown"))
            if drawdown is not None and abs(drawdown) > self.max_drawdown:
                reasons.append(
                    "failure_window_veto: "
                    f"{window.get('name', 'window')!s} max_drawdown {abs(drawdown):g} "
                    f"exceeds {self.max_drawdown:g}"
                )
        return GateDecision(
            gate_name="failure_window_veto",
            accepted=not reasons,
            reasons=tuple(reasons),
            evidence={
                **_artifact_metadata(windows[0]),
                "max_drawdown": self.max_drawdown,
                "veto_window_count": veto_count,
                "window_count": len(windows),
            },
        )

    @staticmethod
    def _failure_windows(candidate: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
        validation = candidate.get("validation")
        if not isinstance(validation, Mapping):
            return ()
        return WalkForwardGate._windows(validation.get("failure_windows"))


@dataclass(frozen=True, slots=True)
class CostStressGate:
    """Validate fee, cost, and slippage sensitivity."""

    max_degradation: float
    max_slippage_sensitivity: float
    min_stressed_score: float | None = None

    def __post_init__(self) -> None:
        if self.max_degradation < 0:
            raise ValueError("max_degradation must be non-negative")
        if self.max_slippage_sensitivity < 0:
            raise ValueError("max_slippage_sensitivity must be non-negative")

    def evaluate(self, candidate: Mapping[str, Any]) -> GateDecision:
        """Return cost-stress and slippage-sensitivity decision."""

        evidence = self._cost_stress(candidate)
        if not evidence:
            return GateDecision(
                gate_name="cost_stress",
                accepted=False,
                reasons=("cost_stress: evidence missing",),
                evidence={},
            )
        reasons: list[str] = []
        degradation = WalkForwardGate._number(evidence.get("degradation"))
        if degradation is None:
            reasons.append("cost_stress: degradation missing")
        elif degradation > self.max_degradation:
            reasons.append(
                f"cost_stress: degradation {degradation:g} exceeds {self.max_degradation:g}"
            )
        slippage = WalkForwardGate._number(evidence.get("slippage_sensitivity"))
        if slippage is None:
            reasons.append("cost_stress: slippage_sensitivity missing")
        elif slippage > self.max_slippage_sensitivity:
            reasons.append(
                f"cost_stress: slippage_sensitivity {slippage:g} exceeds "
                f"{self.max_slippage_sensitivity:g}"
            )
        stressed_score = WalkForwardGate._number(evidence.get("stressed_score"))
        if (
            self.min_stressed_score is not None
            and stressed_score is not None
            and stressed_score < self.min_stressed_score
        ):
            reasons.append(
                f"cost_stress: stressed_score {stressed_score:g} below {self.min_stressed_score:g}"
            )
        return GateDecision(
            gate_name="cost_stress",
            accepted=not reasons,
            reasons=tuple(reasons),
            evidence={
                **_artifact_metadata(evidence),
                "degradation": degradation,
                "slippage_sensitivity": slippage,
                "stressed_score": stressed_score,
            },
        )

    @staticmethod
    def _cost_stress(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        validation = candidate.get("validation")
        if not isinstance(validation, Mapping):
            return {}
        cost_stress = validation.get("cost_stress")
        return cost_stress if isinstance(cost_stress, Mapping) else {}


@dataclass(frozen=True, slots=True)
class CorrelationGate:
    """Reject candidates too correlated with active strategies."""

    max_active_correlation: float

    def __post_init__(self) -> None:
        if self.max_active_correlation < 0:
            raise ValueError("max_active_correlation must be non-negative")

    def evaluate(self, candidate: Mapping[str, Any]) -> GateDecision:
        """Return active-correlation decision."""

        evidence = self._correlation(candidate)
        if not evidence:
            return GateDecision(
                gate_name="correlation",
                accepted=False,
                reasons=("correlation: evidence missing",),
                evidence={},
            )
        max_correlation = WalkForwardGate._number(evidence.get("max_active_correlation"))
        reasons: list[str] = []
        snapshot = evidence.get("active_portfolio_snapshot")
        active_status = (
            snapshot.get("active_portfolio_status") if isinstance(snapshot, Mapping) else None
        )
        active_count = (
            WalkForwardGate._number(snapshot.get("active_candidate_count"))
            if isinstance(snapshot, Mapping)
            else None
        )
        candidate_return_count = (
            WalkForwardGate._number(snapshot.get("candidate_return_count"))
            if isinstance(snapshot, Mapping)
            else None
        )
        if active_status not in {"computed", "no_active_candidates"}:
            reasons.append("correlation: active_portfolio_status missing")
        if candidate_return_count is None or candidate_return_count <= 0:
            reasons.append("correlation: candidate return series missing")
        if active_status == "computed" and (active_count is None or active_count <= 0):
            reasons.append("correlation: active candidates missing")
        if max_correlation is None:
            reasons.append("correlation: max_active_correlation missing")
        elif abs(max_correlation) > self.max_active_correlation:
            reasons.append(
                f"correlation: max_active_correlation {abs(max_correlation):g} "
                f"exceeds {self.max_active_correlation:g}"
            )
        return GateDecision(
            gate_name="correlation",
            accepted=not reasons,
            reasons=tuple(reasons),
            evidence={
                **_artifact_metadata(evidence),
                "active_candidate_count": active_count,
                "active_portfolio_status": active_status,
                "candidate_return_count": candidate_return_count,
                "max_active_correlation": max_correlation,
            },
        )

    @staticmethod
    def _correlation(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        validation = candidate.get("validation")
        if not isinstance(validation, Mapping):
            return {}
        correlation = validation.get("correlation")
        return correlation if isinstance(correlation, Mapping) else {}


@dataclass(frozen=True, slots=True)
class CapacityGate:
    """Validate capacity and turnover constraints."""

    max_turnover: float | None = None

    def __post_init__(self) -> None:
        if self.max_turnover is not None and self.max_turnover < 0:
            raise ValueError("max_turnover must be non-negative")

    def evaluate(self, candidate: Mapping[str, Any]) -> GateDecision:
        """Return capacity and turnover decision."""

        evidence = self._capacity(candidate)
        if not evidence:
            return GateDecision(
                gate_name="capacity",
                accepted=False,
                reasons=("capacity: evidence missing",),
                evidence={},
            )
        estimated_capacity = WalkForwardGate._number(evidence.get("estimated_capacity"))
        required_capital = WalkForwardGate._number(evidence.get("required_capital"))
        turnover = WalkForwardGate._number(evidence.get("turnover"))
        reasons: list[str] = []
        if estimated_capacity is None:
            reasons.append("capacity: estimated_capacity missing")
        if required_capital is None:
            reasons.append("capacity: required_capital missing")
        if (
            estimated_capacity is not None
            and required_capital is not None
            and required_capital > estimated_capacity
        ):
            reasons.append(
                f"capacity: required_capital {self._number_text(required_capital)} "
                f"exceeds estimated_capacity {self._number_text(estimated_capacity)}"
            )
        if self.max_turnover is not None:
            if turnover is None:
                reasons.append("capacity: turnover missing")
            elif turnover > self.max_turnover:
                reasons.append(f"capacity: turnover {turnover:g} exceeds {self.max_turnover:g}")
        return GateDecision(
            gate_name="capacity",
            accepted=not reasons,
            reasons=tuple(reasons),
            evidence={
                **_artifact_metadata(evidence),
                "estimated_capacity": estimated_capacity,
                "required_capital": required_capital,
                "turnover": turnover,
            },
        )

    @staticmethod
    def _capacity(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        validation = candidate.get("validation")
        if not isinstance(validation, Mapping):
            return {}
        capacity = validation.get("capacity")
        return capacity if isinstance(capacity, Mapping) else {}

    @staticmethod
    def _number_text(value: float) -> str:
        return f"{value:.12g}"


@dataclass(frozen=True, slots=True)
class NoLookaheadGate:
    """Validate no-lookahead evidence contains timing-protocol proof.

    String-only scans are rejected for promotion-grade validation.
    The evidence must contain timing_validation with real feature
    timestamp and label cutoff checks.
    """

    def evaluate(self, candidate: Mapping[str, Any]) -> GateDecision:
        """Return the no-lookahead gate decision."""

        evidence = self._no_lookahead_evidence(candidate)
        reasons: list[str] = []

        if not evidence:
            return GateDecision(
                gate_name="no_lookahead",
                accepted=False,
                reasons=("no_lookahead: evidence missing",),
                evidence={},
            )

        if evidence.get("passed") is not True:
            reasons.append("no_lookahead: validation evidence failed")

        # String-only scan is insufficient for promotion-grade validation.
        string_scan_only = evidence.get("string_scan_only")
        timing_validation = evidence.get("timing_validation")

        if string_scan_only is True:
            reasons.append(
                "no_lookahead: string-only scan is insufficient for promotion-grade validation"
            )

        if not isinstance(timing_validation, Mapping):
            reasons.append(
                "no_lookahead: timing_validation evidence missing; "
                "only string scan detected which is insufficient for promotion"
            )
        else:
            timing_passed = timing_validation.get("passed")
            if timing_passed is not True:
                reasons.append("no_lookahead: timing protocol validation failed")

            timing_violations = timing_validation.get("violations")
            if isinstance(timing_violations, Sequence) and not isinstance(timing_violations, str):
                for violation in timing_violations:
                    if isinstance(violation, Mapping):
                        code = violation.get("code", "")
                        msg = violation.get("message", "")
                        if code or msg:
                            reasons.append(f"no_lookahead: {code}: {msg}")

            window_overlaps = timing_validation.get("window_overlaps")
            if isinstance(window_overlaps, Sequence) and not isinstance(window_overlaps, str):
                for overlap in window_overlaps:
                    if isinstance(overlap, str) and overlap.strip():
                        reasons.append(f"no_lookahead: window overlap: {overlap}")

        gate_evidence: dict[str, Any] = {
            **_artifact_metadata(evidence),
            "has_timing_validation": isinstance(timing_validation, Mapping),
            "passed": evidence.get("passed") is True,
            "string_scan_only": string_scan_only is True,
        }
        if isinstance(timing_validation, Mapping):
            gate_evidence["timing_checked_features"] = timing_validation.get("checked_features", [])
            gate_evidence["timing_violation_count"] = len(timing_validation.get("violations", []))

        return GateDecision(
            gate_name="no_lookahead",
            accepted=not reasons,
            reasons=tuple(reasons),
            evidence=gate_evidence,
        )

    @staticmethod
    def _no_lookahead_evidence(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
        validation = candidate.get("validation")
        if not isinstance(validation, Mapping):
            return {}
        no_lookahead = validation.get("no_lookahead")
        return no_lookahead if isinstance(no_lookahead, Mapping) else {}


@dataclass(frozen=True, slots=True)
class DeflatedSharpeGate:
    """Reject candidates whose Deflated Sharpe Ratio falls below the threshold.

    The Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) is the probability
    that the candidate's true Sharpe exceeds the expected maximum Sharpe of the
    ``N`` trials run in its family. Because the deflation benchmark grows with the
    trial count, a candidate with a high *raw* Sharpe but a poor *deflated* Sharpe
    fails this gate. Evidence is read from the multiplicity-adjustment section that
    ``CandidateSelector`` records on each candidate.
    """

    min_deflated_sharpe_ratio: float = 0.95

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_deflated_sharpe_ratio <= 1.0:
            raise ValueError("min_deflated_sharpe_ratio must be in [0, 1]")

    def evaluate(self, candidate: Mapping[str, Any]) -> GateDecision:
        """Return the deflated-Sharpe gate decision."""

        evidence = _multiplicity_evidence(candidate)
        if not evidence:
            return GateDecision(
                gate_name="deflated_sharpe",
                accepted=False,
                reasons=("deflated_sharpe: multiplicity adjustment evidence missing",),
                evidence={},
            )
        dsr = WalkForwardGate._number(evidence.get("deflated_sharpe_ratio"))
        trial_count = WalkForwardGate._number(evidence.get("trial_count"))
        reasons: list[str] = []
        if dsr is None:
            reasons.append("deflated_sharpe: deflated_sharpe_ratio missing")
        elif dsr < self.min_deflated_sharpe_ratio:
            reasons.append(
                f"deflated_sharpe: deflated_sharpe_ratio {dsr:g} "
                f"below {self.min_deflated_sharpe_ratio:g}"
            )
        return GateDecision(
            gate_name="deflated_sharpe",
            accepted=not reasons,
            reasons=tuple(reasons),
            evidence={
                "deflated_sharpe_ratio": dsr,
                "expected_maximum_sharpe": WalkForwardGate._number(
                    evidence.get("expected_maximum_sharpe")
                ),
                "min_deflated_sharpe_ratio": self.min_deflated_sharpe_ratio,
                "observed_sharpe": WalkForwardGate._number(evidence.get("observed_sharpe")),
                "trial_count": int(trial_count) if trial_count is not None else None,
            },
        )


@dataclass(frozen=True, slots=True)
class PBOGate:
    """Reject candidates whose Probability of Backtest Overfitting is too high.

    PBO is estimated by Combinatorially-Symmetric Cross-Validation (Bailey,
    Borwein, Lopez de Prado & Zhu 2017): the frequency with which the in-sample
    best configuration under-performs the median out of sample. Evidence is read
    from the multiplicity-adjustment section recorded by ``CandidateSelector``.
    """

    max_pbo: float = 0.50

    def __post_init__(self) -> None:
        if not 0.0 <= self.max_pbo <= 1.0:
            raise ValueError("max_pbo must be in [0, 1]")

    def evaluate(self, candidate: Mapping[str, Any]) -> GateDecision:
        """Return the PBO gate decision."""

        evidence = _multiplicity_evidence(candidate)
        if not evidence:
            return GateDecision(
                gate_name="pbo",
                accepted=False,
                reasons=("pbo: multiplicity adjustment evidence missing",),
                evidence={},
            )
        pbo = WalkForwardGate._number(evidence.get("probability_of_backtest_overfitting"))
        reasons: list[str] = []
        if pbo is None:
            reasons.append("pbo: probability_of_backtest_overfitting missing")
        elif pbo > self.max_pbo:
            reasons.append(
                f"pbo: probability_of_backtest_overfitting {pbo:g} exceeds {self.max_pbo:g}"
            )
        return GateDecision(
            gate_name="pbo",
            accepted=not reasons,
            reasons=tuple(reasons),
            evidence={
                "max_pbo": self.max_pbo,
                "probability_of_backtest_overfitting": pbo,
            },
        )


def _multiplicity_evidence(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    adjustment = candidate.get("multiplicity_adjustment")
    return adjustment if isinstance(adjustment, Mapping) else {}


@dataclass(frozen=True, slots=True)
class ValidationGauntletResult:
    """Complete validation gauntlet decision for one selected candidate."""

    candidate_id: str
    accepted: bool
    gate_decisions: tuple[GateDecision, ...]
    deterministic_replay_status: str
    no_lookahead_status: str
    reasons: tuple[str, ...]
    audit_record_id: str | None = None

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        object.__setattr__(self, "reasons", tuple(str(reason) for reason in self.reasons))

    @property
    def validation_hash(self) -> str:
        """Return the deterministic hash of the gauntlet artifact."""

        return stable_json_hash(self._payload_without_hash())

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready validation result."""

        payload = self._payload_without_hash()
        payload["validation_hash"] = self.validation_hash
        return payload

    def to_audit_payload(self) -> dict[str, Any]:
        """Return the payload used for ResearchAuditLog evidence records."""

        payload = self.to_payload()
        payload.pop("audit_record_id", None)
        return payload

    def with_audit_record_id(self, audit_record_id: str) -> ValidationGauntletResult:
        """Return an equivalent result linked to a persisted audit record."""

        return ValidationGauntletResult(
            candidate_id=self.candidate_id,
            accepted=self.accepted,
            gate_decisions=self.gate_decisions,
            deterministic_replay_status=self.deterministic_replay_status,
            no_lookahead_status=self.no_lookahead_status,
            reasons=self.reasons,
            audit_record_id=audit_record_id,
        )

    def _payload_without_hash(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "audit_record_id": self.audit_record_id,
            "candidate_id": self.candidate_id,
            "deterministic_replay_status": self.deterministic_replay_status,
            "gate_decisions": [decision.to_payload() for decision in self.gate_decisions],
            "no_lookahead_status": self.no_lookahead_status,
            "reasons": list(self.reasons),
        }


class ValidationGauntlet:
    """Runs all validation gates required before promotion packet generation."""

    def __init__(
        self,
        *,
        walk_forward_gate: WalkForwardGate | None = None,
        failure_window_gate: FailureWindowVetoGate | None = None,
        cost_stress_gate: CostStressGate | None = None,
        correlation_gate: CorrelationGate | None = None,
        capacity_gate: CapacityGate | None = None,
        no_lookahead_gate: NoLookaheadGate | None = None,
        deflated_sharpe_gate: DeflatedSharpeGate | None = None,
        pbo_gate: PBOGate | None = None,
        require_artifacts: bool = False,
    ) -> None:
        self.walk_forward_gate = walk_forward_gate or WalkForwardGate()
        self.failure_window_gate = failure_window_gate or FailureWindowVetoGate(max_drawdown=0.25)
        self.cost_stress_gate = cost_stress_gate or CostStressGate(
            max_degradation=0.30,
            max_slippage_sensitivity=0.20,
        )
        self.correlation_gate = correlation_gate or CorrelationGate(max_active_correlation=0.80)
        self.capacity_gate = capacity_gate or CapacityGate()
        self.no_lookahead_gate = no_lookahead_gate or NoLookaheadGate()
        # Multiplicity gates are opt-in: they run only when a multiplicity-aware
        # gauntlet is constructed with them, so callers that have not yet attached
        # multiplicity-adjustment evidence keep their existing gate set.
        self.deflated_sharpe_gate = deflated_sharpe_gate
        self.pbo_gate = pbo_gate
        self.require_artifacts = require_artifacts

    def validate(
        self,
        candidate: Mapping[str, Any],
        *,
        audit_log: ResearchAuditLog | None = None,
        created_at: datetime | None = None,
    ) -> ValidationGauntletResult:
        """Run all gates and optionally append an audit record."""

        normalized_candidate = self._json_candidate(candidate)
        artifact_reasons: tuple[str, ...] = ()
        if self.require_artifacts:
            normalized_candidate, artifact_reasons = self._candidate_with_artifact_payloads(
                normalized_candidate
            )
        candidate_id = self._candidate_id(normalized_candidate)
        decisions: list[GateDecision] = [
            self.walk_forward_gate.evaluate(normalized_candidate),
            self.failure_window_gate.evaluate(normalized_candidate),
            self.cost_stress_gate.evaluate(normalized_candidate),
            self.correlation_gate.evaluate(normalized_candidate),
            self.capacity_gate.evaluate(normalized_candidate),
        ]
        if self.deflated_sharpe_gate is not None:
            decisions.append(self.deflated_sharpe_gate.evaluate(normalized_candidate))
        if self.pbo_gate is not None:
            decisions.append(self.pbo_gate.evaluate(normalized_candidate))
        # ``no_lookahead`` is evaluated last so the status logic can read it as the
        # final decision regardless of which optional gates are configured.
        decisions.append(self.no_lookahead_gate.evaluate(normalized_candidate))
        gate_decisions = tuple(decisions)
        status_reasons: list[str] = []
        deterministic_status = self._status(
            normalized_candidate,
            field_name="deterministic_replay",
            failed_reason="deterministic_replay: replay evidence failed",
            missing_reason="deterministic_replay: evidence missing",
            reasons=status_reasons,
        )
        no_lookahead_decision = gate_decisions[-1]
        if no_lookahead_decision.accepted:
            no_lookahead_status = "passed"
        elif no_lookahead_decision.reasons:
            no_lookahead_status = "failed"
            status_reasons.extend(
                reason for reason in no_lookahead_decision.reasons if reason not in status_reasons
            )
        else:
            no_lookahead_status = "missing"
            status_reasons.append("no_lookahead: evidence missing")
        reasons = (
            artifact_reasons
            + tuple(reason for decision in gate_decisions for reason in decision.reasons)
            + tuple(status_reasons)
        )
        result = ValidationGauntletResult(
            candidate_id=candidate_id,
            accepted=not reasons,
            gate_decisions=gate_decisions,
            deterministic_replay_status=deterministic_status,
            no_lookahead_status=no_lookahead_status,
            reasons=reasons,
        )
        if audit_log is None:
            return result
        record = audit_log.append(
            "evidence_validated",
            result.to_audit_payload(),
            created_at=created_at,
        )
        return result.with_audit_record_id(record.record_id)

    @staticmethod
    def _status(
        candidate: Mapping[str, Any],
        *,
        field_name: str,
        failed_reason: str,
        missing_reason: str,
        reasons: list[str],
    ) -> str:
        validation = candidate.get("validation")
        if not isinstance(validation, Mapping):
            reasons.append(missing_reason)
            return "missing"
        evidence = validation.get(field_name)
        if not isinstance(evidence, Mapping):
            reasons.append(missing_reason)
            return "missing"
        if evidence.get("passed") is True:
            return "passed"
        reasons.append(failed_reason)
        return "failed"

    @staticmethod
    def _json_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
        loaded = json.loads(stable_json_dumps(dict(candidate)))
        if not isinstance(loaded, dict):
            raise ValueError("candidate must be a JSON object")
        return loaded

    @staticmethod
    def _candidate_id(candidate: Mapping[str, Any]) -> str:
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise ValueError("candidate_id is required")
        return candidate_id.strip()

    def _candidate_with_artifact_payloads(
        self,
        candidate: Mapping[str, Any],
    ) -> tuple[dict[str, Any], tuple[str, ...]]:
        validation = candidate.get("validation")
        if not isinstance(validation, Mapping):
            return dict(candidate), ("validation artifacts: validation section missing",)
        artifact_refs = validation.get("artifacts")
        if not isinstance(artifact_refs, Mapping):
            return dict(candidate), ("validation artifacts: artifact refs missing",)
        reasons: list[str] = []
        sections: dict[str, Any] = {}
        for artifact_name, target_section in _REQUIRED_VALIDATION_ARTIFACTS.items():
            ref = artifact_refs.get(artifact_name)
            payload = self._load_validation_artifact(artifact_name, ref, reasons)
            if payload is None:
                continue
            if target_section == "failure_windows":
                windows = payload.get("failure_windows")
                if isinstance(windows, Sequence) and not isinstance(windows, str):
                    sections[target_section] = [
                        {
                            **dict(window),
                            **_artifact_metadata(payload),
                        }
                        for window in windows
                        if isinstance(window, Mapping)
                    ]
                else:
                    reasons.append(f"{artifact_name}: payload.failure_windows must be a sequence")
                continue
            sections[target_section] = payload
        return {**dict(candidate), "validation": {**dict(validation), **sections}}, tuple(reasons)

    def _load_validation_artifact(
        self,
        artifact_name: str,
        ref: Any,
        reasons: list[str],
    ) -> Mapping[str, Any] | None:
        if not isinstance(ref, Mapping):
            reasons.append(f"{artifact_name}: artifact ref missing")
            return None
        path_text = ref.get("path")
        expected_hash = ref.get("payload_hash")
        if not isinstance(path_text, str) or not path_text.strip():
            reasons.append(f"{artifact_name}: artifact path missing")
            return None
        if not isinstance(expected_hash, str) or not expected_hash.strip():
            reasons.append(f"{artifact_name}: payload_hash missing for {path_text}")
            return None
        path = Path(path_text)
        if not path.exists():
            reasons.append(f"{artifact_name}: artifact path does not exist: {path}")
            return None
        try:
            wrapper = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            reasons.append(f"{artifact_name}: artifact unreadable: {path}: {exc}")
            return None
        if not isinstance(wrapper, Mapping):
            reasons.append(f"{artifact_name}: artifact must be a JSON object: {path}")
            return None
        if wrapper.get("evidence_source") != "backtest_pipeline_artifact":
            reasons.append(
                f"{artifact_name}: artifact evidence_source is not backtest_pipeline_artifact"
            )
        payload = wrapper.get("payload")
        if not isinstance(payload, Mapping):
            reasons.append(f"{artifact_name}: payload must be a JSON object: {path}")
            return None
        actual_hash = stable_json_hash(payload)
        recorded_hash = wrapper.get("payload_hash")
        if recorded_hash != actual_hash:
            reasons.append(
                f"{artifact_name}: artifact payload_hash mismatch at {path}: "
                f"{actual_hash} != {recorded_hash}"
            )
        if expected_hash != actual_hash:
            reasons.append(
                f"{artifact_name}: artifact ref payload_hash mismatch at {path}: "
                f"{actual_hash} != {expected_hash}"
            )
        return {**dict(payload), "artifact_path": str(path), "payload_hash": actual_hash}


_REQUIRED_VALIDATION_ARTIFACTS = {
    "capacity_report": "capacity",
    "correlation_report": "correlation",
    "cost_stress": "cost_stress",
    "deterministic_replay": "deterministic_replay",
    "failure_window_veto": "failure_windows",
    "no_lookahead": "no_lookahead",
    "walk_forward_validation": "walk_forward",
}


def _artifact_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for field_name in ("artifact_path", "payload_hash"):
        value = payload.get(field_name)
        if isinstance(value, str) and value.strip():
            metadata[field_name] = value
    return metadata


__all__ = [
    "CapacityGate",
    "CorrelationGate",
    "CostStressGate",
    "DeflatedSharpeGate",
    "FailureWindowVetoGate",
    "GateDecision",
    "NoLookaheadGate",
    "PBOGate",
    "ValidationGauntlet",
    "ValidationGauntletResult",
    "WalkForwardGate",
]
