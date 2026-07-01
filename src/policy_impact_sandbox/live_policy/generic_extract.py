from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Protocol

from policy_impact_sandbox.phase1.graph import build_networkx_fallback
from policy_impact_sandbox.phase2.json_utils import parse_json_object


class JSONLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


PROMPT_PATH = Path("prompts/case_graph_extraction.md")


def extract_generic_case_graph(policy_text: str, llm_client: JSONLLMClient) -> dict[str, Any]:
    """Extract a case graph from policy text without loading any historical truth_set."""
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = (
        "seed_policy_document:\n"
        f"{policy_text.strip()}\n\n"
        "historical_truth_set:\n"
        "UNAVAILABLE. Do not infer historical outcomes or backtest facts.\n"
    )
    raw_response = llm_client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
    parsed = parse_json_object(raw_response)

    case_id = _stable_case_id(str(parsed.get("case_id") or parsed.get("case_name") or "user_policy"))
    case_graph = {
        "case_id": case_id,
        "case_name": str(parsed.get("case_name") or case_id.replace("_", " ").title()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "extraction_method": "llm_deepseek_openai_compatible_no_truth_set",
        "source_truth_set": {
            "path": "",
            "fact_count": 0,
            "available": False,
        },
        "entities": _normalize_items(parsed.get("entities"), "entity"),
        "stakeholders": _normalize_stakeholders(parsed.get("stakeholders")),
        "assumptions": _normalize_items(parsed.get("assumptions"), "assumption"),
        "constraints": _ensure_safety_constraints(_normalize_items(parsed.get("constraints"), "constraint")),
        "evidence": [],
    }
    case_graph["graph"] = build_networkx_fallback(case_graph)
    return case_graph


def _stable_case_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "user_policy"


def _normalize_items(raw_items: Any, item_kind: str) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []
    output: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            continue
        item_id = _stable_case_id(str(raw.get("id") or raw.get("name") or raw.get("statement") or f"{item_kind}_{index}"))
        if item_kind == "entity":
            output.append(
                {
                    "id": item_id,
                    "type": str(raw.get("type") or "policy"),
                    "name": str(raw.get("name") or item_id.replace("_", " ").title()),
                    "description": str(raw.get("description") or ""),
                    "evidence_fact_ids": _string_list(raw.get("evidence_fact_ids")),
                }
            )
        elif item_kind == "assumption":
            output.append(
                {
                    "id": item_id,
                    "statement": str(raw.get("statement") or raw.get("description") or item_id.replace("_", " ")),
                    "status": str(raw.get("status") or "待核实"),
                    "evidence_fact_ids": _string_list(raw.get("evidence_fact_ids")),
                }
            )
        else:
            output.append(
                {
                    "id": item_id,
                    "kind": str(raw.get("kind") or "safety"),
                    "statement": str(raw.get("statement") or raw.get("description") or item_id.replace("_", " ")),
                    "evidence_fact_ids": _string_list(raw.get("evidence_fact_ids")),
                }
            )
    return output


def _normalize_stakeholders(raw_items: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        raw_items = []
    output: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or f"Stakeholder group {index}")
        output.append(
            {
                "id": _stable_case_id(str(raw.get("id") or name)),
                "name": name,
                "archetype_group": str(raw.get("archetype_group") or "affected_public"),
                "stance_prior": str(raw.get("stance_prior") or "unknown"),
                "interests": _string_list(raw.get("interests")) or ["policy_impact"],
                "evidence_fact_ids": _string_list(raw.get("evidence_fact_ids")),
            }
        )
    if output:
        return output
    return [
        {
            "id": "affected_public",
            "name": "Affected public",
            "archetype_group": "affected_public",
            "stance_prior": "unknown",
            "interests": ["policy_impact", "fairness", "implementation"],
            "evidence_fact_ids": [],
        }
    ]


def _ensure_safety_constraints(constraints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    required = [
        ("decision_support_only", "safety", "Reports must be decision support, not deterministic forecast."),
        ("archetypes_only_no_pii", "privacy", "Agents must be archetypes only and must not process real-person PII."),
        ("no_automatic_chain_actions", "human_in_the_loop", "Agents must not automatically send blockchain transactions."),
        ("no_automatic_weight_changes", "human_in_the_loop", "Agents must not automatically change stakeholder weights."),
    ]
    existing = {item["id"] for item in constraints}
    for item_id, kind, statement in required:
        if item_id not in existing:
            constraints.append({"id": item_id, "kind": kind, "statement": statement, "evidence_fact_ids": []})
    return constraints


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
