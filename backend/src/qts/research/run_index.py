"""Research workflow index artifacts.

The workflow summary is the machine evidence source; this module builds a
read-only index and dashboard that point at completed artifacts without
changing research, optimizer, backtest, or promotion decisions.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash


class ResearchRunIndexWriter:
    """Writes read-only index artifacts for a completed workflow summary."""

    def write(
        self,
        *,
        workflow_summary_path: Path,
        workflow_payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Write ``research_index.json`` and ``research_dashboard.md`` beside a summary."""

        output_dir = workflow_summary_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        index_payload = self.payload(
            workflow_summary_path=workflow_summary_path,
            workflow_payload=workflow_payload,
        )
        index_path = output_dir / "research_index.json"
        dashboard_path = output_dir / "research_dashboard.md"
        index_path.write_text(stable_json_dumps(index_payload) + "\n", encoding="utf-8")
        dashboard_path.write_text(self._dashboard(index_payload), encoding="utf-8")
        return {
            "dashboard_path": str(dashboard_path),
            "index_hash": stable_json_hash(index_payload),
            "index_path": str(index_path),
        }

    def payload(
        self,
        *,
        workflow_summary_path: Path,
        workflow_payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Return the canonical research index payload for a workflow summary."""

        artifacts = self._artifacts(workflow_payload)
        return {
            "artifacts": artifacts,
            "paper_live_launches": [],
            "research_manifest": {
                "hash": str(workflow_payload.get("manifest_hash", "")),
                "path": str(workflow_payload.get("manifest_path", "")),
            },
            "schema_version": 1,
            "status": str(workflow_payload.get("status", "")),
            "workflow_id": str(workflow_payload.get("workflow_id", "")),
            "workflow_summary": {
                "hash": self._summary_hash(workflow_summary_path, workflow_payload),
                "path": str(workflow_summary_path),
            },
        }

    def _artifacts(self, workflow_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        artifacts: list[dict[str, Any]] = []
        steps = workflow_payload.get("steps", ())
        if not isinstance(steps, Sequence) or isinstance(steps, str):
            return artifacts
        for step in steps:
            if not isinstance(step, Mapping):
                continue
            step_id = str(step.get("id", ""))
            kind = str(step.get("kind", ""))
            outputs = step.get("outputs", {})
            if not isinstance(outputs, Mapping):
                continue
            self._append_output_artifact(
                artifacts,
                kind=self._manifest_kind(kind),
                path=outputs.get("manifest_path"),
                step_id=step_id,
            )
            self._append_output_artifact(
                artifacts,
                kind="optimizer_validation_summary",
                path=outputs.get("validation_output"),
                step_id=step_id,
            )
            self._append_output_artifact(
                artifacts,
                kind="walk_forward_validation_summary",
                path=outputs.get("walk_forward_validation_output"),
                step_id=step_id,
            )
            self._append_output_artifact(
                artifacts,
                kind="failure_window_veto_summary",
                path=outputs.get("failure_window_veto_output"),
                step_id=step_id,
            )
            self._append_output_artifact(
                artifacts,
                kind="research_report",
                path=outputs.get("report_path"),
                step_id=step_id,
            )
            ranked_results = outputs.get("ranked_results", ())
            if isinstance(ranked_results, Sequence) and not isinstance(ranked_results, str):
                for rank, result in enumerate(ranked_results, start=1):
                    if not isinstance(result, Mapping):
                        continue
                    path = result.get("manifest_path")
                    if not isinstance(path, str) or not path:
                        continue
                    artifacts.append(
                        {
                            "hash": result.get("manifest_hash") or self._path_hash(Path(path)),
                            "kind": "optimizer_manifest",
                            "path": path,
                            "rank": rank,
                            "step_id": step_id,
                        }
                    )
        return sorted(artifacts, key=lambda item: (str(item["kind"]), str(item["path"])))

    @staticmethod
    def _manifest_kind(kind: str) -> str | None:
        if kind == "backtest":
            return "backtest_manifest"
        if kind == "factor_tearsheet":
            return "factor_tearsheet_manifest"
        return None

    def _append_output_artifact(
        self,
        artifacts: list[dict[str, Any]],
        *,
        kind: str | None,
        path: Any,
        step_id: str,
    ) -> None:
        if kind is None or not isinstance(path, str) or not path:
            return
        artifacts.append(
            {
                "hash": self._path_hash(Path(path)),
                "kind": kind,
                "path": path,
                "step_id": step_id,
            }
        )

    @staticmethod
    def _summary_hash(path: Path, payload: Mapping[str, Any]) -> str:
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                return stable_json_hash(payload)
            if isinstance(loaded, Mapping):
                return stable_json_hash(dict(loaded))
        return stable_json_hash(dict(payload))

    @staticmethod
    def _path_hash(path: Path) -> str:
        if not path.exists() or not path.is_file():
            return "unknown"
        return f"sha256:{stable_json_hash(path.read_text(encoding='utf-8'))[7:]}"

    @staticmethod
    def _dashboard(index_payload: Mapping[str, Any]) -> str:
        artifacts = index_payload.get("artifacts", ())
        lines = [
            "# Research Run Dashboard",
            "",
            f"- Workflow ID: {index_payload.get('workflow_id', '')}",
            f"- Status: {index_payload.get('status', '')}",
            f"- Workflow summary: {index_payload.get('workflow_summary', {}).get('path', '')}",
            f"- Research manifest: {index_payload.get('research_manifest', {}).get('path', '')}",
            "",
            "## Artifacts",
            "",
        ]
        if isinstance(artifacts, Sequence) and not isinstance(artifacts, str):
            for artifact in artifacts:
                if not isinstance(artifact, Mapping):
                    continue
                lines.append(
                    f"- {artifact.get('kind', '')}: {artifact.get('path', '')} "
                    f"({artifact.get('hash', '')})"
                )
        lines.append("")
        return "\n".join(lines)


__all__ = ["ResearchRunIndexWriter"]
