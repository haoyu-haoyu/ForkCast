from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from policy_impact_sandbox.phase2.audit import canonical_json, canonical_sha256


KASPA_PAYLOAD_PRACTICAL_LIMIT_BYTES = 25_000
KASPA_TRANSACTION_PAYLOAD_DOC = "https://docs.kaspa.org/integrate/transaction-payload"
KASPA_WALLET_DOC = "https://docs.kaspa.org/integrate/wallet"
KASPA_TESTNET_DOC = "https://wiki.kaspa.org/en/testnets"


def build_kaspa_anchor_record(
    audit_manifest: dict[str, Any],
    manifest_uri: str,
    *,
    network: str = "testnet-10",
    tx_id: str | None = None,
    send_attempted: bool = False,
    send_reason: str | None = None,
) -> dict[str, Any]:
    """Build the Kaspa commitment payload without broadcasting a transaction.

    Chained live-run manifests commit to the hash-chain head. Legacy cached
    manifests continue to commit to the canonical audit manifest hash. The
    payload never includes LLM prompts, simulation logs, personas, PII, or
    source documents.
    """

    prepared_at = datetime.now(timezone.utc).isoformat()
    manifest_hash = canonical_sha256(audit_manifest)
    head_hash = _hash_chain_head(audit_manifest)
    commitment_type = "hash_chain_head" if head_hash else "audit_manifest_hash"
    on_chain_payload = "hash_chain_head_commitment" if head_hash else "manifest_hash_commitment_only"
    payload = {
        "protocol": "policy-impact-sandbox.kaspa-anchor",
        "version": 1,
        "case_id": audit_manifest["case_id"],
        "run_id": audit_manifest["run_id"],
        "stage": commitment_type,
        "commitment_type": commitment_type,
        "manifest_hash": f"sha256:{manifest_hash}",
        "manifest_uri": manifest_uri,
        "artifact_count": len(audit_manifest.get("entries", [])),
        "canonicalization": "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False)",
        "human_approval_gate": {
            "checkpoint": "report_chain_review",
            "required_before_broadcast": True,
            "automatic_broadcast_allowed": False,
        },
        "chain_policy": {
            "off_chain_ai_reasoning": True,
            "on_chain_payload": on_chain_payload,
            "decision_support_not_forecast": True,
        },
        "created_at": prepared_at,
    }
    if head_hash:
        payload["head_hash"] = f"sha256:{head_hash}"
        payload["hash_chain_status"] = audit_manifest.get("chain_status", "hash_chained")
    payload_json = canonical_json(payload)
    payload_size = len(payload_json.encode("utf-8"))
    if payload_size > KASPA_PAYLOAD_PRACTICAL_LIMIT_BYTES:
        raise ValueError(
            f"Kaspa payload is {payload_size} bytes; keep it under the practical "
            f"{KASPA_PAYLOAD_PRACTICAL_LIMIT_BYTES} byte standard-transaction limit."
        )

    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    explorer_base = _explorer_base_url(network)
    explorer_url = f"{explorer_base}/txs/{tx_id}" if tx_id else None
    status = "anchored" if tx_id else "local_verification_only"
    if send_attempted and not tx_id:
        status = "broadcast_failed_or_not_completed"

    return {
        "case_id": audit_manifest["case_id"],
        "run_id": audit_manifest["run_id"],
        "network": network,
        "status": status,
        "tx_id": tx_id,
        "explorer_url": explorer_url,
        "explorer_base_url": explorer_base,
        "manifest_uri": manifest_uri,
        "manifest_hash": manifest_hash,
        "head_hash": head_hash,
        "payload_hash": payload_hash,
        "payload_size_bytes": payload_size,
        "payload_practical_limit_bytes": KASPA_PAYLOAD_PRACTICAL_LIMIT_BYTES,
        "payload": payload,
        "payload_canonical_json": payload_json,
        "prepared_at": prepared_at,
        "send_attempt": {
            "attempted": send_attempted,
            "reason": send_reason
            or "No broadcast attempted. A funded Kaspa testnet wallet and explicit checkpoint-4 approval are required.",
        },
        "human_approval_required_for_chain_anchor": True,
        "automatic_chain_actions_allowed": False,
        "sources": [
            {
                "title": "Kaspa transaction payload documentation",
                "url": KASPA_TRANSACTION_PAYLOAD_DOC,
                "note": "Payload field supports application data; practical standard limit is about 25KB.",
            },
            {
                "title": "Kaspa Wallet API documentation",
                "url": KASPA_WALLET_DOC,
                "note": "High-level Wallet API accountsSend supports payload on outgoing transactions.",
            },
            {
                "title": "Kaspa testnet documentation",
                "url": KASPA_TESTNET_DOC,
                "note": "TN-10 testnet faucet and explorer endpoints.",
            },
        ],
    }


def verify_kaspa_anchor_record(audit_manifest: dict[str, Any], anchor_record: dict[str, Any]) -> dict[str, Any]:
    expected_manifest_hash = canonical_sha256(audit_manifest)
    expected_head_hash = _hash_chain_head(audit_manifest)
    payload_json = canonical_json(anchor_record["payload"])
    expected_payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    return {
        "manifest_hash_matches": anchor_record.get("manifest_hash") == expected_manifest_hash,
        "head_hash_matches": anchor_record.get("head_hash") == expected_head_hash,
        "payload_manifest_hash_matches": anchor_record["payload"].get("manifest_hash")
        == f"sha256:{expected_manifest_hash}",
        "payload_head_hash_matches": expected_head_hash is None
        or anchor_record["payload"].get("head_hash") == f"sha256:{expected_head_hash}",
        "payload_hash_matches": anchor_record.get("payload_hash") == expected_payload_hash,
        "payload_size_matches": anchor_record.get("payload_size_bytes") == len(payload_json.encode("utf-8")),
        "payload_under_practical_limit": len(payload_json.encode("utf-8")) <= KASPA_PAYLOAD_PRACTICAL_LIMIT_BYTES,
        "automatic_chain_actions_disabled": anchor_record.get("automatic_chain_actions_allowed") is False,
    }


def _hash_chain_head(audit_manifest: dict[str, Any]) -> str | None:
    head_hash = audit_manifest.get("head_hash")
    if isinstance(head_hash, str) and head_hash:
        return head_hash
    hash_chain = audit_manifest.get("hash_chain")
    if isinstance(hash_chain, dict):
        nested_head_hash = hash_chain.get("head_hash")
        if isinstance(nested_head_hash, str) and nested_head_hash:
            return nested_head_hash
    return None


def _explorer_base_url(network: str) -> str:
    normalized = network.lower()
    if normalized in {"testnet", "testnet-10", "tn10", "testnet10"}:
        return "https://explorer-tn10.kaspa.org"
    if normalized in {"testnet-11", "tn11", "testnet11"}:
        return "https://explorer-tn11.kaspa.org"
    return "https://explorer.kaspa.org"
