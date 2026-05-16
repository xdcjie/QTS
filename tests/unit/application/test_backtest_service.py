from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace

from pytest import MonkeyPatch


def test_research_backtest_submit_returns_manifest_and_artifacts(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    import qts.application.services.backtest as service_module
    from qts.application.dto.backtest import BacktestRequestDTO
    from qts.application.services.backtest import BacktestService

    config_path = tmp_path / "research.yaml"
    config_path.write_text("mode: backtest\n", encoding="utf-8")
    manifest_path = tmp_path / "bt-research.manifest.json"
    equity_curve_path = tmp_path / "bt-research.equity_curve.ndjson"
    orders_path = tmp_path / "bt-research.orders.ndjson"
    fills_path = tmp_path / "bt-research.fills.ndjson"
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": "bt-research",
                "metrics": {"total_return": "0.125", "max_drawdown": "0.02"},
                "artifacts": {
                    "equity_curve": {
                        "path": str(equity_curve_path),
                        "sha256": "sha256:eq",
                    },
                    "orders": {"path": str(orders_path), "sha256": "sha256:orders"},
                    "fills": {"path": str(fills_path), "sha256": "sha256:fills"},
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_run_backtest(path: Path, *, output_dir: Path) -> SimpleNamespace:
        assert path == config_path
        assert output_dir == tmp_path / "runs"
        return SimpleNamespace(
            manifest_path=manifest_path,
            result=SimpleNamespace(
                actor_ref=object(),
                runtime_session=object(),
                artifact_hashes={"runtime": "internal"},
            ),
        )

    monkeypatch.setattr(service_module, "run_backtest", fake_run_backtest)

    result = BacktestService(output_dir=tmp_path / "runs").submit(
        BacktestRequestDTO(config_path=str(config_path))
    )

    assert result.run_id == "bt-research"
    assert result.manifest_path == str(manifest_path)
    assert result.equity_curve_path == str(equity_curve_path)
    assert result.orders_path == str(orders_path)
    assert result.fills_path == str(fills_path)
    assert result.metrics == {"total_return": "0.125", "max_drawdown": "0.02"}
    assert result.artifact_hashes == {
        "equity_curve": "sha256:eq",
        "orders": "sha256:orders",
        "fills": "sha256:fills",
    }


def test_research_batch_submit_is_deterministic(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    import qts.application.services.backtest as service_module
    from qts.application.dto.backtest import BacktestRequestDTO
    from qts.application.services.backtest import BacktestService

    config_paths = [tmp_path / "first.yaml", tmp_path / "second.yaml"]
    for path in config_paths:
        path.write_text("mode: backtest\n", encoding="utf-8")

    def fake_run_backtest(path: Path, *, output_dir: Path) -> SimpleNamespace:
        run_id = f"bt-{path.stem}"
        manifest_path = output_dir / f"{run_id}.manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "metrics": {"total_return": path.stem},
                    "artifacts": {
                        "equity_curve": {
                            "path": str(output_dir / f"{run_id}.equity_curve.ndjson"),
                            "sha256": f"sha256:{path.stem}:equity",
                        },
                        "orders": {
                            "path": str(output_dir / f"{run_id}.orders.ndjson"),
                            "sha256": f"sha256:{path.stem}:orders",
                        },
                        "fills": {
                            "path": str(output_dir / f"{run_id}.fills.ndjson"),
                            "sha256": f"sha256:{path.stem}:fills",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        return SimpleNamespace(manifest_path=manifest_path, result=SimpleNamespace())

    monkeypatch.setattr(service_module, "run_backtest", fake_run_backtest)
    service = BacktestService(output_dir=tmp_path / "runs")
    requests = [BacktestRequestDTO(config_path=str(path)) for path in config_paths]

    first = service.submit_batch(requests)
    second = service.submit_batch(requests)

    assert first == second
    assert [result.run_id for result in first] == ["bt-first", "bt-second"]


def test_research_code_cannot_access_runtime_actor_internals(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    import qts.application.services.backtest as service_module
    from qts.application.dto.backtest import BacktestRequestDTO, BacktestRunResultDTO
    from qts.application.services.backtest import BacktestService

    config_path = tmp_path / "research.yaml"
    config_path.write_text("mode: backtest\n", encoding="utf-8")
    manifest_path = tmp_path / "bt-research.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": "bt-research",
                "metrics": {},
                "artifacts": {
                    "equity_curve": {"path": "equity.ndjson", "sha256": "sha256:eq"},
                    "orders": {"path": "orders.ndjson", "sha256": "sha256:orders"},
                    "fills": {"path": "fills.ndjson", "sha256": "sha256:fills"},
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_run_backtest(path: Path, *, output_dir: Path) -> SimpleNamespace:
        return SimpleNamespace(
            manifest_path=manifest_path,
            engine=object(),
            actors={"account": object()},
            result=SimpleNamespace(
                runtime_session=object(),
                actor_ref=object(),
                execution_adapter=object(),
                broker_adapter=object(),
            ),
        )

    monkeypatch.setattr(service_module, "run_backtest", fake_run_backtest)

    result = BacktestService(output_dir=tmp_path / "runs").submit(
        BacktestRequestDTO(config_path=str(config_path))
    )

    assert isinstance(result, BacktestRunResultDTO)
    exposed_names = {field.name for field in fields(result)}
    assert exposed_names == {
        "run_id",
        "manifest_path",
        "equity_curve_path",
        "orders_path",
        "fills_path",
        "metrics",
        "artifact_hashes",
    }
    for forbidden in (
        "engine",
        "actor",
        "actors",
        "actor_ref",
        "runtime_session",
        "execution_adapter",
        "broker_adapter",
        "report_hash",
        "summary_path",
        "status",
    ):
        assert forbidden not in exposed_names
        assert not hasattr(result, forbidden)
