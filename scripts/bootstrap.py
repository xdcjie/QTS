#!/usr/bin/env python
"""Idempotent local bootstrap for live-beta development."""

from __future__ import annotations

from pathlib import Path

from qts.load.bootstrap import bootstrap_local


def main() -> None:
    """Perform main."""
    bootstrap_local(Path(".qts-local"))


if __name__ == "__main__":
    main()
