from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from policy_impact_sandbox.phase2.agents import DeterministicAgentLLMClient, generate_agent_profiles


def test_generate_agent_profiles_covers_all_stakeholders_and_required_groups() -> None:
    case_graph = json.loads(Path("data/cases/ulez_2023/case_graph.json").read_text(encoding="utf-8"))

    payload = generate_agent_profiles(
        case_graph=case_graph,
        llm_client=DeterministicAgentLLMClient(),
        target_count=36,
    )

    assert payload["case_id"] == "ulez_2023_expansion"
    assert len(payload["agents"]) == 36
    stakeholder_ids = {agent["stakeholder_id"] for agent in payload["agents"]}
    expected_ids = {stakeholder["id"] for stakeholder in case_graph["stakeholders"]}
    assert expected_ids.issubset(stakeholder_ids)
    assert "stakeholder_van_drivers_tradespeople" in stakeholder_ids
    assert "stakeholder_low_income_households" in stakeholder_ids
    assert all(agent["persona_type"] == "archetype" for agent in payload["agents"])
    assert all("real_person" not in agent["persona"].lower() for agent in payload["agents"])
    serialized_agents = json.dumps(payload["agents"], ensure_ascii=False)
    assert "Sadiq Khan" not in serialized_agents
    assert all(" " not in agent["stance"] for agent in payload["agents"])

    schema = json.loads(Path("schemas/agents.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(payload)
