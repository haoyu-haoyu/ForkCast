from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Protocol

from policy_impact_sandbox.phase2.json_utils import parse_json_object


class AgentLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


class DeterministicAgentLLMClient:
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps({"agents": []})


PROMPT_PATH = Path("prompts/agent_generation.md")


def generate_agent_profiles(
    case_graph: dict[str, Any],
    llm_client: AgentLLMClient,
    target_count: int = 36,
    max_count: int = 200,
) -> dict[str, Any]:
    if not 1 <= target_count <= max_count:
        raise ValueError("target_count must be between 1 and max_count.")
    stakeholders = case_graph.get("stakeholders", [])
    if target_count < len(stakeholders):
        raise ValueError("target_count must cover every stakeholder at least once.")

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = json.dumps(
        {
            "case_id": case_graph["case_id"],
            "target_count": target_count,
            "stakeholders": stakeholders,
            "constraints": case_graph.get("constraints", []),
        },
        ensure_ascii=False,
        indent=2,
    )
    parsed = parse_json_object(llm_client.complete_json(system_prompt, user_prompt))
    llm_agents = parsed.get("agents", [])
    if not isinstance(llm_agents, list):
        llm_agents = []

    agents = _normalize_llm_agents(llm_agents, stakeholders)
    agents = _ensure_coverage_and_count(agents, stakeholders, target_count)
    return {
        "case_id": case_graph["case_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generation_method": "deepseek_openai_compatible_with_coverage_guard",
        "target_count": target_count,
        "max_count": max_count,
        "safety_constraints": [
            "archetype personas only",
            "no real-person PII",
            "no automatic on-chain actions",
            "no automatic stakeholder weight changes",
        ],
        "agents": agents,
    }


def _normalize_llm_agents(llm_agents: list[Any], stakeholders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stakeholder_ids = {stakeholder["id"] for stakeholder in stakeholders}
    normalized = []
    seen = set()
    for raw in llm_agents:
        if not isinstance(raw, dict):
            continue
        stakeholder_id = raw.get("stakeholder_id")
        if stakeholder_id not in stakeholder_ids:
            continue
        agent_id = str(raw.get("id") or f"agent_{stakeholder_id}_{len(normalized) + 1:03d}")
        if agent_id in seen:
            continue
        seen.add(agent_id)
        stakeholder = next(item for item in stakeholders if item["id"] == stakeholder_id)
        normalized.append(_build_agent(agent_id, stakeholder, raw))
    return normalized


def _ensure_coverage_and_count(
    agents: list[dict[str, Any]],
    stakeholders: list[dict[str, Any]],
    target_count: int,
) -> list[dict[str, Any]]:
    by_stakeholder = {stakeholder["id"]: [] for stakeholder in stakeholders}
    for agent in agents:
        by_stakeholder.setdefault(agent["stakeholder_id"], []).append(agent)

    next_index = 1
    output: list[dict[str, Any]] = []
    for stakeholder in stakeholders:
        existing = by_stakeholder.get(stakeholder["id"], [])
        if existing:
            output.append(existing[0])
        else:
            output.append(_build_agent(f"agent_{next_index:03d}_{stakeholder['id']}", stakeholder, {}))
            next_index += 1

    stakeholder_cycle = stakeholders[:]
    while len(output) < target_count:
        stakeholder = stakeholder_cycle[(len(output) - len(stakeholders)) % len(stakeholder_cycle)]
        output.append(_build_agent(f"agent_{next_index:03d}_{stakeholder['id']}", stakeholder, {}))
        next_index += 1

    return output[:target_count]


def _build_agent(agent_id: str, stakeholder: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    stance = _normalize_stance(str(raw.get("stance") or _stance_for_stakeholder(stakeholder)))
    concerns = list(raw.get("concerns") or stakeholder.get("interests") or ["policy_impact"])
    stakeholder_name = _sanitize_archetype_text(stakeholder["name"])
    archetype = _sanitize_archetype_text(str(raw.get("archetype") or stakeholder_name))
    return {
        "id": agent_id,
        "persona_type": "archetype",
        "stakeholder_id": stakeholder["id"],
        "stakeholder_name": stakeholder_name,
        "archetype": archetype,
        "persona": _sanitize_archetype_text(str(raw.get("persona") or _persona_for(stakeholder, concerns))),
        "stance": stance,
        "action_tendency": str(raw.get("action_tendency") or _action_tendency_for(stakeholder, stance)),
        "concerns": concerns,
        "evidence_fact_ids": list(raw.get("evidence_fact_ids") or stakeholder.get("evidence_fact_ids", [])),
        "adaptation_capacity": str(raw.get("adaptation_capacity") or _adaptation_capacity_for(stakeholder)),
    }


def _stance_for_stakeholder(stakeholder: dict[str, Any]) -> str:
    stakeholder_id = stakeholder["id"]
    stance_prior = stakeholder.get("stance_prior", "mixed")
    if stakeholder_id in {"stakeholder_van_drivers_tradespeople", "stakeholder_ulez_opponents_radical"}:
        return "strongly_oppose"
    if stance_prior == "oppose":
        return "oppose"
    if stance_prior == "support":
        return "support"
    return "mixed"


def _persona_for(stakeholder: dict[str, Any], concerns: list[str]) -> str:
    concern_text = ", ".join(concerns[:3])
    return f"Archetype member of {_sanitize_archetype_text(stakeholder['name'])} focused on {concern_text}."


def _action_tendency_for(stakeholder: dict[str, Any], stance: str) -> str:
    stakeholder_id = stakeholder["id"]
    if stakeholder_id == "stakeholder_van_drivers_tradespeople":
        return "raise high-intensity cost objections and request targeted mitigation"
    if stakeholder_id == "stakeholder_low_income_households":
        return "raise fairness and affordability concerns while asking for support"
    if stakeholder_id == "stakeholder_ulez_opponents_radical":
        return "amplify enforcement backlash narratives"
    if stance in {"support", "strongly_support"}:
        return "defend air-quality and health benefits"
    return "express practical objections and seek concessions"


def _adaptation_capacity_for(stakeholder: dict[str, Any]) -> str:
    stakeholder_id = stakeholder["id"]
    if stakeholder_id in {"stakeholder_van_drivers_tradespeople", "stakeholder_low_income_households"}:
        return "low"
    if stakeholder_id in {"stakeholder_outer_london_residents", "stakeholder_conservative_party"}:
        return "medium"
    return "high"


def _normalize_stance(stance: str) -> str:
    return stance.strip().lower().replace(" ", "_")


def _sanitize_archetype_text(value: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", value).strip()
