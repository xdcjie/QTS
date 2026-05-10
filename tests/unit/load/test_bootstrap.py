from __future__ import annotations

from qts.load.bootstrap import bootstrap_local


def test_bootstrap_local_is_idempotent(tmp_path) -> None:  # type: ignore[no-untyped-def]
    first = bootstrap_local(tmp_path)
    second = bootstrap_local(tmp_path)

    assert first == second
    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / ".qts-bootstrap").read_text(encoding="utf-8").strip() == "ok"
