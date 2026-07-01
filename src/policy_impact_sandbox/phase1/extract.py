from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Protocol

from policy_impact_sandbox.phase1.graph import build_networkx_fallback


class JSONLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


PROMPT_PATH = Path("prompts/case_graph_extraction.md")


def extract_case_graph(seed_policy: str, truth_set: dict[str, Any], llm_client: JSONLLMClient) -> dict[str, Any]:
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = _build_user_prompt(seed_policy, truth_set)
    raw_response = llm_client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
    case_graph = _parse_json_object(raw_response)

    case_graph["case_id"] = case_graph.get("case_id") or truth_set["case_id"]
    case_graph["case_name"] = case_graph.get("case_name") or truth_set.get("case_name", case_graph["case_id"])
    case_graph["generated_at"] = datetime.now(timezone.utc).isoformat()
    case_graph["extraction_method"] = "llm_deepseek_openai_compatible"
    case_graph["source_truth_set"] = {
        "path": "data/cases/ulez_2023/truth_set.json",
        "fact_count": len(truth_set.get("facts", [])),
    }
    case_graph["evidence"] = _evidence_from_truth_set(truth_set)
    case_graph["graph"] = build_networkx_fallback(case_graph)
    return case_graph


def build_seed_policy_from_truth_set(truth_set: dict[str, Any]) -> str:
    lines = [
        f"# {truth_set.get('case_name', truth_set['case_id'])}",
        "",
        "This seed policy document is derived from the verified ULEZ truth_set for Phase 1 extraction.",
        "It is not a replacement for source evidence; fact IDs remain the evidence anchors.",
        "",
    ]
    for fact in truth_set.get("facts", []):
        status = fact.get("confidence_status", "unknown")
        lines.append(f"- [{fact['id']}] ({status}) {fact.get('fact', fact.get('requested_item', ''))}")
    return "\n".join(lines).strip() + "\n"


def _build_user_prompt(seed_policy: str, truth_set: dict[str, Any]) -> str:
    return (
        "seed_policy_document:\n"
        f"{seed_policy}\n\n"
        "truth_set_json:\n"
        f"{json.dumps(truth_set, ensure_ascii=False, indent=2)}\n"
    )


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    if not stripped.startswith("{"):
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("LLM response did not contain a JSON object.")
        stripped = stripped[start : end + 1]
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON must be an object.")
    return parsed


def _evidence_from_truth_set(truth_set: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = []
    for fact in truth_set.get("facts", []):
        evidence.append(
            {
                "fact_id": fact["id"],
                "category": fact.get("category"),
                "confidence_status": fact.get("confidence_status"),
                "source_urls": [source.get("url") for source in fact.get("sources", []) if source.get("url")],
                "quotes": [source.get("quote") for source in fact.get("sources", []) if source.get("quote")],
            }
        )
    return evidence


class DeterministicMockLLMClient:
    def __init__(self, truth_set: dict[str, Any]):
        self._truth_set = truth_set

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        facts = {fact["id"]: fact for fact in self._truth_set.get("facts", [])}
        return json.dumps(
            {
                "case_id": self._truth_set["case_id"],
                "case_name": self._truth_set.get("case_name", self._truth_set["case_id"]),
                "entities": [
                    {
                        "id": "policy_ulez_2023_expansion",
                        "type": "policy",
                        "name": "ULEZ 2023 London-wide expansion",
                        "description": facts.get("A1_policy_effective_date_and_scope", {}).get("fact", ""),
                        "evidence_fact_ids": ["A1_policy_effective_date_and_scope", "A2_daily_charge", "A3_emission_standards"],
                    },
                    {
                        "id": "ulez_camera_network",
                        "type": "enforcement_asset",
                        "name": "ULEZ camera enforcement network",
                        "description": facts.get("C2_camera_vandalism_and_enforcement_resistance", {}).get("fact", ""),
                        "evidence_fact_ids": ["C2_camera_vandalism_and_enforcement_resistance"],
                    },
                ],
                "stakeholders": [
                    {
                        "id": "outer_london_drivers",
                        "name": "Outer London drivers",
                        "archetype_group": "affected_vehicle_owners",
                        "stance_prior": "mixed_to_opposed",
                        "interests": ["daily_charge", "vehicle_replacement_cost", "fairness"],
                        "evidence_fact_ids": ["C1_public_opinion_distribution", "A2_daily_charge"],
                    },
                    {
                        "id": "small_business_van_operators",
                        "name": "Small business van operators",
                        "archetype_group": "commercial_vehicle_users",
                        "stance_prior": "cost_sensitive",
                        "interests": ["operating_cost", "scrappage_access", "customer_coverage"],
                        "evidence_fact_ids": ["D1_six_month_compliance_rate_change"],
                    },
                    {
                        "id": "public_health_beneficiaries",
                        "name": "Residents exposed to roadside pollution",
                        "archetype_group": "health_beneficiaries",
                        "stance_prior": "support",
                        "interests": ["air_quality", "children_health", "reduced_no2"],
                        "evidence_fact_ids": ["D3_air_quality_and_emissions_changes"],
                    },
                    {
                        "id": "anti_ulez_activists",
                        "name": "Anti-ULEZ enforcement opponents",
                        "archetype_group": "policy_resistance_group",
                        "stance_prior": "strongly_opposed",
                        "interests": ["camera_resistance", "civil_disobedience", "privacy"],
                        "evidence_fact_ids": ["C2_camera_vandalism_and_enforcement_resistance", "C3_public_view_on_camera_vandalism"],
                    },
                    {
                        "id": "mayor_tfl_policy_team",
                        "name": "Mayor of London and TfL policy team",
                        "archetype_group": "policy_implementers",
                        "stance_prior": "support",
                        "interests": ["compliance", "air_quality", "delivery_risk"],
                        "evidence_fact_ids": ["A1_policy_effective_date_and_scope", "D1_six_month_compliance_rate_change"],
                    },
                ],
                "assumptions": [
                    {
                        "id": "compliance_improves_after_expansion",
                        "statement": "Compliance rate should rise after the 2023 London-wide expansion.",
                        "status": "supported_by_truth_set",
                        "evidence_fact_ids": ["D1_six_month_compliance_rate_change", "D2_non_compliant_vehicle_count_change"],
                    },
                    {
                        "id": "political_salience_high_in_outer_london",
                        "statement": "ULEZ expansion creates a high-salience political risk signal in affected outer London constituencies.",
                        "status": "supported_by_truth_set",
                        "evidence_fact_ids": ["B2_ulez_as_key_by_election_issue", "C1_public_opinion_distribution"],
                    },
                ],
                "constraints": [
                    {
                        "id": "decision_support_only",
                        "kind": "safety",
                        "statement": "All reports must be labelled decision support, not forecast.",
                        "evidence_fact_ids": [],
                    },
                    {
                        "id": "archetypes_only_no_pii",
                        "kind": "privacy",
                        "statement": "Agents must be archetypes only and must not process real person PII.",
                        "evidence_fact_ids": [],
                    },
                    {
                        "id": "no_automatic_chain_actions",
                        "kind": "human_in_the_loop",
                        "statement": "Agents must not automatically send Kaspa or Canton transactions.",
                        "evidence_fact_ids": [],
                    },
                ],
            },
            ensure_ascii=False,
        )
