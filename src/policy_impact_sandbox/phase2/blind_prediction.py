from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Protocol

from policy_impact_sandbox.phase2.agents import _sanitize_archetype_text
from policy_impact_sandbox.phase2.json_utils import parse_json_object


class BlindLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


ALLOWED_POLICY_ENTITY_IDS = {"entity_ulez_policy"}
EXCLUDED_CASE_GRAPH_FIELDS = [
    "evidence",
    "evidence_fact_ids",
    "evidence_note",
    "graph",
    "source_truth_set",
    "entities except policy definition",
    "historical assumptions derived from outcomes",
]
OUTCOME_ENTITY_TYPES = {"political_event", "public_reaction", "policy_outcome", "report", "poll"}


class DeterministicBlindLLMClient:
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps(
            {
                "summary": "Blind qualitative prediction based only on policy design and stakeholder incentives.",
                "group_reactions": [
                    {
                        "group_id": "stakeholder_outer_london_residents",
                        "direction": "oppose",
                        "intensity": "high",
                        "rationale": "vehicle-dependent households outside the existing zone face cost and fairness concerns",
                    },
                    {
                        "group_id": "stakeholder_inner_london_residents",
                        "direction": "support",
                        "intensity": "medium",
                        "rationale": "health and air-quality benefits are more salient",
                    },
                    {
                        "group_id": "stakeholder_van_drivers_tradespeople",
                        "direction": "oppose",
                        "intensity": "very_high",
                        "rationale": "work vehicles and replacement costs create concentrated livelihood pressure",
                    },
                    {
                        "group_id": "stakeholder_low_income_households",
                        "direction": "oppose",
                        "intensity": "high",
                        "rationale": "replacement affordability and distributional burden are central",
                    },
                ],
                "ranked_opposition_groups": [
                    "stakeholder_van_drivers_tradespeople",
                    "stakeholder_low_income_households",
                    "stakeholder_outer_london_residents",
                ],
                "political_consequences": [
                    "political salience and electoral risk are likely because costs are concentrated and visible"
                ],
                "time_dynamics": [
                    "short-term backlash may be strong, while some affected groups gradually adapt behaviour and compliance over time"
                ],
                "secondary_reactions": [
                    "enforcement resistance and camera-sabotage narratives are plausible secondary reactions"
                ],
                "benefit_burden_balance": [
                    "air-quality and public-health benefits are likely",
                    "fairness and distributional burden are also likely for low-income and vehicle-dependent groups",
                ],
                "confidence_notes": [
                    "Directional qualitative prediction only; no historical percentages or election outcomes used."
                ],
            },
            ensure_ascii=False,
        )


def make_blind_case_context(case_graph: dict[str, Any]) -> dict[str, Any]:
    """Build the only context allowed in blind prediction.

    This function intentionally does not accept truth_set and drops every evidence
    field or historical outcome entity from case_graph before prompt construction.
    """
    policy_entities = [
        _clean_policy_entity(entity)
        for entity in case_graph.get("entities", [])
        if entity.get("id") in ALLOWED_POLICY_ENTITY_IDS and entity.get("type") not in OUTCOME_ENTITY_TYPES
    ]
    stakeholders = [_clean_stakeholder(item) for item in case_graph.get("stakeholders", [])]
    constraints = [
        {"id": item["id"], "kind": item.get("kind"), "statement": item.get("statement", "")}
        for item in case_graph.get("constraints", [])
    ]
    return {
        "case_id": case_graph["case_id"],
        "case_name": case_graph.get("case_name", case_graph["case_id"]),
        "policy_entities": policy_entities,
        "stakeholders": stakeholders,
        "blind_safe_assumptions": [],
        "constraints": constraints,
        "sanitization_summary": "historical outcome evidence and post-implementation metrics removed before prediction",
    }


def build_blind_prediction_prompts(blind_context: dict[str, Any]) -> dict[str, str]:
    system_prompt = (
        "You are producing a blind policy impact prediction. "
        "Do not use historical outcome data, election results, post-implementation metrics, polling results, "
        "camera offence counts, compliance rates, air-quality measurements, or source quotes. "
        "Use only the provided sanitized policy context and stakeholder incentives. "
        "Return one JSON object and no prose. Do not predict exact percentages, vote margins, offence counts, "
        "or any specific election result. Political output must be framed as political salience/electoral risk only."
    )
    user_prompt = (
        "sanitized_blind_case_context:\n"
        f"{json.dumps(blind_context, ensure_ascii=False, indent=2)}\n\n"
        "Return JSON with keys: summary, group_reactions, ranked_opposition_groups, "
        "political_consequences, time_dynamics, secondary_reactions, benefit_burden_balance, confidence_notes. "
        "For group_reactions include group_id, direction, intensity, rationale."
    )
    return {"system_prompt": system_prompt, "user_prompt": user_prompt}


def generate_blind_prediction(
    case_graph: dict[str, Any],
    llm_client: BlindLLMClient,
    llm_metadata: dict[str, Any],
) -> dict[str, Any]:
    blind_context = make_blind_case_context(case_graph)
    prompts = build_blind_prediction_prompts(blind_context)
    raw_text = llm_client.complete_json(prompts["system_prompt"], prompts["user_prompt"])
    parsed = parse_json_object(raw_text)
    return {
        "case_id": case_graph["case_id"],
        "mode": "blind_prediction",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "llm": llm_metadata,
        "leakage_guard": {
            "truth_set_loaded_into_prompt": False,
            "truth_set_file_read_by_prediction_step": False,
            "excluded_case_graph_fields": EXCLUDED_CASE_GRAPH_FIELDS,
        },
        "prompt": prompts,
        "blind_context": blind_context,
        "raw_prediction_text": raw_text,
        "raw_prediction": parsed,
        "prediction": _normalize_prediction(parsed),
    }


def _clean_policy_entity(entity: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entity["id"],
        "type": entity.get("type"),
        "name": entity.get("name"),
        "description": entity.get("description", ""),
    }


def _clean_stakeholder(stakeholder: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": stakeholder["id"],
        "name": _sanitize_archetype_text(stakeholder.get("name", stakeholder["id"])),
        "archetype_group": stakeholder.get("archetype_group"),
        "visible_prior_stance": "unknown",
        "interests": stakeholder.get("interests", []),
    }


def _normalize_prediction(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": parsed.get("summary", ""),
        "group_reactions": _as_list(parsed.get("group_reactions")),
        "ranked_opposition_groups": _as_list(parsed.get("ranked_opposition_groups")),
        "political_consequences": _as_list(parsed.get("political_consequences")),
        "time_dynamics": _as_list(parsed.get("time_dynamics")),
        "secondary_reactions": _as_list(parsed.get("secondary_reactions")),
        "benefit_burden_balance": _as_list(parsed.get("benefit_burden_balance")),
        "confidence_notes": _as_list(parsed.get("confidence_notes")),
    }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
