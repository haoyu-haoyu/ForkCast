from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from policy_impact_sandbox.phase4.kaspa_anchor import build_kaspa_anchor_record, verify_kaspa_anchor_record


def record_anchor_transaction(
    *,
    run_dir: str | Path,
    tx_id: str,
    network: str = "testnet-10",
) -> dict[str, Any]:
    run_path = Path(run_dir)
    manifest_path = run_path / "audit_manifest.json"
    status_path = run_path / "status.json"
    anchor_path = run_path / "kaspa_anchor.json"
    audit_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    anchor_record = build_kaspa_anchor_record(
        audit_manifest,
        str(manifest_path),
        network=network,
        tx_id=tx_id,
    )
    verification = verify_kaspa_anchor_record(audit_manifest, anchor_record)
    if not all(verification.values()):
        raise ValueError(f"Anchor verification failed: {verification}")
    anchor_record["verification"] = verification
    anchor_path.write_text(json.dumps(anchor_record, ensure_ascii=False, indent=2), encoding="utf-8")

    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    if status.get("status") not in {"AWAITING_ANCHOR_APPROVAL", "DONE"}:
        raise ValueError("Run must be AWAITING_ANCHOR_APPROVAL before recording an anchor transaction.")
    history = list(status.get("history", []))
    timestamp = datetime.now(timezone.utc).isoformat()
    history.append({"status": "DONE", "timestamp": timestamp})
    status.update(
        {
            "run_id": audit_manifest["run_id"],
            "status": "DONE",
            "updated_at": timestamp,
            "history": history,
            "anchor": {
                "status": "anchored",
                "network": network,
                "tx_id": tx_id,
                "explorer_url": anchor_record["explorer_url"],
                "head_hash": anchor_record.get("head_hash"),
                "manifest_hash": anchor_record["manifest_hash"],
                "payload_hash": anchor_record["payload_hash"],
            },
        }
    )
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return anchor_record
