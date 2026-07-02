from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable
import urllib.request

from policy_impact_sandbox.phase2.audit import canonical_json, canonical_sha256, compute_hash_chain


FetchPayloadHex = Callable[[str, str], str]


def verify_run(
    *,
    run_dir: str | Path,
    txid: str,
    network: str = "testnet-10",
    fetch_payload_hex: FetchPayloadHex | None = None,
) -> dict[str, Any]:
    run_path = Path(run_dir)
    audit_manifest = _read_json(run_path / "audit_manifest.json")
    anchor = _read_json(run_path / "kaspa_anchor.json")
    fetcher = fetch_payload_hex or fetch_kaspa_transaction_payload_hex
    tx_payload_hex = fetcher(txid, network)
    tx_payload_json = bytes.fromhex(tx_payload_hex).decode("utf-8")
    tx_payload = json.loads(tx_payload_json)

    checks = {
        "tx_payload_matches_anchor": _check(
            canonical_json(tx_payload) == canonical_json(anchor["payload"]),
            "Kaspa transaction payload matches local kaspa_anchor.json payload.",
        ),
        "txid_matches_anchor": _check(
            anchor.get("tx_id") in {None, txid},
            "Provided txid matches local anchor txid when one is recorded.",
        ),
        "manifest_hash_matches_anchor": _check(
            canonical_sha256(audit_manifest) == anchor.get("manifest_hash"),
            "Canonical audit_manifest.json hash matches local anchor package.",
        ),
        "payload_hash_matches_anchor": _check(
            canonical_sha256(tx_payload) == anchor.get("payload_hash"),
            "Canonical transaction payload hash matches local anchor package.",
        ),
    }
    mode = "hash_chain_head" if _manifest_head_hash(audit_manifest) else "legacy_manifest_hash"
    if mode == "hash_chain_head":
        links, chain_checks = _verify_hash_chain(run_path, audit_manifest, anchor, tx_payload)
        checks.update(chain_checks)
    else:
        links, legacy_checks = _verify_legacy_entries(audit_manifest, anchor, tx_payload)
        checks.update(legacy_checks)

    overall_pass = all(item["status"] == "PASS" for item in checks.values()) and all(
        item["status"] == "PASS" for item in links
    )
    return {
        "overall": "PASS" if overall_pass else "FAIL",
        "mode": mode,
        "network": network,
        "txid": txid,
        "checks": checks,
        "links": links,
    }


def fetch_kaspa_transaction_payload_hex(txid: str, network: str) -> str:
    base_url = _api_base_url(network)
    request = urllib.request.Request(
        f"{base_url}/transactions/{txid}",
        headers={"User-Agent": "policy-impact-sandbox-verifier/0.1"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    tx_payload = payload.get("payload")
    if not isinstance(tx_payload, str) or not tx_payload:
        raise ValueError("Kaspa transaction response did not include a payload hex string.")
    return tx_payload


def _verify_hash_chain(
    run_dir: Path,
    audit_manifest: dict[str, Any],
    anchor: dict[str, Any],
    tx_payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    payloads = {}
    for stage in ["policy_input", "case_graph_ai", "approval_event", "simulation_outputs", "report"]:
        entry = _entry_for_stage(audit_manifest, stage)
        payloads[stage] = _read_json(_resolve_artifact_path(run_dir, entry["artifact_uri"]))
    recomputed = compute_hash_chain(
        policy_input=payloads["policy_input"],
        case_graph_ai=payloads["case_graph_ai"],
        approval_event=payloads["approval_event"],
        simulation_outputs=payloads["simulation_outputs"],
        report=payloads["report"],
    )
    manifest_links = {item["stage"]: item for item in audit_manifest["hash_chain"]["links"]}
    links = []
    for link in recomputed["links"]:
        manifest_link = manifest_links[link["stage"]]
        links.append(
            {
                "id": link["id"],
                "stage": link["stage"],
                "status": "PASS" if link["hash"] == manifest_link["hash"] else "FAIL",
                "expected": manifest_link["hash"],
                "actual": link["hash"],
            }
        )
    head_hash = recomputed["head_hash"]
    checks = {
        "head_hash_matches_manifest": _check(
            head_hash == audit_manifest.get("head_hash") == audit_manifest.get("hash_chain", {}).get("head_hash"),
            "Recomputed hash-chain head matches audit manifest.",
        ),
        "head_hash_matches_anchor": _check(
            head_hash == anchor.get("head_hash"),
            "Recomputed hash-chain head matches local anchor package.",
        ),
        "head_hash_matches_tx_payload": _check(
            tx_payload.get("head_hash") == f"sha256:{head_hash}",
            "Recomputed hash-chain head matches on-chain payload commitment.",
        ),
    }
    return links, checks


def _verify_legacy_entries(
    audit_manifest: dict[str, Any],
    anchor: dict[str, Any],
    tx_payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    links = []
    for entry in audit_manifest.get("entries", []):
        artifact_path = _resolve_artifact_path(Path("."), entry["artifact_uri"])
        payload = _read_json(artifact_path)
        actual = canonical_sha256(payload)
        links.append(
            {
                "id": entry["stage"],
                "stage": entry["stage"],
                "status": "PASS" if actual == entry["hash"] else "FAIL",
                "expected": entry["hash"],
                "actual": actual,
            }
        )
    manifest_hash = canonical_sha256(audit_manifest)
    checks = {
        "manifest_hash_matches_tx_payload": _check(
            tx_payload.get("manifest_hash") == f"sha256:{manifest_hash}",
            "Canonical audit manifest hash matches on-chain payload commitment.",
        ),
        "legacy_payload_mode": _check(
            tx_payload.get("chain_policy", {}).get("on_chain_payload") == "manifest_hash_commitment_only",
            "Legacy payload uses manifest-hash commitment mode.",
        ),
    }
    return links, checks


def _check(condition: bool, note: str) -> dict[str, str]:
    return {"status": "PASS" if condition else "FAIL", "note": note}


def _entry_for_stage(audit_manifest: dict[str, Any], stage: str) -> dict[str, Any]:
    for entry in audit_manifest.get("entries", []):
        if entry.get("stage") == stage:
            return entry
    raise KeyError(f"Missing audit manifest entry for stage {stage}.")


def _resolve_artifact_path(run_dir: Path, artifact_uri: str) -> Path:
    path = Path(artifact_uri)
    if path.is_absolute() or path.exists():
        return path
    return run_dir / path.name


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_head_hash(audit_manifest: dict[str, Any]) -> str | None:
    head_hash = audit_manifest.get("head_hash")
    return head_hash if isinstance(head_hash, str) and head_hash else None


def _api_base_url(network: str) -> str:
    normalized = network.lower()
    if normalized in {"testnet", "testnet-10", "tn10", "testnet10"}:
        return "https://api-tn10.kaspa.org"
    if normalized in {"testnet-11", "tn11", "testnet11"}:
        return "https://api-tn11.kaspa.org"
    return "https://api.kaspa.org"
