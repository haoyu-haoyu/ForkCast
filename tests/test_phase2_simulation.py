from __future__ import annotations

from policy_impact_sandbox.phase2.simulation import run_policy_mock_simulation


def test_policy_mock_simulation_emits_backlash_and_adaptation_dynamics() -> None:
    agents_payload = {
        "case_id": "ulez_2023_expansion",
        "agents": [
            {
                "id": "agent_outer_001",
                "stakeholder_id": "stakeholder_outer_london_residents",
                "archetype": "Outer London vehicle-dependent driver",
                "stance": "oppose",
                "concerns": ["daily_charge", "fairness"],
                "adaptation_capacity": "medium",
            },
            {
                "id": "agent_van_001",
                "stakeholder_id": "stakeholder_van_drivers_tradespeople",
                "archetype": "Self-employed van tradesperson",
                "stance": "strongly_oppose",
                "concerns": ["operating_cost", "vehicle_replacement_cost"],
                "adaptation_capacity": "low",
            },
            {
                "id": "agent_inner_001",
                "stakeholder_id": "stakeholder_inner_london_residents",
                "archetype": "Inner London air-quality supporter",
                "stance": "support",
                "concerns": ["air_quality", "children_health"],
                "adaptation_capacity": "high",
            },
        ],
    }

    result = run_policy_mock_simulation(agents_payload=agents_payload, run_id="test_run", rounds=3)

    event_types = {event["type"] for event in result["events"]}
    assert {"post", "comment", "stance_change"}.issubset(event_types)
    assert result["signals"]["outer_london_backlash"] == "strong"
    assert result["signals"]["van_tradespeople_pressure"] == "high"
    assert result["signals"]["behavioural_adaptation"] == "present"
    assert any(event.get("to_stance") == "mixed_adapting" for event in result["events"])
