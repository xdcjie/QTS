from __future__ import annotations

from typing import Any

import pytest
from qts.core.hashing import stable_json_hash
from qts.research.orchestrator.experiment_runner import ResearchExperimentRunner


def force_clean_reproducibility(monkeypatch: pytest.MonkeyPatch) -> None:
    original = ResearchExperimentRunner._reproducibility_payload
    original_git_output = ResearchExperimentRunner._git_output

    def clean_payload(
        self: ResearchExperimentRunner,
        *,
        job: Any,
        manifest_hash: str,
    ) -> dict[str, Any]:
        payload = original(self, job=job, manifest_hash=manifest_hash)
        payload["git_dirty"] = False
        payload["blockers"] = [
            reason
            for reason in payload.get("blockers", [])
            if reason != "git working tree is dirty"
        ]
        snapshot_payload = {
            key: value
            for key, value in payload.items()
            if key not in {"artifact_id", "payload_hash", "path"}
        }
        payload["payload_hash"] = stable_json_hash(snapshot_payload)
        return payload

    def clean_git_output(
        self: ResearchExperimentRunner,
        args: tuple[str, ...],
    ) -> str:
        if args == ("status", "--short"):
            return ""
        return original_git_output(self, args)

    monkeypatch.setattr(
        ResearchExperimentRunner,
        "_reproducibility_payload",
        clean_payload,
    )
    monkeypatch.setattr(
        ResearchExperimentRunner,
        "_git_output",
        clean_git_output,
    )
