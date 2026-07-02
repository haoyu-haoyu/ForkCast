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
    if anchor_path.exists():
        anchor_record = json.loads(anchor_path.read_text(encoding="utf-8"))
        if anchor_record.get("run_id") != audit_manifest["run_id"]:
            raise ValueError("Existing anchor package run_id does not match audit manifest.")
        if anchor_record.get("network") not in {None, network}:
            raise ValueError("Existing anchor package network does not match requested network.")
        existing_tx_id = anchor_record.get("tx_id")
        if existing_tx_id and existing_tx_id != tx_id:
            raise ValueError("Existing anchor package already records a different transaction id.")
        explorer_base_url = anchor_record.get("explorer_base_url") or _explorer_base_url(network)
        anchor_record.update(
            {
                "network": network,
                "status": "anchored",
                "tx_id": tx_id,
                "explorer_base_url": explorer_base_url,
                "explorer_url": f"{explorer_base_url}/txs/{tx_id}",
            }
        )
    else:
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


def _explorer_base_url(network: str) -> str:
    normalized = network.lower()
    if normalized in {"testnet", "testnet-10", "tn10", "testnet10"}:
        return "https://explorer-tn10.kaspa.org"
    if normalized in {"testnet-11", "tn11", "testnet11"}:
        return "https://explorer-tn11.kaspa.org"
    return "https://explorer.kaspa.org"
