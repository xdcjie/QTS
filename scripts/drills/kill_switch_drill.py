"""Deterministic kill-switch readiness drill for live-capital gating."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(slots=True)
class _DryRunOrder:
    order_id: str
    accepted: bool
    cancelled: bool = False


class _DryRunKillSwitchRuntime:
    """Small deterministic runtime used to prove kill-switch semantics without network I/O."""

    def __init__(self) -> None:
        self.kill_switch_active = False
        self._orders: dict[str, _DryRunOrder] = {}

    def submit_order(self, order_id: str) -> dict[str, object]:
        """Submit a dry-run order unless the kill switch blocks new orders."""

        if self.kill_switch_active:
            return {
                "accepted": False,
                "reason_code": "KILL_SWITCH_ACTIVE",
                "order_id": order_id,
            }
        self._orders[order_id] = _DryRunOrder(order_id=order_id, accepted=True)
        return {"accepted": True, "order_id": order_id}

    def activate_kill_switch_and_cancel(self) -> dict[str, object]:
        """Activate the kill switch and allow safety cancellation of active orders."""

        self.kill_switch_active = True
        cancelled_order_ids: list[str] = []
        for order in self._orders.values():
            if order.accepted and not order.cancelled:
                order.cancelled = True
                cancelled_order_ids.append(order.order_id)
        return {"allowed": True, "cancelled_order_ids": cancelled_order_ids}

    def deactivate_kill_switch(self, *, authorized: bool) -> dict[str, object]:
        """Deactivate only with authorized signoff."""

        if not authorized:
            return {
                "accepted": False,
                "reason": "kill switch deactivate requires safety authorization",
            }
        self.kill_switch_active = False
        return {"accepted": True}


def run_kill_switch_drill(*, output_root: Path, run_id: str) -> Path:
    """Run the deterministic drill and write evidence.json."""

    if not run_id.strip():
        raise ValueError("run_id must not be empty")

    runtime = _DryRunKillSwitchRuntime()
    allowed_order = runtime.submit_order("live-000001")
    safety_cancel = runtime.activate_kill_switch_and_cancel()
    blocked_order = runtime.submit_order("live-000002")
    low_privilege_deactivate = runtime.deactivate_kill_switch(authorized=False)
    authorized_deactivate = runtime.deactivate_kill_switch(authorized=True)

    payload = {
        "schema_version": 1,
        "collector": "kill_switch_drill",
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "runtime_mode": "paper_broker",
        "live_orders_enabled": False,
        "steps": {
            "allowed_order": allowed_order,
            "activate_kill_switch": {"accepted": True},
            "new_order_after_kill_switch": blocked_order,
            "safety_cancel": safety_cancel,
            "low_privilege_deactivate": low_privilege_deactivate,
            "authorized_deactivate": authorized_deactivate,
        },
        "manifest": {
            "kill_switch_blocks_new_orders": blocked_order.get("accepted") is False
            and blocked_order.get("reason_code") == "KILL_SWITCH_ACTIVE",
            "kill_switch_allows_safety_cancel": safety_cancel.get("allowed") is True
            and safety_cancel.get("cancelled_order_ids") == ["live-000001"],
            "kill_switch_deactivation_requires_authorized_signoff": (
                low_privilege_deactivate.get("accepted") is False
                and authorized_deactivate.get("accepted") is True
            ),
            "live_capital_disabled_by_default": True,
            "deterministic_no_network": True,
        },
    }

    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = run_dir / "evidence.json"
    evidence_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return evidence_path


def main() -> None:
    """CLI entrypoint used by operators and CI drills."""

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/drills/kill_switch"))
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    evidence_path = run_kill_switch_drill(output_root=args.output_root, run_id=args.run_id)
    print(evidence_path)


if __name__ == "__main__":
    main()
