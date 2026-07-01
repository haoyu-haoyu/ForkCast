from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def chained_sha256(previous_hash: str, payload: Any) -> str:
    return hashlib.sha256((previous_hash + canonical_json(payload)).encode("utf-8")).hexdigest()


def compute_hash_chain(
    *,
    policy_input: Any,
    case_graph_ai: Any,
    approval_event: Any,
    simulation_outputs: Any,
    report: Any,
) -> dict[str, Any]:
    payloads = [
        ("h0", "policy_input", policy_input),
        ("h1", "case_graph_ai", case_graph_ai),
        ("h2", "approval_event", approval_event),
        ("h3", "simulation_outputs", simulation_outputs),
        ("h4", "report", report),
    ]
    links: list[dict[str, Any]] = []
    previous_hash = ""
    for index, (link_id, stage, payload) in enumerate(payloads):
        payload_hash = canonical_sha256(payload)
        link_hash = payload_hash if index == 0 else chained_sha256(previous_hash, payload)
        links.append(
            {
                "id": link_id,
                "stage": stage,
                "payload_hash": payload_hash,
                "previous_hash": previous_hash or None,
                "hash": link_hash,
            }
        )
        previous_hash = link_hash
    return {
        "canonicalization": "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')",
        "links": links,
        "head_hash": previous_hash,
    }


def build_audit_manifest(
    case_id: str,
    run_id: str,
    artifacts: dict[str, tuple[str, Any]],
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "case_id": case_id,
        "run_id": run_id,
        "generated_at": timestamp,
        "chain_status": "not_on_chain",
        "human_approval_required_for_chain_anchor": True,
        "entries": [
            {
                "stage": stage,
                "hash": canonical_sha256(payload),
                "actor": "conduct_core",
                "approval": "not_on_chain",
                "artifact_uri": artifact_uri,
                "timestamp": timestamp,
            }
            for stage, (artifact_uri, payload) in artifacts.items()
        ],
    }


def build_chained_audit_manifest(
    case_id: str,
    run_id: str,
    artifacts: dict[str, tuple[str, Any]],
) -> dict[str, Any]:
    required = ["policy_input", "case_graph_ai", "approval_event", "simulation_outputs", "report"]
    missing = [stage for stage in required if stage not in artifacts]
    if missing:
        raise ValueError(f"Missing chained audit artifacts: {', '.join(missing)}")

    timestamp = datetime.now(timezone.utc).isoformat()
    chain = compute_hash_chain(
        policy_input=artifacts["policy_input"][1],
        case_graph_ai=artifacts["case_graph_ai"][1],
        approval_event=artifacts["approval_event"][1],
        simulation_outputs=artifacts["simulation_outputs"][1],
        report=artifacts["report"][1],
    )
    entries = []
    for stage in required:
        artifact_uri, payload = artifacts[stage]
        link = next(item for item in chain["links"] if item["stage"] == stage)
        entries.append(
            {
                "stage": stage,
                "hash": canonical_sha256(payload),
                "chain_link_hash": link["hash"],
                "actor": "conduct_core" if stage != "approval_event" else "human",
                "approval": "human_approved" if stage == "approval_event" else "not_on_chain",
                "artifact_uri": artifact_uri,
                "timestamp": timestamp,
            }
        )
    approval_event = artifacts["approval_event"][1]
    return {
        "case_id": case_id,
        "run_id": run_id,
        "generated_at": timestamp,
        "chain_status": "hash_chained",
        "human_approval_required_for_chain_anchor": True,
        "head_hash": chain["head_hash"],
        "hash_chain": chain,
        "approval_event": approval_event,
        "entries": entries,
    }
