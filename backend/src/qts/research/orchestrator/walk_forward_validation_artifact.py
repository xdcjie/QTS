"""Walk-forward validation verdict artifact owner."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class WalkForwardValidationResult:
    """Typed walk-forward verdict and score evidence."""

    train_score: Decimal
    test_score: Decimal
    max_train_test_gap: Decimal
    max_allowed_train_test_gap: Decimal
    accepted: bool
    train_manifest_hash: str
    train_manifest_path: Path
    test_manifest_hash: str
    test_manifest_path: Path
    manifest_statistics_hash: str

    @property
    def consistent(self) -> bool:
        """Return whether the train/test split passed the consistency gate."""

        return self.accepted

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical walk-forward validation payload."""

        return {
            "consistent": self.consistent,
            "manifest_statistics_hash": self.manifest_statistics_hash,
            "max_allowed_train_test_gap": float(self.max_allowed_train_test_gap),
            "max_train_test_gap": float(self.max_train_test_gap),
            "test_windows": [
                {
                    "accepted": self.accepted,
                    "manifest_hash": self.test_manifest_hash,
                    "manifest_path": str(self.test_manifest_path),
                    "name": "split-001-test",
                    "score": float(self.test_score),
                    "train_manifest_hash": self.train_manifest_hash,
                    "train_manifest_path": str(self.train_manifest_path),
                    "train_score": float(self.train_score),
                }
            ],
        }


class WalkForwardValidationArtifact:
    """Build walk-forward validation verdicts from train/test result evidence."""

    def result(
        self,
        *,
        train_objective_value: object,
        train_manifest: Mapping[str, Any],
        train_manifest_path: Path,
        test_objective_value: object,
        test_manifest: Mapping[str, Any],
        test_manifest_path: Path,
    ) -> WalkForwardValidationResult:
        """Compute the walk-forward verdict from immutable train/test evidence."""

        train = self._decimal(train_objective_value)
        test = self._decimal(test_objective_value)
        gap = abs(train - test)
        allowed_gap = max(abs(train), abs(test), Decimal("1")) * Decimal("0.25")
        accepted = test >= Decimal("0") and gap <= allowed_gap
        return WalkForwardValidationResult(
            train_score=train,
            test_score=test,
            max_train_test_gap=gap,
            max_allowed_train_test_gap=allowed_gap,
            accepted=accepted,
            train_manifest_hash=str(train_manifest.get("manifest_hash", "")),
            train_manifest_path=train_manifest_path,
            test_manifest_hash=str(test_manifest.get("manifest_hash", "")),
            test_manifest_path=test_manifest_path,
            manifest_statistics_hash=str(test_manifest.get("statistics_hash", "")),
        )

    def payload(
        self,
        *,
        train_objective_value: object,
        train_manifest: Mapping[str, Any],
        train_manifest_path: Path,
        test_objective_value: object,
        test_manifest: Mapping[str, Any],
        test_manifest_path: Path,
    ) -> dict[str, Any]:
        """Return the walk-forward validation payload from typed result evidence."""

        return self.result(
            train_objective_value=train_objective_value,
            train_manifest=train_manifest,
            train_manifest_path=train_manifest_path,
            test_objective_value=test_objective_value,
            test_manifest=test_manifest,
            test_manifest_path=test_manifest_path,
        ).to_payload()

    @staticmethod
    def _decimal(value: object) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal("0")


__all__ = ["WalkForwardValidationArtifact", "WalkForwardValidationResult"]
