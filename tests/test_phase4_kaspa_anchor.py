from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from policy_impact_sandbox.phase2.audit import build_chained_audit_manifest, canonical_sha256
from policy_impact_sandbox.phase4.kaspa_anchor import (
    KASPA_PAYLOAD_PRACTICAL_LIMIT_BYTES,
    build_kaspa_anchor_record,
    verify_kaspa_anchor_record,
)


def _manifest() -> dict:
    return json.loads(Path("runs/ulez_2023_phase2_deepseek/audit_manifest.json").read_text(encoding="utf-8"))


def test_kaspa_anchor_payload_commits_to_manifest_hash_only() -> None:
    manifest = _manifest()
    anchor = build_kaspa_anchor_record(manifest, "runs/ulez_2023_phase2_deepseek/audit_manifest.json")

    assert anchor["manifest_hash"] == canonical_sha256(manifest)
    assert anchor["payload"]["manifest_hash"] == f"sha256:{canonical_sha256(manifest)}"
    assert anchor["payload"]["chain_policy"]["on_chain_payload"] == "manifest_hash_commitment_only"
    assert anchor["payload_size_bytes"] < KASPA_PAYLOAD_PRACTICAL_LIMIT_BYTES
    assert anchor["automatic_chain_actions_allowed"] is False
    assert "blind_prediction" not in anchor["payload_canonical_json"]
    assert "persona_chat" not in anchor["payload_canonical_json"]


def test_kaspa_anchor_payload_commits_to_hash_chain_head_when_present() -> None:
    manifest = build_chained_audit_manifest(
        case_id="school_street_trial",
        run_id="policy_run_test",
        artifacts={
            "policy_input": ("runs/policy_run_test/input.json", {"policy_text": "School street trial"}),
            "case_graph_ai": ("runs/policy_run_test/case_graph_ai.json", {"case_id": "school_street_trial"}),
            "approval_event": (
                "runs/policy_run_test/approval_event.json",
                {
                    "timestamp": "2026-07-02T00:00:00+00:00",
                    "stage": "case_graph_review",
                    "editor": "human",
                    "diff": [{"path": "/stakeholders/0/weight", "before": 1.0, "after": 1.2}],
                    "approved_hash": "approved-hash",
                },
            ),
            "simulation_outputs": ("runs/policy_run_test/simulation_outputs.json", {"events": []}),
            "report": ("runs/policy_run_test/impact_report.json", {"risk_timeline": []}),
        },
    )

    anchor = build_kaspa_anchor_record(manifest, "runs/policy_run_test/audit_manifest.json")

    assert anchor["manifest_hash"] == canonical_sha256(manifest)
    assert anchor["head_hash"] == manifest["head_hash"]
    assert anchor["payload"]["commitment_type"] == "hash_chain_head"
    assert anchor["payload"]["head_hash"] == f"sha256:{manifest['head_hash']}"
    assert anchor["payload"]["manifest_hash"] == f"sha256:{canonical_sha256(manifest)}"
    assert anchor["payload"]["chain_policy"]["on_chain_payload"] == "hash_chain_head_commitment"
    assert all(verify_kaspa_anchor_record(manifest, anchor).values())


def test_kaspa_anchor_record_verifies() -> None:
    manifest = _manifest()
    anchor = build_kaspa_anchor_record(manifest, "runs/ulez_2023_phase2_deepseek/audit_manifest.json")
    assert all(verify_kaspa_anchor_record(manifest, anchor).values())


def test_kaspa_anchor_cli_refuses_send_without_human_approval() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kaspa_anchor_manifest.py",
            "--manifest",
            "runs/ulez_2023_phase2_deepseek/audit_manifest.json",
            "--send",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--send requires --human-approved" in result.stderr
