"""Research-system manifest loading and deterministic candidate expansion."""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_hash


@dataclass(frozen=True, slots=True)
class ResearchCandidate:
    """One deterministic research candidate parameter set."""

    candidate_id: str
    parameters: Mapping[str, Any]
    search_type: str = "grid"

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready candidate payload."""

        return {
            "candidate_id": self.candidate_id,
            "parameters": dict(self.parameters),
            "search_type": self.search_type,
        }


@dataclass(frozen=True, slots=True)
class ResearchManifest:
    """Normalized manifest for one research-system run."""

    run_id: str
    question: str
    strategy_id: str
    strategy_entrypoint: str
    strategy_hypothesis: str
    default_config: Path
    dataset_id: str
    data_config: Path
    catalog: str
    roots: tuple[str, ...]
    timeframe: str
    start: str
    end: str
    parameter_grid: Mapping[str, tuple[Any, ...]]
    random_search: Mapping[str, Any]
    promotion_config: Path
    output_root: Path
    split_config: Mapping[str, Any]
    raw: Mapping[str, Any]

    @classmethod
    def from_yaml(cls, path: str | Path) -> ResearchManifest:
        """Load and normalize a research manifest YAML file."""

        manifest_path = Path(path)
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("research manifest must be a YAML mapping")
        run = _required_mapping(payload, "run")
        strategy = _required_mapping(payload, "strategy")
        data = _required_mapping(payload, "data")
        grid = _required_mapping(payload, "parameter_grid")
        random_search = _optional_mapping(payload, "random_search")
        split_config = _optional_mapping(payload, "splits")
        normalized_grid = _parameter_grid(grid)
        return cls(
            run_id=_required_text(run, "id"),
            question=_required_text(run, "question"),
            strategy_id=_required_text(strategy, "id"),
            strategy_entrypoint=_required_text(strategy, "entrypoint"),
            strategy_hypothesis=_required_text(strategy, "hypothesis"),
            default_config=_resolve_path(manifest_path, _required_text(strategy, "default_config")),
            dataset_id=_required_text(data, "dataset_id"),
            data_config=_resolve_path(manifest_path, _required_text(data, "config")),
            catalog=_required_text(data, "catalog"),
            roots=_string_tuple(data.get("roots"), "data.roots"),
            timeframe=_required_text(data, "timeframe"),
            start=_required_text(data, "start"),
            end=_required_text(data, "end"),
            parameter_grid=normalized_grid,
            random_search=_random_search(random_search),
            promotion_config=_resolve_path(
                manifest_path,
                str(payload.get("promotion_config", "configs/promotion/default.yaml")),
            ),
            output_root=_resolve_output_path(
                manifest_path,
                str(payload.get("output_root", "artifacts/research")),
            ),
            split_config=split_config,
            raw=_json_ready_mapping(payload),
        )

    @property
    def manifest_hash(self) -> str:
        """Return the deterministic hash of the normalized manifest."""

        return stable_json_hash(self.to_payload(include_hash=False))

    def candidates(self) -> tuple[ResearchCandidate, ...]:
        """Expand the parameter grid into deterministic candidate IDs."""

        names = tuple(self.parameter_grid)
        results: list[ResearchCandidate] = []
        for values in _cartesian_product(tuple(self.parameter_grid[name] for name in names)):
            parameters = dict(zip(names, values, strict=True))
            results.append(
                ResearchCandidate(
                    candidate_id=_candidate_id(
                        manifest_hash=self.manifest_hash,
                        parameters=parameters,
                        search_type="grid",
                        index=len(results),
                    ),
                    parameters=parameters,
                    search_type="grid",
                )
            )
        results.extend(_random_candidates(self.manifest_hash, self.random_search))
        return tuple(results)

    def grid_candidates(self) -> tuple[ResearchCandidate, ...]:
        """Return only deterministic grid-search candidates."""

        names = tuple(self.parameter_grid)
        results: list[ResearchCandidate] = []
        for values in _cartesian_product(tuple(self.parameter_grid[name] for name in names)):
            parameters = dict(zip(names, values, strict=True))
            results.append(
                ResearchCandidate(
                    candidate_id=_candidate_id(
                        manifest_hash=self.manifest_hash,
                        parameters=parameters,
                        search_type="grid",
                        index=len(results),
                    ),
                    parameters=parameters,
                    search_type="grid",
                )
            )
        return tuple(results)

    def to_payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        """Return the normalized manifest payload."""

        payload: dict[str, Any] = {
            "data": {
                "catalog": self.catalog,
                "config": str(self.data_config),
                "dataset_id": self.dataset_id,
                "end": self.end,
                "roots": list(self.roots),
                "start": self.start,
                "timeframe": self.timeframe,
            },
            "output_root": str(self.output_root),
            "parameter_grid": {name: list(values) for name, values in self.parameter_grid.items()},
            "promotion_config": str(self.promotion_config),
            "random_search": _random_search_payload(self.random_search),
            "run": {
                "id": self.run_id,
                "question": self.question,
            },
            "splits": dict(self.split_config),
            "strategy": {
                "default_config": str(self.default_config),
                "entrypoint": self.strategy_entrypoint,
                "hypothesis": self.strategy_hypothesis,
                "id": self.strategy_id,
            },
        }
        if include_hash:
            payload["manifest_hash"] = self.manifest_hash
        return payload


def write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    """Write deterministic JSONL rows."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(dict(row), sort_keys=True) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _required_mapping(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    value = payload.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _optional_mapping(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    value = payload.get(field_name, {})
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field_name} must not be empty")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return tuple(item.strip() for item in value)


