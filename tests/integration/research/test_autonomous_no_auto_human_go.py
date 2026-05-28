from __future__ import annotations

import json
from pathlib import Path

from qts.research.audit_log import ResearchAuditLog

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_autonomous_engine_outputs_human_pending_packets_without_auto_go(
    tmp_path: Path,
) -> None:
    _campaign_path, result = run_engine(tmp_path)

    selected_rows = read_jsonl(result.selected_candidates_path)
    assert selected_rows
    for row in selected_rows:
        packet = json.loads(Path(row["promotion_packet_path"]).read_text(encoding="utf-8"))
        assert packet["review"] == {"status": "human_pending"}
        assert packet["validation"]["status"] == "human_pending"

    records = ResearchAuditLog(result.audit_log_path).list()
    assert "human_review_decided" not in {record.record_type for record in records}
