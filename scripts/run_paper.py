from __future__ import annotations

from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime


def main() -> None:
    """Perform main."""
    runtime = start_runtime(
        StartRuntimeCommand(
            runtime_mode="paper_simulated",
            config_ref="configs/paper_simulated.yaml",
            operator_id="paper-local",
            idempotency_key="run-paper-local",
            reason="local paper runtime start",
        )
    )
    print(runtime.status)


if __name__ == "__main__":
    main()
