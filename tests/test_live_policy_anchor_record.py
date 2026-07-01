from __future__ import annotations

import json
from pathlib import Path

from policy_impact_sandbox.live_policy.anchoring import record_anchor_transaction
from policy_impact_sandbox.phase2.audit import build_chained_audit_manifest


def test_record_anchor_transaction_writes_anchor_and_marks_run_done(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "policy_run_test"
    run_dir.mkdir(parents=True)
    manifest = build_chained_audit_manifest(
        case_id="school_street_trial",
        run_id="policy_run_test",
        artifacts={
            "policy_input": (str(run_dir / "input.json"), {"policy_text": "School street trial"}),
            "case_graph_ai": (str(run_dir / "case_graph_ai.json"), {"case_id": "school_street_trial"}),
            "approval_event": (
                str(run_dir / "approval_event.json"),
                {
                    "timestamp": "2026-07-02T00:00:00+00:00",
                    "stage": "case_graph_review",
                    "editor": "human",
                    "diff": [{"path": "/stakeholders/0/weight", "before": 1.0, "after": 1.2}],
                    "approved_hash": "approved-hash",
                },
            ),
            "simulation_outputs": (str(run_dir / "simulation_outputs.json"), {"events": []}),
            "report": (str(run_dir / "impact_report.json"), {"risk_timeline": []}),
        },
    )
    (run_dir / "audit_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (run_dir / "status.json").write_text(
        json.dumps({"run_id": "policy_run_test", "status": "AWAITING_ANCHOR_APPROVAL", "history": []}),
        encoding="utf-8",
    )

    result = record_anchor_transaction(
        run_dir=run_dir,
        tx_id="abc123",
        network="testnet-10",
    )

    anchor = json.loads((run_dir / "kaspa_anchor.json").read_text(encoding="utf-8"))
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert result["tx_id"] == "abc123"
    assert anchor["status"] == "anchored"
    assert anchor["head_hash"] == manifest["head_hash"]
    assert anchor["explorer_url"] == "https://explorer-tn10.kaspa.org/txs/abc123"
    assert status["status"] == "DONE"
    assert status["anchor"]["tx_id"] == "abc123"
    assert status["history"][-1]["status"] == "DONE"
