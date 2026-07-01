from policy_impact_sandbox.simulation.mock import generate_mock_simulation


def test_mock_simulation_outputs_social_events_and_stance_changes():
    agents = [
        {
            "id": "outer_driver_001",
            "group": "outer_london_driver",
            "stance": "opposed",
        },
        {
            "id": "health_parent_001",
            "group": "health_beneficiary",
            "stance": "supportive",
        },
    ]
    config = {"case_id": "ulez_2023_expansion", "rounds": 2, "random_seed": 7}

    result = generate_mock_simulation(agents=agents, config=config)

    assert result["case_id"] == "ulez_2023_expansion"
    assert result["mode"] == "mock"
    assert len(result["events"]) >= 4
    assert {event["type"] for event in result["events"]} >= {"post", "comment", "stance_change"}
    assert all("round" in event for event in result["events"])
    assert all("agent_id" in event for event in result["events"])
    assert result["metadata"]["agent_count"] == 2
    assert result["metadata"]["rounds"] == 2
    assert result["metadata"]["disclaimer"] == "simulation is decision support, not deterministic forecast"
