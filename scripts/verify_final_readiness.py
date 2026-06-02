"""Verify final-state product readiness gates."""

from __future__ import annotations

from pathlib import Path

from qts.quality.final_readiness import run_final_readiness


def main() -> int:
    """Run final-readiness checks from the repository root."""

    repo_root = Path.cwd()
    violations = run_final_readiness(repo_root)
    if not violations:
        print("Final-readiness gates passed.")
        return 0
    print("Final-readiness gates failed:")
    for violation in violations:
        print(f"  {violation.format()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
