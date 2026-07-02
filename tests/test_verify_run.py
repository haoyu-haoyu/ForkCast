from __future__ import annotations

import json
from pathlib import Path

from policy_impact_sandbox.phase2.audit import build_chained_audit_manifest, canonical_sha256
from policy_impact_sandbox.phase4.kaspa_anchor import build_kaspa_anchor_record
from policy_impact_sandbox.verify_run import verify_run


def test_canonical_hash_round_trip_is_stable_for_floats_and_non_ascii(tmp_path: Path) -> None:
    payload = {"z": "低收入家庭", "a": 1.2, "nested": {"b": ["ULEZ", 0.8]}}
    path = tmp_path / "payload.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    assert canonical_sha256(payload) == canonical_sha256(json.loads(path.read_text(encoding="utf-8")))


def test_verify_legacy_demo_run_with_mocked_kaspa_payload() -> None:
    run_dir = Path("runs/ulez_2023_phase2_deepseek")
    anchor = json.loads((run_dir / "kaspa_anchor.json").read_text(encoding="utf-8"))

    result = verify_run(
        run_dir=run_dir,
        txid=anchor["tx_id"],
        fetch_payload_hex=lambda txid, network: anchor["payload_canonical_json"].encode("utf-8").hex(),
    )

    assert result["overall"] == "PASS"
    assert result["mode"] == "legacy_manifest_hash"
    assert result["checks"]["tx_payload_matches_anchor"]["status"] == "PASS"
    assert result["checks"]["manifest_hash_matches_anchor"]["status"] == "PASS"


def test_verify_chained_run_and_detect_tampered_artifact(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "policy_run_test"
    run_dir.mkdir(parents=True)
    artifacts = {
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
    }
    for artifact_uri, payload in artifacts.values():
        Path(artifact_uri).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = build_chained_audit_manifest(case_id="school_street_trial", run_id="policy_run_test", artifacts=artifacts)
    (run_dir / "audit_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    anchor = build_kaspa_anchor_record(manifest, str(run_dir / "audit_manifest.json"), tx_id="abc123")
    (run_dir / "kaspa_anchor.json").write_text(json.dumps(anchor, ensure_ascii=False, indent=2), encoding="utf-8")

    passed = verify_run(
        run_dir=run_dir,
        txid="abc123",
        fetch_payload_hex=lambda txid, network: anchor["payload_canonical_json"].encode("utf-8").hex(),
    )
    assert passed["overall"] == "PASS"
    assert passed["mode"] == "hash_chain_head"
    assert all(item["status"] == "PASS" for item in passed["links"])

    (run_dir / "input.json").write_text(json.dumps({"policy_text": "Tampered"}), encoding="utf-8")
    failed = verify_run(
        run_dir=run_dir,
        txid="abc123",
        fetch_payload_hex=lambda txid, network: anchor["payload_canonical_json"].encode("utf-8").hex(),
    )
    assert failed["overall"] == "FAIL"
    assert failed["links"][0]["status"] == "FAIL"
