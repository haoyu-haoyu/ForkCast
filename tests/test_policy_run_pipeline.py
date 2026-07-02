from __future__ import annotations

import json

from policy_impact_sandbox.live_policy.pipeline import run_policy_analysis


class RecordingLLMClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        if "policy case graph" in system_prompt.lower():
            return json.dumps(
                {
                    "case_id": "school_street_trial",
                    "case_name": "School Street Trial",
                    "entities": [
                        {
                            "id": "policy_school_street_trial",
                            "type": "policy",
                            "name": "School street trial",
                            "description": "Restrict motor traffic near a primary school during drop-off and pick-up.",
                            "evidence_fact_ids": [],
                        }
                    ],
                    "stakeholders": [
                        {
                            "id": "parents_and_guardians",
                            "name": "Parents and guardians",
                            "archetype_group": "affected_public",
                            "stance_prior": "mixed",
                            "interests": ["child_safety", "journey_time"],
                            "evidence_fact_ids": [],
                        },
                        {
                            "id": "local_shop_owners",
                            "name": "Local shop owners",
                            "archetype_group": "affected_business",
                            "stance_prior": "oppose",
                            "interests": ["customer_access", "delivery_access"],
                            "evidence_fact_ids": [],
                        },
                    ],
                    "assumptions": [
                        {
                            "id": "traffic_displacement_possible",
                            "statement": "Traffic may be displaced onto nearby streets.",
                            "status": "待核实",
                            "evidence_fact_ids": [],
                        }
                    ],
                    "constraints": [],
                }
            )
        if "synthetic archetype agent profiles" in system_prompt.lower():
            return json.dumps(
                {
                    "agents": [
                        {
                            "id": "agent_parent_001",
                            "stakeholder_id": "parents_and_guardians",
                            "archetype": "Time-pressed parent",
                            "persona": "Archetype parent balancing child safety and commute time.",
                            "stance": "mixed",
                            "action_tendency": "ask for school safety benefits and practical exemptions",
                            "concerns": ["child_safety", "journey_time"],
                            "evidence_fact_ids": [],
                            "adaptation_capacity": "medium",
                        },
                        {
                            "id": "agent_shop_001",
                            "stakeholder_id": "local_shop_owners",
                            "archetype": "Local shop owner",
                            "persona": "Archetype shop owner concerned about customer and delivery access.",
                            "stance": "oppose",
                            "action_tendency": "request delivery windows and signage",
                            "concerns": ["customer_access", "delivery_access"],
                            "evidence_fact_ids": [],
                            "adaptation_capacity": "medium",
                        },
                    ]
                }
            )
        if "impact report" in system_prompt.lower():
            return json.dumps(
                {
                    "stakeholder_impact_matrix": [
                        {
                            "stakeholder_id": "parents_and_guardians",
                            "name": "Parents and guardians",
                            "impact_level": "medium",
                            "opposition_intensity": "medium",
                            "qualitative_signal": "Safety benefits are visible, but travel friction must be managed.",
                        },
                        {
                            "stakeholder_id": "local_shop_owners",
                            "name": "Local shop owners",
                            "impact_level": "high",
                            "opposition_intensity": "high",
                            "qualitative_signal": "Access constraints may create concentrated business concerns.",
                        },
                    ],
                    "risk_timeline": [
                        {
                            "stage": "implementation",
                            "signal": "Access objections likely rise during initial enforcement.",
                            "risk_level": "medium",
                        }
                    ],
                    "mitigation_options": [
                        {
                            "option": "delivery access window",
                            "rationale": "Keeps business access concerns visible without changing stakeholder weights automatically.",
                        }
                    ],
                    "confidence_notes": ["No historical truth_set was supplied, so this is impact analysis only."],
                }
            )
        raise AssertionError(system_prompt)


def test_generic_policy_run_does_not_load_truth_set_and_marks_backtest_unavailable() -> None:
    client = RecordingLLMClient()

    result = run_policy_analysis(
        policy_text="Restrict motor traffic near a primary school during drop-off and pick-up.",
        llm_client=client,
        run_id="school_street_trial_test",
        agent_count=4,
        rounds=2,
    )

    assert result["case_graph"]["case_id"] == "school_street_trial"
    assert result["truth_set_status"]["status"] == "unavailable"
    assert result["truth_set_status"]["message"] == "无历史回测数据，仅提供影响分析"
    assert result["backtest_result"] is None
    assert result["impact_report"]["disclaimer"] == "simulation is decision support, not deterministic forecast"
    assert result["impact_report"]["claims_audit_table"]
    assert all(row["provenance_class"] for row in result["impact_report"]["claims_audit_table"])
    assert result["audit_manifest"]["entries"]
    assert len(result["agents"]["agents"]) == 4
    assert all("truth_set_json" not in user_prompt for _, user_prompt in client.calls)
    assert any("claims_audit_table" in system_prompt for system_prompt, _ in client.calls)
