from __future__ import annotations

import json
from pathlib import Path

from policy_impact_sandbox.phase1.extract import extract_case_graph
from policy_impact_sandbox.phase1.graph import build_networkx_fallback


class FakeLLMClient:
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        assert "Only use supplied source material" in system_prompt
        assert "truth_set_json" in user_prompt
        return json.dumps(
            {
                "case_id": "ulez_2023_expansion",
                "case_name": "London Ultra Low Emission Zone 2023 expansion",
                "entities": [
                    {
                        "id": "policy_ulez_2023",
                        "type": "policy",
                        "name": "ULEZ 2023 expansion",
                        "description": "ULEZ expanded London-wide on 2023-08-29.",
                        "evidence_fact_ids": ["A1_policy_effective_date_and_scope"],
                    }
                ],
                "stakeholders": [
                    {
                        "id": "outer_london_drivers",
                        "name": "Outer London drivers",
                        "archetype_group": "affected_vehicle_owners",
                        "stance_prior": "mixed_to_opposed",
                        "interests": ["daily_charge", "vehicle_replacement_cost"],
                        "evidence_fact_ids": ["C1_public_opinion_distribution"],
                    }
                ],
                "assumptions": [
                    {
                        "id": "compliance_will_rise",
                        "statement": "Compliance is expected to rise after expansion.",
                        "status": "supported_by_truth_set",
                        "evidence_fact_ids": ["D1_six_month_compliance_rate_change"],
                    }
                ],
                "constraints": [
                    {
                        "id": "decision_support_only",
                        "kind": "safety",
                        "statement": "Reports must be decision support, not forecast.",
                        "evidence_fact_ids": [],
                    }
                ],
            }
        )


def test_extract_case_graph_uses_llm_output_and_truth_set_evidence() -> None:
    truth_set = json.loads(Path("data/cases/ulez_2023/truth_set.json").read_text(encoding="utf-8"))

    case_graph = extract_case_graph(
        seed_policy="ULEZ expanded across all London boroughs.",
        truth_set=truth_set,
        llm_client=FakeLLMClient(),
    )

    assert case_graph["case_id"] == "ulez_2023_expansion"
    assert case_graph["extraction_method"] == "llm_deepseek_openai_compatible"
    assert case_graph["source_truth_set"]["fact_count"] == 12
    assert case_graph["evidence"][0]["fact_id"] == "A1_policy_effective_date_and_scope"
    assert case_graph["graph"]["nodes"]
    assert case_graph["graph"]["edges"]


def test_networkx_fallback_exports_nodes_and_edges() -> None:
    case_graph = {
        "case_id": "ulez_2023_expansion",
        "entities": [{"id": "policy_ulez_2023", "type": "policy", "name": "ULEZ"}],
        "stakeholders": [{"id": "outer_london_drivers", "name": "Outer London drivers"}],
        "assumptions": [{"id": "compliance_will_rise", "statement": "Compliance rises"}],
        "constraints": [{"id": "decision_support_only", "statement": "Decision support only"}],
        "evidence": [{"fact_id": "A1_policy_effective_date_and_scope"}],
    }

    graph_payload = build_networkx_fallback(case_graph)

    node_ids = {node["id"] for node in graph_payload["nodes"]}
    assert "case:ulez_2023_expansion" in node_ids
    assert "stakeholder:outer_london_drivers" in node_ids
    assert any(edge["type"] == "HAS_STAKEHOLDER" for edge in graph_payload["edges"])
