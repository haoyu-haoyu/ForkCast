from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


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
