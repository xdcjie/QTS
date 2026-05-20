"""Deterministic persistence for human-reviewable factor specs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qts.research.factor_spec import FactorSpec


class FactorSpecStore:
    """Owns deterministic storage for non-executable factor spec drafts."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir / "factor-specs"

    def path_for(self, name: str) -> Path:
        """Return the JSON path for a raw spec name."""

        normalized = name.strip()
        if (
            not normalized
            or "/" in normalized
            or "\\" in normalized
            or ".." in normalized
            or normalized.endswith(".json")
        ):
            raise ValueError("factor spec name must be a plain name without .json suffix")
        return self._root_dir / f"{normalized}.json"

    def save(self, spec: FactorSpec) -> Path:
        """Persist a spec as deterministic JSON and return its path."""

        path = self.path_for(spec.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(spec.to_payload(), sort_keys=True, indent=2) + "\n"
        path.write_text(content, encoding="utf-8")
        return path

    def load(self, name: str) -> FactorSpec:
        """Load one persisted spec by raw spec name."""

        payload = json.loads(self.path_for(name).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("factor spec payload must be a JSON object")
        return FactorSpec.from_payload(self._string_key_mapping(payload))

    def list_specs(self) -> tuple[FactorSpec, ...]:
        """Return all persisted specs sorted lexicographically by filename."""

        return tuple(self.load(path.stem) for path in sorted(self._root_dir.glob("*.json")))

    @staticmethod
    def _string_key_mapping(payload: dict[Any, Any]) -> dict[str, Any]:
        return {str(key): value for key, value in payload.items()}