def _parameter_grid(value: Mapping[str, Any]) -> dict[str, tuple[Any, ...]]:
    result: dict[str, tuple[Any, ...]] = {}
    for name in sorted(value):
        values = value[name]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("parameter names must be non-empty strings")
        if not isinstance(values, list) or not values:
            raise ValueError(f"parameter_grid.{name} must not be empty")
        result[name.strip()] = tuple(_json_ready(item) for item in values)
    if not result:
        raise ValueError("parameter_grid must not be empty")
    return result


def _random_search(value: Mapping[str, Any]) -> dict[str, Any]:
    if not value:
        return {}
    samples = value.get("samples")
    if not isinstance(samples, int) or samples < 1:
        raise ValueError("random_search.samples must be a positive integer")
    seed = value.get("seed")
    if not isinstance(seed, int):
        raise ValueError("random_search.seed must be an integer")
    raw_parameters = value.get("parameters")
    if not isinstance(raw_parameters, Mapping):
        raise ValueError("random_search.parameters must be a mapping")
    return {
        "parameters": _parameter_grid(raw_parameters),
        "samples": samples,
        "seed": seed,
    }


def _random_search_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    if not value:
        return {}
    parameters = value.get("parameters")
    if not isinstance(parameters, Mapping):
        return dict(value)
    return {
        "parameters": {name: list(values) for name, values in parameters.items()},
        "samples": value["samples"],
        "seed": value["seed"],
    }


def _random_candidates(
    manifest_hash: str,
    search: Mapping[str, Any],
) -> tuple[ResearchCandidate, ...]:
    if not search:
        return ()
    samples = int(search["samples"])
    generator = random.Random(int(search["seed"]))
    parameter_space = search["parameters"]
    if not isinstance(parameter_space, Mapping):
        raise ValueError("random_search.parameters must be normalized before sampling")
    names = tuple(parameter_space)
    candidates: list[ResearchCandidate] = []
    for index in range(samples):
        parameters = {name: generator.choice(tuple(parameter_space[name])) for name in names}
        candidates.append(
            ResearchCandidate(
                candidate_id=_candidate_id(
                    manifest_hash=manifest_hash,
                    parameters=parameters,
                    search_type="random",
                    index=index,
                ),
                parameters=parameters,
                search_type="random",
            )
        )
    return tuple(candidates)


def _candidate_id(
    *,
    manifest_hash: str,
    parameters: Mapping[str, Any],
    search_type: str,
    index: int,
) -> str:
    candidate_hash = stable_json_hash(
        {
            "index": index,
            "manifest_hash": manifest_hash,
            "parameters": parameters,
            "search_type": search_type,
        }
    )
    return f"cand-{candidate_hash.split(':', maxsplit=1)[1][:12]}"


def _cartesian_product(groups: tuple[tuple[Any, ...], ...]) -> tuple[tuple[Any, ...], ...]:
    if not groups:
        return ((),)
    head, *tail = groups
    suffixes = _cartesian_product(tuple(tail))
    return tuple((item, *suffix) for item in head for suffix in suffixes)


def _resolve_path(config_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    sibling = config_path.parent / path
    if sibling.exists():
        return sibling
    return path


def _resolve_output_path(config_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    sibling = config_path.parent / path
    if value.startswith("../") or sibling.exists():
        return sibling
    return path


def _json_ready_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _json_ready(value) for key, value in payload.items()}


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _json_ready_mapping(value)
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


__all__ = ["ResearchCandidate", "ResearchManifest", "write_jsonl"]
